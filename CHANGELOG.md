# Changelog

## v0.9 — 2026-10-24

- Initial public experimental version; package version is 0.9.0.
- Three identically named choices in Core selectors and the dedicated node:
  MOSS Shift Scheduler, MOSS Curve Scheduler and MOSS Sigma Scheduler.
- MOSS Shift Scheduler is the dedicated node's default and retains the original MIT Radiance calculation.
- Added the original Power Shift defaults and an experimental fractional-grid variant.
- Included English/Japanese documentation, manual Git clone installation,
  the MOSS-Image SFT + lora_latest DMD LoRA example, and original MIT attribution.
- Verified CPU numerical compatibility and offline workflow-name migration.
- Practical use has focused on MOSS-Image SFT with the DMD acceleration LoRA.
  SFT without acceleration LoRA has had very limited practical testing; other models are unverified.
- Updated the documented project starting point from 8 steps / LoRA strength 0.7 to
  10 steps / strength 0.8, with dpmpp_sde, CFG 3, MOSS Shift Scheduler and denoise 1.0.
  The upstream LoRA author's 0.7 recommendation remains separately attributed.
