# CPU verification — v0.9

Checked on 2026-10-24 with ComfyUI **0.42.1** at commit
`63be2f9b82ad0dac88a7ceaa28a9cf3154125a18`.
Environment: Python 3.12.12, PyTorch 2.14.1+cu130, NumPy 2.5.2.

**PASS: 8 Python unittest cases and the Node.js offline workflow-migration check.**

| Check | Scope |
|---|---|
| Original Radiance compatibility | 28 bit-exact comparisons: real Core flow tables with shifts 1/5/12 and a short synthetic table; steps 1/3/8/20/25/50/1000 |
| Original Power defaults | 16 bit-exact comparisons |
| Fractional-grid variant | 12 comparisons closer to Radiance than the first unshifted prototype; 24 finite/descending/zero-endpoint checks |
| Dedicated node / Core selector | 18 cases, including denoise 1.0/0.5/0 and unchanged source tables |
| Real Core KSampler | 8 cases covering er_sde/dpmpp_sde/dpm_2/uni_pc and Core penultimate handling |
| Names / defaults | Exact full names match in both selectors; MOSS Shift Scheduler is the node default; old mode aliases retain their outputs |
| Registration | Three new names, one node, no replacement of existing handlers, no duplicates on repeated registration |
| Offline JavaScript migration | Original and later development names, saved settings/prompts/custom titles, subgraphs and repeated migration |
| CPU isolation | No CUDA initialization, checked after every Python test |

The Python test runs real Core schedule and KSampler math with lightweight model-sampling
tables, without loading model weights. Core is put into CPU mode, CUDA availability/device
count is forced to false/zero, optional GPU attention packages are hidden in that test
process, and CUDA initialization is guarded. Those overrides do not modify any installed
dependency, settings file, or running ComfyUI process.

The JavaScript test provides only an app-registration harness and checks the migration
function offline. It is not a real browser UI test. Separately, user-provided screenshots
show the MOSS Shift Scheduler name and the documented SFT + DMD LoRA use case.

The MIT reference is pinned to `silveroxides/ComfyUI_PowerShiftScheduler` commit
`770d7b8e4104b8d864d1fed0a65713e4a3e7a953`.
The full reference is retained as text; only its two scheduler functions are extracted by
AST. Its original imports, registrations and node classes are never executed.

Reference SHA256:
`87911c03363f0cde997573952f0f8e3a203557eb12fc418541b77758e2f8bce4`.

## Reproduce

Use an existing ComfyUI Python environment, with its Core directory available:

```powershell
$env:COMFYUI_ROOT = 'C:\path\to\ComfyUI'
& 'C:\path\to\ComfyUI\venv\Scripts\python.exe' -B tests/test_scheduler.py
node tests/test_rename.cjs
```

No installation of testing dependencies is required: Python uses unittest and Node uses
its standard library. Normal use does not require Node.js.

Not established: a minimum older ComfyUI version, comparative GPU image quality/speed/VRAM,
optimal settings, or practical compatibility with other models. Normal generation without
the acceleration LoRA has had very limited practical testing.
