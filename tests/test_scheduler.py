"""Offline, CPU-only contract checks against the pinned MIT source and real Core."""
import ast
import hashlib
import importlib.util
import os
import pathlib
import sys
import types
import unittest

os.environ["CUDA_VISIBLE_DEVICES"] = ""
import numpy
import torch


ROOT = pathlib.Path(__file__).resolve().parents[1]
COMFY_ROOT = pathlib.Path(os.environ.get("COMFYUI_ROOT", pathlib.Path(sys.executable).resolve().parents[2]))
sys.path.insert(0, str(COMFY_ROOT))
sys.argv = [sys.argv[0], "--cpu"]
CUDA_CALLS = []


def forbid_cuda(*args, **kwargs):
    CUDA_CALLS.append(True)
    raise AssertionError("CPU verification attempted CUDA initialization")


torch.cuda.init = forbid_cuda
torch.cuda._lazy_init = forbid_cuda
torch.cuda.is_available = lambda: False
torch.cuda.device_count = lambda: 0
# These optional GPU packages probe CUDA on import even with Core's --cpu flag.
# Hide them only in this offline test process; no runtime files are changed.
for gpu_package in ("sageattention", "sageattn3", "flash_attn"):
    sys.modules[gpu_package] = None

import comfy.options
comfy.options.enable_args_parsing()
import comfy.samplers
import comfy.model_sampling


before_handlers = dict(comfy.samplers.SCHEDULER_HANDLERS)
before_names = list(comfy.samplers.SCHEDULER_NAMES)
spec = importlib.util.spec_from_file_location(
    "moss_scheduler_cpu_test", ROOT / "__init__.py", submodule_search_locations=[str(ROOT)]
)
package = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = package
spec.loader.exec_module(package)
scheduler = sys.modules[spec.name + ".scheduler"]

reference_file = ROOT / "tests/reference/PowerShiftScheduler-770d7b8e4104b8d864d1fed0a65713e4a3e7a953.py.txt"
reference_source = reference_file.read_text(encoding="utf-8")
tree = ast.parse(reference_source)
functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
             and node.name in ("power_shift_scheduler", "radiance_shift_scheduler")]
assert len(functions) == 2
upstream = {"numpy": numpy, "torch": torch}
exec(compile(ast.Module(body=functions, type_ignores=[]), str(reference_file), "exec"), upstream)


class Model:
    def __init__(self, sampling):
        self.sampling = sampling

    def get_model_object(self, name):
        assert name == "model_sampling"
        return self.sampling


class SchedulerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.samplings = [comfy.model_sampling.ModelSamplingDiscreteFlow(
            types.SimpleNamespace(sampling_settings={"shift": shift, "multiplier": 1.0})
        ) for shift in (1.0, 5.0, 12.0)]
        cls.samplings.append(types.SimpleNamespace(sigmas=torch.linspace(0.01, 1, 7)))

    def test_radiance_bit_exact_against_original_mit_function(self):
        for sampling in self.samplings:
            for steps in (1, 3, 8, 20, 25, 50, 1000):
                with self.subTest(table=len(sampling.sigmas), steps=steps):
                    expected = upstream["radiance_shift_scheduler"](sampling, steps)
                    actual = scheduler.radiance_shift_scheduler(sampling, steps)
                    self.assertTrue(torch.equal(expected, actual))
                    self.assertEqual(actual.dtype, torch.float32)
                    self.assertEqual(actual.device.type, "cpu")

    def test_standard_matches_original_mit_power_curve(self):
        for sampling in self.samplings:
            for steps in (3, 8, 25, 50):
                for mode, power, midpoint in (("MOSS Curve Scheduler", 2.0, 1.0),):
                    with self.subTest(mode=mode, steps=steps, table=len(sampling.sigmas)):
                        expected = upstream["power_shift_scheduler"](
                            sampling, steps, power, midpoint, discard_penultimate=False
                        )
                        actual = scheduler.MODE_HANDLERS[mode](sampling, steps)
                        self.assertTrue(torch.equal(expected, actual))
                        self.assertTrue(torch.isfinite(actual).all())
                        self.assertTrue((actual[:-1] >= actual[1:]).all())
                        self.assertEqual(actual[-1].item(), 0.0)

    def test_dmd_is_closer_to_radiance_than_previous_dmd(self):
        for sampling in self.samplings:
            for steps in (3, 8, 20, 25, 50, 1000):
                actual = scheduler.moss_dmd_scheduler(sampling, steps)
                self.assertTrue(torch.isfinite(actual).all())
                self.assertTrue((actual[:-1] >= actual[1:]).all())
                self.assertEqual(actual[-1].item(), 0.0)
                self.assertEqual(actual.device.type, "cpu")
                if len(sampling.sigmas) == 1000 and steps <= 25:
                    with self.subTest(shift=sampling.shift, steps=steps):
                        previous = upstream["power_shift_scheduler"](sampling, steps, 2.4, 0.98)
                        radiance = upstream["radiance_shift_scheduler"](sampling, steps)
                        self.assertEqual(actual.shape, radiance.shape)
                        self.assertEqual(actual.numel(), steps + 1)
                        self.assertTrue((actual >= previous).all())
                        self.assertTrue((actual <= radiance).all())
                        self.assertLess((actual - radiance).abs().mean().item(),
                                        (previous - radiance).abs().mean().item())
                        self.assertFalse(torch.equal(actual, radiance))

    def test_node_and_core_selector_share_results_and_denoise_tail(self):
        sampling = self.samplings[1]
        original_table = sampling.sigmas.clone()
        model = Model(sampling)
        node = package.NODE_CLASS_MAPPINGS["MOSS_Scheduler"]()
        for mode, name in zip(scheduler.MODES, scheduler.SCHEDULER_HANDLERS):
            for steps in (8, 25):
                for denoise in (1.0, 0.5, 0.0):
                    with self.subTest(mode=mode, steps=steps, denoise=denoise):
                        actual, = node.get_sigmas(model, mode, steps, denoise)
                        if denoise == 0:
                            self.assertEqual(actual.numel(), 0)
                        else:
                            total = int(steps / denoise)
                            expected = comfy.samplers.calculate_sigmas(sampling, name, total)[-(steps + 1):]
                            self.assertTrue(torch.equal(actual, expected))
        self.assertTrue(torch.equal(original_table, sampling.sigmas))

    def test_core_ksampler_penultimate_and_denoise_integration(self):
        sampling = self.samplings[1]
        model = Model(sampling)
        for sampler_name in ("er_sde", "dpmpp_sde", "dpm_2", "uni_pc"):
            for steps, denoise in ((8, 1.0), (25, 0.5)):
                with self.subTest(sampler=sampler_name, steps=steps, denoise=denoise):
                    total = int(steps / denoise)
                    extra = sampler_name in comfy.samplers.KSampler.DISCARD_PENULTIMATE_SIGMA_SAMPLERS
                    expected = upstream["radiance_shift_scheduler"](sampling, total + int(extra))
                    if extra:
                        expected = torch.cat((expected[:-2], expected[-1:]))
                    expected = expected[-(steps + 1):]
                    core = comfy.samplers.KSampler(model, steps, torch.device("cpu"),
                                                  sampler=sampler_name, scheduler="MOSS Shift Scheduler",
                                                  denoise=denoise)
                    self.assertTrue(torch.equal(core.sigmas, expected))

    def test_registration_is_namespaced_and_idempotent(self):
        for name, handler in before_handlers.items():
            self.assertIs(comfy.samplers.SCHEDULER_HANDLERS[name], handler)
        new_names = set(comfy.samplers.SCHEDULER_NAMES) - set(before_names)
        self.assertEqual(new_names, set(scheduler.SCHEDULER_HANDLERS))
        first = dict(comfy.samplers.SCHEDULER_HANDLERS)
        package.register_schedulers()
        self.assertEqual(first, comfy.samplers.SCHEDULER_HANDLERS)
        for name in scheduler.SCHEDULER_HANDLERS:
            self.assertEqual(comfy.samplers.SCHEDULER_NAMES.count(name), 1)
        self.assertEqual(len(package.NODE_CLASS_MAPPINGS), 1)

    def test_no_cuda_initialization(self):
        self.assertEqual(CUDA_CALLS, [])
        self.assertFalse(torch.cuda.is_initialized())

    def test_renamed_choices_default_and_legacy_mode_results(self):
        node = package.MOSSScheduler()
        choices, config = node.INPUT_TYPES()["required"]["mode"]
        self.assertEqual(choices, ["MOSS Shift Scheduler", "MOSS Curve Scheduler", "MOSS Sigma Scheduler"])
        self.assertEqual(list(scheduler.SCHEDULER_HANDLERS), choices)
        self.assertEqual(config["default"], "MOSS Shift Scheduler")
        model = Model(self.samplings[1])
        for old, new in scheduler.MODE_ALIASES.items():
            self.assertTrue(node.VALIDATE_INPUTS(old))
            self.assertTrue(torch.equal(node.get_sigmas(model, old, 25)[0],
                                        node.get_sigmas(model, new, 25)[0]))
        self.assertFalse(node.VALIDATE_INPUTS("unknown"))

    def tearDown(self):
        self.assertEqual(CUDA_CALLS, [])
        self.assertFalse(torch.cuda.is_initialized())


if __name__ == "__main__":
    print("Reference SHA256:", hashlib.sha256(reference_file.read_bytes()).hexdigest())
    print("Core:", COMFY_ROOT)
    unittest.main(argv=[sys.argv[0]], verbosity=2)
