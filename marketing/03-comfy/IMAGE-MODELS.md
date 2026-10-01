# Image models for the 3090 — licence-verified recommendation

**Answers Martin's open question:** which image-generation model(s) to run on vast.ai instance <instance-id>
(single RTX 3090, 24GB, shared with an LLM benchmark job) for BC Vote Match marketing assets.
Recommendation is **per asset class**, not one winner: the three asset families have different jobs and
the cheapest licence-clean answer differs per family.

Date of research: 2026-10-01. Every licence below was read at the stated URL on that date.
Provenance is marked **[card]** (read on the model's own card/licence file) or **[secondary]**
(only a third-party or vendor page available — flagged where it matters).

**Bottom line:**

| Asset class | First choice | Fallback | Why |
|---|---|---|---|
| Atmospheric background plates | FLUX.1-schnell fp8 (Comfy-Org) | Chroma1-HD fp8mixed | Abstract composition + prompt adherence at 4 steps; Apache-2.0 |
| BC landscape plates | FLUX.1-schnell fp8 (Comfy-Org) | Chroma1-HD fp8mixed (SDXL if VRAM-contended) | Photographic register at 4 steps; generic geography prompts hold up |
| Flat editorial illustration | SDXL 1.0 base + flat-illustration style LoRA | SDXL 1.0 base, prompt-only | Series consistency; negative prompts; cleanest LoRA licence chain we found |
| Upscaling (1200×630, 1080×1350) | Real-ESRGAN x4plus (BSD-3-Clause) | 4x-UltraSharp (licence undeclared — see caveats) | Only upscancer class with a licence we verified |

---

## 1. The licence gate (applied before any scoring)

The project is MIT-licensed and the artwork will be **published**. A model passes only if the licence
permits (a) commercial use and (b) derivative works, without registering with anyone or paying anyone.
Anything that fails goes to the rejects table with the clause that killed it. Gated HuggingFace repos
(terms click-through with an account) are flagged separately: they change the download path, and for
this project we prefer ungated mirrors so `aria2c` works without an HF token.

Verified licence texts, all read on the date above:

**FLUX.1-schnell — Apache-2.0 — PASS [card]**
Licence text read at
https://github.com/black-forest-labs/flux/blob/main/model_licenses/LICENSE-FLUX1-schnell
(the file is verbatim the Apache License, Version 2.0). The operative grant:
> "each Contributor hereby grants to You a perpetual, worldwide, non-exclusive, no-charge, royalty-free,
> irrevocable copyright license to reproduce, prepare Derivative Works of, publicly display, publicly
> perform, sublicense, and distribute the Work and such Derivative Works in Source or Object form."

No use restrictions, no revenue clause. Apache-2.0 claims nothing over outputs (they are not "the Work").
Model card metadata on https://huggingface.co/black-forest-labs/FLUX.1-schnell also reads
`license: apache-2.0` **[card]**. Caveat: the BFL HuggingFace repo is now **gated** (`gated: auto`,
requires account + sharing contact info) — verified via the HF API and by being refused the raw
LICENSE without auth. Download instead from the ungated Comfy-Org repack (below).

**FLUX.1-dev — FLUX.1 [dev] Non-Commercial License v1.1.1 — REJECT [card]**
Text read at
https://github.com/black-forest-labs/flux/blob/main/model_licenses/LICENSE-FLUX1-dev :
> "Company grants you a non-exclusive, worldwide, non-transferable, non-sublicensable, revocable,
> royalty free and limited license to access, use, create Derivatives of, and Distribute the
> FLUX.1 [dev] Models and Derivatives solely for your Non-Commercial Purposes."

with "Non-Commercial Purpose" defined as use "only so far as you do not receive any direct or indirect
payment arising from the use of the FLUX.1 [dev] Model". Publishing assets for a funded civic campaign
is production use for us → fails the gate. Note the same licence explicitly covers "fine-tuned version[s]"
as Derivatives, so **FLUX.1-dev LoRAs are tainted too** (Outputs are not Derivatives — but that only
matters if you already have a licensed right to run the model). The repo is also gated (`gated: auto`).

**SDXL 1.0 base — CreativeML Open RAIL++-M, dated July 26, 2023 — PASS with flow-down conditions [card]**
Full text read at
https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/blob/main/LICENSE.md :
> "The Output You Generate. Except as set forth herein, Licensor claims no rights in the Output You
> generate using the Model. You are accountable for the Output you generate and its subsequent uses."

Commercial use and derivatives are permitted ("You" is defined as using the Model "for whichever purpose
and in any field of use"), but the restrictions attach:
> "Use-based restrictions. The restrictions set forth in Attachment A are considered Use-based
> restrictions. Therefore You cannot use the Model and the Derivatives of the Model for the specified
> restricted uses."

Attachment A's restrictions (no disinformation, no PII-harming outputs, no illegal use, etc.) are
compatible with a neutral civic tool — and actually align with our own content rules. If we ever
distribute a fine-tune or LoRA, the definition of "Derivatives of the Model" ("all modifications to the
Model… transfer of patterns of the weights…") means the restrictions flow down with it. Publishing
*images* is fine.

**Chroma1-HD — Apache-2.0 — PASS [card]**
Model card (https://huggingface.co/lodestones/Chroma1-HD, frontmatter `license: apache-2.0`):
> "Chroma1-HD is an 8.9B parameter text-to-image foundational model based on FLUX.1-schnell. It is fully
> Apache 2.0 licensed, ensuring that anyone can use, modify, and build upon it."

The Comfy-Org repack `Comfy-Org/Chroma1-HD_repackaged` also declares `license: apache-2.0` **[card]**.
Derivative of FLUX.1-schnell (itself Apache-2.0), so the lineage is clean. Ungated. The older
`lodestones/Chroma` repo is deprecated ("use Chroma1-HD, Chroma1-Base or Chroma1-Flash instead").

**Real-ESRGAN x4plus — BSD 3-Clause — PASS [secondary, corroborated]**
Upstream code licence is BSD 3-Clause (github.com/xinntao/Real-ESRGAN, LICENSE file). The weights are
distributed under the same terms per the AMD-hosted mirror
(https://huggingface.co/amd/realesrgan-x4plus):
> "These weights are distributed under the BSD 3-Clause License, Copyright (c) 2021 Xintao Wang
> (upstream LICENSE)."

Commercial use and modification explicitly allowed (OpenModelDB rights page for 4x-RealESRGAN-x4Plus:
"Private use / Commercial use / Distribution / Modifications / Credit required" **[secondary]**). We did
not read a weight-specific licence file inside the xinntao release — the BSD-3 weight claim rests on the
mirror's statement plus OpenModelDB; treat as high-confidence but secondary.

**Flat-illustration style LoRA — see §3.** The short version: the LoRA ecosystem is licence-murky and we
recommend only one, with caveats.

---

## 2. Comparison of candidates that pass the gate

Sizes are from the HuggingFace API (file listing), VRAM figures are community estimates **marked (est)**
— no measurements were taken, the GPU is owned by another agent right now.

| Model | Download | VRAM @1024² | ComfyUI loader | Sampler settings | Official template in Comfy-Org/workflow_templates |
|---|---|---|---|---|---|
| **FLUX.1-schnell fp8** (Comfy-Org all-in-one checkpoint) | 17.24 GB single file `flux1-schnell-fp8.safetensors` (diffusion model + T5 + CLIP + VAE bundled) | ~12–16 GB (est) | `CheckpointLoaderSimple` — standard, no extra nodes | **4 steps, cfg 1.0, euler / simple** (read from the template) | ✅ `flux_schnell.json`, `flux_schnell_full_text_to_image.json` |
| FLUX.1-schnell fp16 (full) | 23.78 GB `flux1-schnell.safetensors` | ~20–24 GB (est) — effectively the whole card | `CheckpointLoaderSimple` | same | ✅ (same templates, full variant) |
| **Chroma1-HD fp8mixed** (Comfy-Org repack) | 9.19 GB `Chroma1-HD-fp8mixed.safetensors` **+ support files**: T5 `t5xxl_fp8_e4m3fn_scaled.safetensors` 5.16 GB + FLUX VAE `ae.safetensors` 0.34 GB | ~10–14 GB total (est) | `UNETLoader` (diffusion_models) + `CLIPLoader` (type `chroma`) + `VAELoader` — stock nodes | **26 steps, cfg 3.5, euler, beta scheduler, shift 1, negative prompt supported** (read from the template) | ✅ `image_chroma_text_to_image.json`, `image_chroma1_radiance_text_to_image.json` |
| Chroma1-HD bf16 | 17.80 GB single file + same T5/VAE | ~18–22 GB (est) | same | same | ✅ (same) |
| **SDXL 1.0 base** | 6.94 GB `sd_xl_base_1.0.safetensors` | ~8 GB (est) | `CheckpointLoaderSimple` | **25 steps, cfg 7, dpmpp_2m / karras** (read from the template) | ✅ `image_sdxl_simple.json` |
| Real-ESRGAN x4plus | 63.9 MB `RealESRGAN_x4plus.pth` | <2 GB (est) | `UpscaleModelLoader` → models/upscale_models | n/a (single pass) | ❌ only API-based upscale templates exist; the node is two wires |

Note on Chroma1-HD: it takes **negative prompts** (it is a CFG model — the official template ships a
negative conditioning node), which FLUX.1-schnell effectively does not (cfg 1.0). For our use that
matters mainly for the illustration class ("no text, no watermark, no mascot").

### Considered but not recommended (gate status noted)

| Model | Licence | Verdict | Why not |
|---|---|---|---|
| Playground v2.5 | Playground v2.5 Community License **[card]**: "this permissive license is available for free for research and commercial use (by an entity or individual)", with Additional Commercial Terms above 1M monthly unique users | Passes gate at our scale | Custom licence with redistribution pass-through duty; aesthetic-tuned toward cinematic looks, not our restrained register; 13.88 GB fp16 (6.94 GB fp16 single-file exists). Redundant given SDXL + schnell |
| PixArt-Sigma | CreativeML OpenRAIL++-M (card metadata) **[card, metadata level]** | Passes gate at metadata level | Needs its own T5 stack; weaker ecosystem for style-LoRA consistency; weaker fit than SDXL for the illustration class |
| Lumina-Image 2.0 | Apache-2.0 (card metadata) **[card, metadata level]** | Passes | Viable reserve — Comfy-Org repack exists (`lumina_2.safetensors` 10.62 GB all-in-one). Unproven for our register; keep in reserve |
| Sana | Apache-2.0 (card metadata) **[card, metadata level]** | Passes | Efficient, but style control and editorial-register output are less predictable; no reason to prefer over the shortlist |

### Rejects (fail the licence gate)

| Model / asset | Licence | Reason rejected | Source read |
|---|---|---|---|
| **FLUX.1-dev** (+ Fill/Depth/Canny/Redux/Kontext dev, and every LoRA trained on them) | FLUX.1 [dev] Non-Commercial License v1.1.1 | "…license to access, use, create Derivatives of, and Distribute the FLUX.1 [dev] Models and Derivatives **solely for your Non-Commercial Purposes**" — our use is funded production output | [card] github.com/black-forest-labs/flux model_licenses/LICENSE-FLUX1-dev |
| **Kolors** | frontmatter says `apache-2.0`, but the card's License section says: "Kolors are fully open-sourced for **academic research. For commercial use, please fill out this questionnaire … and sent it to kwai-kolors@kuaishou.com for registration**" | Weights require commercial registration; Apache-2.0 covers the code only. Frontmatter metadata is misleading here | [card] huggingface.co/Kwai-Kolors/Kolors README |
| **SD3.5 Medium / Large** | Stability AI Community License | Not a hard fail at our revenue (commercial use is free under $1M annual revenue) but: revenue-contingent, **revocable**, and repos are gated (`gated: auto`; raw LICENSE returns 401 unauthenticated). Apache-2.0 alternatives exist, so the extra conditions buy us nothing | [secondary] stability.ai/license: "free for research, non-commercial, and commercial use. You only need a paid Enterprise license if your yearly revenues exceed USD$1M and you use Stability AI models in commercial products or services" — clause text on the SD3.5 model card itself could not be read (gated) |
| **HunyuanDiT** | `tencent-hunyuan-community` (custom) | Terms not read; cannot clear the gate → reject by default | [card, metadata level only] |
| Popular flat-illustration LoRAs (Shakker-Labs re-uploads, Muapi line, "simple-flat-illustration-shakker", etc.) | **No declared licence** on their HF cards (`license: None`) | Cannot verify commercial/derivative rights → reject by default. Some are also FLUX-dev-trained, which taints them twice | [card, metadata level] via HF API |
| 4x-UltraSharp and most OpenModelDB ESRGAN upscalers | no declared licence | Unverifiable; Real-ESRGAN x4plus is the licence-clean equivalent | [secondary] OpenModelDB listing |

---

## 3. The two things that are easy to forget

**Style LoRA (flat editorial illustration).** The honest picture: most illustration LoRAs have murky
licences. The best *licence-declared* candidate we found is
`ramel2/emotional-flat-illustration-sdxl-lora` (SDXL, card declares
`creativeml-openrail-m`, 456.5 MB `minimal_flat_illustration,_emotional_scene.safetensors`, trigger
words `minimal flat illustration` / `emotional scene`) **[card, metadata + file listing]**. The chain is
licence-coherent — SDXL base is OpenRAIL++-M and a LoRA is a "Derivative" under that licence, so the
same terms cover the pair. Two caveats, both testable:
1. It was trained on "emotional storytelling scenes… body language", i.e. human-figure bias — our asset
   rules ban faces and figures, so the benchmark must prove it stays clean on object-only prompts.
2. We read its licence at card-metadata level, not clause level (the card declares the licence rather
   than reproducing it).

Fallback is prompt-only SDXL — for a series of 6–8 icons, disciplined prompt templates with the same
style block may be enough, and it removes the last licence question. Do **not** buy consistency with a
FLUX-dev LoRA (non-commercial taint) or an undeclared-licence LoRA.

**Upscaler.** A 1200×630 share card and a 1080×1350 carousel slide want more than a 1024px generation.
Plan: generate at roughly half-target (1216×576 for share cards, 864×1080 for 4:5 slides), upscale 4×
with **Real-ESRGAN x4plus** (BSD-3-Clause, verified above), Lanczos-downsample to the exact target. On
grain-heavy background plates, benchmark for halo/over-sharpen artifacts; if the plate is too clean after
ESRGAN, re-apply grain in the compositing step instead of trying to preserve it through the upscaler.

---

## 4. Recommendation by asset class

### Atmospheric background plates (abstract, paper/grain, soft gradients, geometry; must survive 40–60% darkening)
- **First: FLUX.1-schnell fp8.** The job is abstract composition and prompt adherence, and schnell gives
  clean, quiet, well-structured abstracts at 4 steps — iteration speed matters because plates are cheap
  to generate and expensive to curate. Abstract prompts also play to its strength (composition) and away
  from its weakness (we don't need negatives for "no text" on a prompt with no objects to misread).
- **Fallback: Chroma1-HD fp8mixed.** Use when the plate drifts busy: cfg 3.5 + negative prompt
  ("text, letters, watermark, signage, structures") reins in unwanted geometry.

### BC landscape plates (coastal rainforest, mountains, interior plateau, river valley; generic, not a town, not a campaign photo)
- **First: FLUX.1-schnell fp8.** Photographic register holds at 4 steps; prompts framed as "wide
  photograph, no buildings, no people, no roads" reliably produce the generic-geography look we want.
- **Fallback: Chroma1-HD fp8mixed** (negative prompt to suppress people/signage/logos), or **SDXL** if
  the shared box is VRAM-contended — SDXL's ~8 GB is the only shortlisted model that is genuinely safe
  to run while an LLM benchmark holds the rest of the card.

### Clean flat / line editorial illustration (ballot box, document, compass, magnifier, scales, shield; restrained, not cute)
- **First: SDXL 1.0 base + `minimal_flat_illustration,_emotional_scene.safetensors` LoRA @ ~0.6–0.8**,
  25 steps, cfg 7, dpmpp_2m / karras, with a fixed negative block ("text, letters, words, watermark,
  logo, mascot, cartoon face, kawaii, anime, 3D render, drop shadow, gradient mesh, human figure,
  corporate memphis"). This class is about *series consistency* — same palette, same line weight across
  6–8 icons — and a style LoRA is the only tool in the shortlist that buys that. SDXL has the deepest
  illustration-LoRA pool with a licence chain we can defend.
- **Fallback: SDXL prompt-only** (drop the LoRA, strengthen the style block; same settings).
  Second fallback **Chroma1-HD** for a stricter line-art look with negatives enabled.

### Upscaling
- **First: Real-ESRGAN x4plus** (BSD-3-Clause) via `UpscaleModelLoader`, 4× then downsample to target.
- **Fallback: 4x-UltraSharp** — quality is well-liked in the community but its licence is undeclared;
  only use it if ESRGAN visibly fails the plate test, and record that trade-off.

---

## 5. Benchmark plan (for whoever gets the GPU next)

Test **FLUX.1-schnell-fp8 → SDXL base (+LoRA) → Chroma1-HD-fp8mixed**, in that order. Nothing else
until these three have data. Downloads are staged in `DOWNLOADS.md`.

### Prompts (reuse verbatim; all text is added later in SVG — text in the image is a defect)

**A. Background plate** (schnell / chroma — for SDXL add the negative block)
```
Abstract institutional background texture, pale grey-green paper grain, soft diagonal gradient,
faint embossed geometric grid lines, subtle fibre texture, flat even lighting, muted desaturated
palette, minimal, no objects, no text, editorial print aesthetic
```
**B. Landscape plate — coast**
```
Wide photograph of a coastal rainforest valley in British Columbia, low soft overcast light,
layered mountain ridges fading into mist, dark evergreen forest, calm water, no buildings,
no people, no roads, no signage, muted natural colours, large-format landscape photography
```
**C. Landscape plate — interior**
```
Wide photograph of an interior plateau river valley in British Columbia, dry golden grasslands,
rolling hills, braided river, big sky, late afternoon light, no buildings, no people, no roads,
no signage, muted natural colours, large-format landscape photography
```
**D. Flat illustration — ballot box** (SDXL + LoRA)
```
Minimal flat editorial illustration of a ballot box with a single folded ballot paper, thin uniform
outlines, limited palette of navy, warm grey and off-white, flat vector shapes, no shading, no
gradients, plain off-white background, generous negative space, restrained civic infographic style
```
**E. Flat illustration — paired scales / magnifier / shield**: same prompt with the object swapped.

**Negative block (SDXL; Chroma uses the positive minus the style terms):**
```
text, letters, words, watermark, logo, mascot, cartoon face, cute, kawaii, anime, 3D render,
drop shadow, gradient mesh, corporate memphis, human figure, face, hands
```

### What to measure
1. **Text-incidence rate** — 8 samples per class; any legible glyphs = defect (target 0).
2. **Darkened-plate test** — overlay each background/landscape candidate at 50% black with white text
   at final size; side-by-side "looks intentional?" judgement. This is the real acceptance test for
   plates.
3. **Series consistency** — 4 illustration icons per model config; rate palette, line weight, corner
   treatment variance (LoRA on vs off).
4. **Prohibited-content audit** — faces, figures, flags, party symbols, anything implying an outcome.
5. **Ops** — VRAM peak (`nvidia-smi` during run) and wall time per image; run while the LLM benchmark
   is active to learn real contention. Record fp8 schnell vs SDXL behaviour first, since SDXL is the
   fallback when the box is busy.
6. **Upscale pass** — one grain-heavy plate and one illustration through Real-ESRGAN ×4 → downsample to
   1200×630 and 1080×1350; check halos and grain survival.

### Targets
- Share card source: generate 1216×576 → ×4 → 2432×1152 → resize 1200×630.
- Carousel slide source: generate 864×1080 → ×4 → 1728×2160 → resize 1080×1350.

---

## 6. Verification status — what was read where

Read directly **[card]**: FLUX.1-schnell licence (Apache-2.0 full text, BFL GitHub), FLUX.1-dev licence
(Non-Commercial v1.1.1 full text, BFL GitHub), SDXL LICENSE.md (CreativeML Open RAIL++-M full text on
the model repo), Chroma1-HD model card statement + frontmatter, Kolors README licence section,
Playground v2.5 LICENSE.md excerpts, Comfy-Org/flux1-schnell README, model file sizes/gating flags via
the HuggingFace API, sampler settings from Comfy-Org/workflow_templates JSON.

Only **[secondary]**: Real-ESRGAN weights-are-BSD-3 claim (AMD mirror card + OpenModelDB, corroborated
by the upstream BSD-3 code licence), SD3.5 community-licence commercial clause (stability.ai/license —
the SD3.5 repos are gated and returned 401 on raw LICENSE), OpenModelDB rights summary. VRAM figures
are all estimates (est) — nothing was executed on the GPU, per the handover arrangement.
