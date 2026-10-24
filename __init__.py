# SPDX-License-Identifier: MIT
__version__ = "0.9.0"

import comfy.samplers

from .scheduler import MODES, MODE_ALIASES, SCHEDULER_HANDLERS, get_sigmas


class MOSSScheduler:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "model": ("MODEL", {"tooltip": "Use the same model as the sampler, after any model-sampling settings."}),
            "mode": (list(MODES), {
                "default": "MOSS Shift Scheduler",
                "tooltip": "MOSS Shift Scheduler: baseline. MOSS Curve Scheduler: original power curve. MOSS Sigma Scheduler: shifted step placement.",
            }),
            "steps": ("INT", {"default": 25, "min": 1, "max": 1000,
                               "tooltip": "Requested sampling steps. Match your workflow; changing mode does not change this value."}),
            "denoise": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01,
                                   "tooltip": "1.0 for text-to-image. Lower values use the tail of a longer schedule for image-to-image."}),
        }}

    RETURN_TYPES = ("SIGMAS",)
    RETURN_NAMES = ("sigmas",)
    OUTPUT_TOOLTIPS = ("Connect to SamplerCustom or SamplerCustomAdvanced. Zero denoise returns an empty schedule.",)
    FUNCTION = "get_sigmas"
    CATEGORY = "model/sampling/schedulers"
    DESCRIPTION = (
        "General-purpose scheduler created for MOSS-Image use, with three step distributions. "
        "Other models are unverified. CFG, sampler, LoRAs and model shift stay under your control."
    )

    @classmethod
    def VALIDATE_INPUTS(cls, mode):
        return mode in MODES or mode in MODE_ALIASES

    def get_sigmas(self, model, mode, steps, denoise=1.0):
        return (get_sigmas(model.get_model_object("model_sampling"), mode, steps, denoise),)


def register_schedulers():
    for name, handler in SCHEDULER_HANDLERS.items():
        if name not in comfy.samplers.SCHEDULER_HANDLERS:
            comfy.samplers.SCHEDULER_HANDLERS[name] = comfy.samplers.SchedulerHandler(handler, use_ms=True)
        if name not in comfy.samplers.SCHEDULER_NAMES:
            comfy.samplers.SCHEDULER_NAMES.append(name)


register_schedulers()

NODE_CLASS_MAPPINGS = {"MOSS_Scheduler": MOSSScheduler}
NODE_DISPLAY_NAME_MAPPINGS = {"MOSS_Scheduler": "MOSS Shift Scheduler"}
WEB_DIRECTORY = "./web"
