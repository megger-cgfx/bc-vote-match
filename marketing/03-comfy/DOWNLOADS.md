# DOWNLOADS.md — models to fetch on vast.ai <instance-id>

Recommended set only (see `IMAGE-MODELS.md` for why). All repos below are **ungated** — no HF token
needed. The box has `aria2c`; run these in order. Nothing here has been executed yet (the GPU is owned
by another agent as of 2026-10-01) — commands are copy-pasteable and URLs were taken from the official
ComfyUI workflow templates / HuggingFace file listings.

Total download: **~39.4 GB**.

```bash
# 0. directories
mkdir -p /workspace/ComfyUI/models/{checkpoints,diffusion_models,text_encoders,vae,loras,upscale_models}
```

## 1. FLUX.1-schnell fp8 — primary for background + landscape plates (17.24 GB)

All-in-one checkpoint (diffusion model + T5 + CLIP + VAE bundled) → standard checkpoint loader.

```bash
aria2c -x8 -s8 -c \
  -d /workspace/ComfyUI/models/checkpoints \
  -o flux1-schnell-fp8.safetensors \
  "https://huggingface.co/Comfy-Org/flux1-schnell/resolve/main/flux1-schnell-fp8.safetensors?download=true"
```

- Repo: `Comfy-Org/flux1-schnell` (ungated repack of `black-forest-labs/FLUX.1-schnell`, Apache-2.0)
- Size: 17.24 GB. Do **not** fetch the 23.78 GB fp16 file — it needs ~24GB VRAM on a shared card.

## 2. SDXL 1.0 base — illustration first choice + low-VRAM fallback (6.94 GB)

```bash
aria2c -x8 -s8 -c \
  -d /workspace/ComfyUI/models/checkpoints \
  -o sd_xl_base_1.0.safetensors \
  "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors"
```

- Repo: `stabilityai/stable-diffusion-xl-base-1.0` (ungated, CreativeML Open RAIL++-M)
- Size: 6.94 GB.

## 3. Chroma1-HD fp8mixed — plate fallback, line-art alternative (9.19 GB + 5.50 GB support)

Three files, one model. UNETLoader + CLIPLoader(type `chroma`) + VAELoader.

```bash
# 3a. the model itself
aria2c -x8 -s8 -c \
  -d /workspace/ComfyUI/models/diffusion_models \
  -o Chroma1-HD-fp8mixed.safetensors \
  "https://huggingface.co/Comfy-Org/Chroma1-HD_repackaged/resolve/main/split_files/diffusion_models/Chroma1-HD-fp8mixed.safetensors"

# 3b. T5-XXL text encoder, fp8 (5.16 GB)  [legacy alias models/clip/ also accepted by ComfyUI]
aria2c -x8 -s8 -c \
  -d /workspace/ComfyUI/models/text_encoders \
  -o t5xxl_fp8_e4m3fn_scaled.safetensors \
  "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp8_e4m3fn_scaled.safetensors"

# 3c. FLUX VAE (0.34 GB) — ungated mirror used by the official Chroma template
aria2c -x8 -s8 -c \
  -d /workspace/ComfyUI/models/vae \
  -o ae.safetensors \
  "https://huggingface.co/Comfy-Org/Lumina_Image_2.0_Repackaged/resolve/main/split_files/vae/ae.safetensors"
```

- Sizes: 9.19 GB + 5.16 GB + 0.34 GB. (bf16 alternative: `lodestones/Chroma1-HD` →
  `Chroma1-HD.safetensors` 17.80 GB into `diffusion_models/` — only if the fp8mixed variant misbehaves.)

## 4. Flat-illustration style LoRA (0.46 GB)

Note the **comma in the filename** — keep the `-o` value quoted. URL uses `%2C` for the comma.

```bash
aria2c -x8 -s8 -c \
  -d /workspace/ComfyUI/models/loras \
  -o "minimal_flat_illustration,_emotional_scene.safetensors" \
  "https://huggingface.co/ramel2/emotional-flat-illustration-sdxl-lora/resolve/main/minimal_flat_illustration%2C_emotional_scene.safetensors"
```

- Repo: `ramel2/emotional-flat-illustration-sdxl-lora` (ungated, declared `creativeml-openrail-m`)
- Size: 456.5 MB. Triggers: `minimal flat illustration`, `emotional scene`. SDXL only.

## 5. Real-ESRGAN x4plus upscaler (64 MB)

```bash
aria2c -x8 -s8 -c \
  -d /workspace/ComfyUI/models/upscale_models \
  -o RealESRGAN_x4plus.pth \
  "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
```

- Upstream release (BSD 3-Clause). Size: 63.9 MB.
- Mirror if GitHub is slow: `https://huggingface.co/amd/realesrgan-x4plus/resolve/main/RealESRGAN_x4plus.pth`

## After download — wiring (no extra nodes needed)

| Model | ComfyUI nodes | From the official template |
|---|---|---|
| flux1-schnell-fp8 | `CheckpointLoaderSimple` | `flux_schnell.json` — 4 steps, cfg 1.0, euler/simple |
| sd_xl_base_1.0 | `CheckpointLoaderSimple` (+ `LoraLoader`) | `image_sdxl_simple.json` — 25 steps, cfg 7, dpmpp_2m/karras |
| Chroma trio | `UNETLoader` + `CLIPLoader` (type `chroma`) + `VAELoader` | `image_chroma_text_to_image.json` — 26 steps, cfg 3.5, euler/beta, shift 1 |
| RealESRGAN_x4plus | `UpscaleModelLoader` | none local (API-only upscale templates in the template browser) |

Restart ComfyUI after fetching so the new files are indexed.

## Sanity checks (expected sizes)

```bash
ls -l /workspace/ComfyUI/models/checkpoints/flux1-schnell-fp8.safetensors        # ~17.24 GB
ls -l /workspace/ComfyUI/models/checkpoints/sd_xl_base_1.0.safetensors           # ~6.94 GB
ls -l /workspace/ComfyUI/models/diffusion_models/Chroma1-HD-fp8mixed.safetensors # ~9.19 GB
ls -l /workspace/ComfyUI/models/text_encoders/t5xxl_fp8_e4m3fn_scaled.safetensors# ~5.16 GB
ls -l /workspace/ComfyUI/models/vae/ae.safetensors                               # ~0.34 GB
ls -l /workspace/ComfyUI/models/loras/                                           # 456.5 MB file
ls -l /workspace/ComfyUI/models/upscale_models/RealESRGAN_x4plus.pth             # ~64 MB
```

**Do not fetch:** `black-forest-labs/FLUX.1-dev` (non-commercial licence), `Kwai-Kolors/Kolors`
(commercial registration required), any Civitai/Muapi/Shakker flat-illustration LoRA with no declared
licence, `4x-UltraSharp` (licence undeclared).
