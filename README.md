# MOSS Shift Scheduler v0.9

[日本語はこちら](#日本語)

Three general-purpose sigma schedulers for ComfyUI, developed for MOSS-Image workflows:
**MOSS Shift Scheduler**, **MOSS Curve Scheduler**, and **MOSS Sigma Scheduler**.

This is a personal, experimental tool primarily used with **MOSS-Image SFT + `lora_latest.safetensors` DMD acceleration LoRA**.
**Normal generation without the acceleration LoRA has had very limited practical testing. Other models are unverified.**
The calculations are not restricted to MOSS, but this is not a claim of broad model compatibility or optimal settings.

The linked LoRA is published as **DMD** (a distillation-based acceleration LoRA).
This README uses its published name; no separate “Turbo” model is required.

## Installation

Open a terminal in your ComfyUI installation, then run:

```bash
cd custom_nodes
git clone https://github.com/ukr8b3g-cmyk/ComfyUI-MOSS-Shift-Scheduler.git
```

Restart ComfyUI and reload the browser. No extra Python dependencies or model downloads are required by this package;
it uses the NumPy and PyTorch already supplied with ComfyUI.

Install **only one copy**. If you have the earlier development folder `ComfyUI-MOSS-Scheduler`,
disable that copy before installing this repository alongside it. Saved node ID `MOSS_Scheduler` is retained.
This repository is not yet registered in ComfyUI Manager/Comfy Registry; Git clone is the available installation route.

## ComfyUI compatibility

- CPU integration checked against **ComfyUI 0.42.1**, commit `63be2f9b82ad0dac88a7ceaa28a9cf3154125a18`.
- The Core selector integration requires `comfy.samplers.SCHEDULER_HANDLERS`, `SchedulerHandler`, and `SCHEDULER_NAMES`.
  A minimum older ComfyUI version has **not** been established.
- Use a ComfyUI build that supports MOSS-Image when following the MOSS workflow below.
- Verification environment: Python 3.12.12, PyTorch 2.14.1+cu130, NumPy 2.5.2.
  These describe the checked environment, not exact required dependency pins.

## Three choices

The dedicated node and Core KSampler selectors use **exactly the same full names**.

| Choice | Calculation |
|---|---|
| **MOSS Shift Scheduler** — default | Original MIT Radiance Shift calculation: power 2.4, midpoint shift 0.98, steps+1 grid, then removal of the penultimate sigma |
| **MOSS Curve Scheduler** | Original Power Shift defaults: power 2.0, midpoint shift 1.0 |
| **MOSS Sigma Scheduler** | Power 2.4, midpoint shift 0.98, with timestep placement `j / (steps + 0.75)` |

MOSS Shift Scheduler is the baseline choice. The names do not rank image quality.
Switching a choice does not load a LoRA or change steps, CFG, sampler, SLG, or model shift.

## MOSS-Image SFT + DMD LoRA example

| Setting | Example / starting point |
|---|---|
| Model | [MOSS-Image SFT](https://huggingface.co/OpenMOSS-Team/MOSS-Image-SFT) |
| Acceleration LoRA | [lodestones/MOSS-Image-SFT-8-steps-dmd](https://huggingface.co/lodestones/MOSS-Image-SFT-8-steps-dmd), specifically [`lora_latest.safetensors`](https://huggingface.co/lodestones/MOSS-Image-SFT-8-steps-dmd/blob/main/lora_latest.safetensors) |
| LoRA strength | **0.7 as a recommended starting point**, not a mandatory or universally optimal value |
| Sampler | **`dpmpp_sde`** or **`dpmpp_2m_sde`** |
| Scheduler | **MOSS Shift Scheduler**; compare the other two choices if useful |
| Steps | **Start around 8 and adjust**; not fixed to 8 |
| CFG | **3.0** |
| Denoise | **1.0** for this text-to-image example |

The LoRA author also recommends strength 0.7 for `lora_latest.safetensors`.
Do not confuse it with the separate `lora.safetensors` file and its different strength recommendation.

This follows the combinations in [this sampler comparison report](https://www.reddit.com/r/StableDiffusion/comments/1x86z9k/moss_image_samplers_and_schedulers/):
`dpmpp_sde / radiance_shift` and `dpmpp_2m_sde / radiance_shift`.
The report evaluates prompt adherence but does **not** state the actual generation step count.
The 8-step example above comes from this project's user-provided use case.
Good prompt adherence has also been reported in that use case; this is an observation, not a controlled benchmark.
The supplied screenshots confirm `dpmpp_sde`, 8 steps, CFG 3 and LoRA strength 0.70.
The second sampler is an alternative from the referenced report, not an independently verified GPU comparison here.

## Usage and changes from upstream

- In **KSampler**, choose one of the three full names under scheduler. KSampler's own default selection is unchanged.
- With the dedicated **MOSS Shift Scheduler** node, connect the same MODEL used by the sampler,
  and connect SIGMAS to SamplerCustom / SamplerCustomAdvanced.
  The node defaults to MOSS Shift Scheduler, 25 steps and denoise 1.0; the example's 8 steps are set manually.
- Denoise below 1.0 uses the tail of a longer schedule; zero returns an empty schedule.
- Some samplers (`dpm_2`, `dpm_2_ancestral`, `uni_pc`, `uni_pc_bh2`) add Core penultimate-sigma handling.
  Their Core KSampler path can differ from passing dedicated SIGMAS directly.
- Repeated timestep indices are removed, so very long schedules or short model tables can yield fewer points.

The baseline retains the original MIT `radiance_shift_scheduler` calculation.
The Curve choice uses the original `power_shift_scheduler` defaults.
The Sigma choice changes timestep placement from `j / steps` to `j / (steps + 0.75)`,
toward Radiance's `j / (steps + 1)` grid. It is not a 75% blend of SIGMAS.
Compared with the first unshifted prototype, it moves toward higher noise and increases the final jump to zero.
A quality improvement has not been established.

The original MIT repository's old dedicated Radiance node calls the Power Shift function;
numerical compatibility here targets the original **Radiance function / registered scheduler**.
This package does not replace the UtilsCollection node or alter its `radiance_shift` registration.

## Earlier development names

| Earlier labels / selector values | Current full name |
|---|---|
| Radiance Shift (Compatible), Balanced, moss_radiance_shift, moss_shift_balanced | MOSS Shift Scheduler |
| MOSS Standard, Power, moss_standard, moss_shift_power | MOSS Curve Scheduler |
| MOSS DMD, Offset, moss_dmd, moss_shift_offset | MOSS Sigma Scheduler |

Normal workflow loading migrates the dedicated node and KSampler / KSamplerAdvanced / BasicScheduler values in the browser.
The saved file changes only when you save it again. Dedicated-node API mode aliases remain accepted.
Old Core API prompts and other custom sampler nodes should be updated to the new full names.

## Verification and license

CPU verification covers numerical output, Core integration, and registration.
Offline JavaScript verification covers old-name migration. These are separate from user-provided practical MOSS use.
No comparative GPU image-quality benchmark was performed here. See [CPU_VALIDATION.md](CPU_VALIDATION.md).

MIT. The upstream copyright and license are retained in [LICENSE](LICENSE);
source, pinned revision, and changes are listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
This is an unofficial extension and is not endorsed by OpenMOSS or the upstream author.

---

<a id="日本語"></a>
## 日本語

### 概要・主な使用対象

**MOSS Shift Scheduler v0.9** は、MOSS-Imageでの利用を目的に作成した、非公式の汎用スケジューラーです。
主に **MOSS-Image SFT＋`lora_latest.safetensors`のDMD高速化LoRA** を使うための個人的な実験用ツールです。

**高速化LoRAを使わない通常生成は、実使用でほとんどテストしていません。他モデルでの生成も未確認です。**
モデル固有の計算や、MOSS以外を拒否する処理はありませんが、汎用性・画質の最適化を実証したという意味ではありません。
リンク先は配布元がDMDと呼んでいる蒸留型の高速化LoRAです。別の「Turbo」モデルを必須とするものではありません。

### 導入方法

ComfyUIフォルダーでターミナルを開き、次を実行してください。

```bash
cd custom_nodes
git clone https://github.com/ukr8b3g-cmyk/ComfyUI-MOSS-Shift-Scheduler.git
```

ComfyUIを再起動し、ブラウザーを再読み込みします。
ComfyUIに含まれるNumPy・PyTorchを使うため、本パッケージ独自の追加依存やモデルのダウンロードは不要です。

**導入は1コピーだけにしてください。** 旧開発フォルダー `ComfyUI-MOSS-Scheduler` がある環境では、
旧コピーを無効化してから導入してください。既存ノードの内部ID `MOSS_Scheduler` は維持しています。
ComfyUI Manager / Comfy Registryには未登録です。現時点の導入方法はGit cloneです。

### ComfyUIの対応・確認環境

- **ComfyUI 0.42.1**、コミット `63be2f9b82ad0dac88a7ceaa28a9cf3154125a18` でCPU統合確認済みです。
- Coreへの登録は `SCHEDULER_HANDLERS`、`SchedulerHandler`、`SCHEDULER_NAMES` のAPIを使います。
  それ以前の最低対応バージョンは確定していません。
- 下記の使用例では、MOSS-Imageを読み込めるComfyUIが必要です。
- 確認環境はPython 3.12.12、PyTorch 2.14.1+cu130、NumPy 2.5.2です。これらの厳密な版固定を要求するものではありません。

### 3種類の選択肢

KSamplerと専用ノードで、名前を省略せず同じ表記で使います。

| 選択名 | 計算 |
|---|---|
| **MOSS Shift Scheduler**（初期選択） | 元のRadiance関数と同じ。power=2.4、midpoint_shift=0.98、steps+1で計算しゼロ直前の点を削除 |
| **MOSS Curve Scheduler** | 元のPower Shiftの既定値。power=2.0、midpoint_shift=1.0 |
| **MOSS Sigma Scheduler** | power=2.4、midpoint_shift=0.98、時刻を `j / (steps + 0.75)` に配置 |

MOSS Shift Schedulerを基準に選びます。名前は画質の順位ではありません。
選択を変えてもLoRA、steps、CFG、サンプラー、SLG、モデルのshiftは自動変更しません。

### MOSS-Image SFT＋DMD高速化LoRAの使用例

| 項目 | 設定例・推奨の開始値 |
|---|---|
| モデル | [MOSS-Image SFT](https://huggingface.co/OpenMOSS-Team/MOSS-Image-SFT) |
| 高速化LoRA | [lodestones/MOSS-Image-SFT-8-steps-dmd](https://huggingface.co/lodestones/MOSS-Image-SFT-8-steps-dmd) の [`lora_latest.safetensors`](https://huggingface.co/lodestones/MOSS-Image-SFT-8-steps-dmd/blob/main/lora_latest.safetensors) |
| LoRA強度 | **0.7は推奨の開始値**。固定・必須・全環境での最適値ではありません |
| サンプラー | **`dpmpp_sde`** または **`dpmpp_2m_sde`** |
| スケジューラー | **MOSS Shift Scheduler**を基準に、ほかの2方式とも比較可能 |
| ステップ | **8を起点に調整**。8固定ではありません |
| CFG | **3.0** |
| denoise | **1.0**（txt2imgの例） |

配布元も`lora_latest.safetensors`の強度0.7を推奨しています。
別ファイル`lora.safetensors`の推奨強度とは区別してください。

この使用例は[サンプラー比較投稿](https://www.reddit.com/r/StableDiffusion/comments/1x86z9k/moss_image_samplers_and_schedulers/)の
`dpmpp_sde / radiance_shift`、`dpmpp_2m_sde / radiance_shift`に準拠しています。
元投稿ではプロンプト追従性が評価されていますが、実際の生成ステップ数は不明です。
上記の8ステップは今回のユーザー使用例に基づきます。
その実使用でも「プロンプトへの追従性がよい」との評価がありましたが、比較ベンチマークではありません。
提供画像ではdpmpp_sde、8 steps、CFG 3、LoRA強度0.70を確認しています。
dpmpp_2m_sdeは参考投稿にある代替候補で、こちらで独立したGPU比較を行ったものではありません。

### 使用方法・元実装との差

- KSamplerではschedulerから上記のフルネームを選びます。KSampler自身の初期選択は変更しません。
- 専用ノードでは同じMODELをサンプラーにも接続し、SIGMASをSamplerCustom / SamplerCustomAdvancedへ渡します。
  ノード初期値はMOSS Shift Scheduler、25 steps、denoise=1.0です。使用例の8 stepsは手動設定します。
- denoiseを小さくすると長いスケジュールの末尾を使います。0は空のSIGMASです。
- `dpm_2`、`dpm_2_ancestral`、`uni_pc`、`uni_pc_bh2` ではCoreの追加末尾処理があるため、
  専用SIGMASを渡す経路との差があります。時刻の重複除去で出力段数が減る場合もあります。

MOSS Shift Schedulerは元MIT版のRadiance関数を再現し、MOSS Curve Schedulerは元のPower Shift既定値を使います。
MOSS Sigma Schedulerは元の時刻配置 `j / steps` を `j / (steps + 0.75)` に変更した派生方式です。
Radianceの配置は重複除去前では `j / (steps + 1)` です。SIGMASを75%混ぜる処理ではありません。
初期の補正なし試作より高ノイズ側へ寄り、最後のゼロまでの飛び幅も大きくなります。画質改善は未検証です。

元MIT版の旧専用RadianceノードはPower Shift関数を呼ぶため、互換対象は元のRadiance関数 / 登録です。
既存UtilsCollectionのノードや`radiance_shift`登録には触れません。

### 旧名・検証・ライセンス

旧Balanced / Radiance Shift (Compatible) / moss_radiance_shift / moss_shift_balancedはMOSS Shift Scheduler、
旧Power / MOSS Standard / moss_standard / moss_shift_powerはMOSS Curve Scheduler、
旧Offset / MOSS DMD / moss_dmd / moss_shift_offsetはMOSS Sigma Schedulerに対応します。

通常ワークフロー読込時は専用ノードとKSampler / KSamplerAdvanced / BasicSchedulerの旧値をブラウザーで変換します。
再保存するまで保存ファイルは変わりません。専用ノードAPIは旧モード値も受け付けます。
旧Core API promptや他のカスタムサンプラーは新しいフルネームへ更新してください。

CPU数値一致・Core統合・登録、旧名移行のオフラインJavaScript確認を実施しています。
ユーザー側のMOSS実使用とは区別し、こちらでGPU画質の比較ベンチマークは行っていません。
詳細は[CPU_VALIDATION.md](CPU_VALIDATION.md)を参照してください。

MIT。原作者の著作権表示と全文は[LICENSE](LICENSE)、出典・固定コミット・改変内容は
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)に記載しています。
OpenMOSSや元スケジューラー作者の公認拡張ではありません。
