#!/usr/bin/env python3
"""run-shotlist.py — batch driver for the BCVM production shot list on the proven box.

Loops over the shot list and calls comfy_run.py once per image (the driver's built-in
lock serialises jobs; we never parallelise). Provenance for every job is appended to
marketing/03-comfy/shotlist-log.jsonl as one JSON line per attempt, so the campaign
manifest can be filled honestly afterwards.

    python3 marketing/03-comfy/scripts/run-shotlist.py gen       # 22 generation jobs
    python3 marketing/03-comfy/scripts/run-shotlist.py upscale   # RealESRGAN x4 per JOB file
    python3 marketing/03-comfy/scripts/run-shotlist.py gen --only a1-s1,c1   # rerun subset

Upscale reads its work list from marketing/03-comfy/upscale-jobs.json (written by the
curation step): [{"id":..., "src": <local raw png>, "prefix": <save prefix>}, ...].
The raw is pushed to the box's ComfyUI/input/ with the vast-ssh helper, then the
RealESRGAN_x4plus workflow runs through comfy_run.py and the 4x PNG is pulled back to
marketing/assets/selected/masters/<id>-esrgan4x.png.
"""
import json
import os
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
REPO_HELPER = os.path.expanduser(
    "<vast-ssh-helper>")
INSTANCE = "<instance-id>"
COMFY_RUN = os.path.join(ROOT, "marketing", "03-comfy", "comfy_run.py")
WF_DIR = os.path.join(ROOT, "marketing", "03-comfy", "workflows")
RAW_DIR = os.path.join(ROOT, "marketing", "assets", "comfy-raw")
MASTER_DIR = os.path.join(ROOT, "marketing", "assets", "selected", "masters")
LOG = os.path.join(ROOT, "marketing", "03-comfy", "shotlist-log.jsonl")

FLUX_CKPT = "flux1-schnell-fp8.safetensors"
SDXL_CKPT = "sd_xl_base_1.0.safetensors"
FLAT_LORA = "minimal_flat_illustration,_emotional_scene.safetensors"
ESRGAN = "RealESRGAN_x4plus.pth"

FLUX_NEG = ("text, letters, words, numbers, watermark, logo, signature, signage, "
            "people, person, flag, ballot, map, landmark")
SDXL_NEG = ("text, letters, words, numbers, watermark, logo, signature, signage, "
            "mascot, cartoon face, cute, kawaii, anime, 3D render, drop shadow, "
            "gradient mesh, corporate memphis, human figure, face, hands, flag, "
            "ballot, map, landmark")

PLATE_STYLE = ", muted desaturated palette, calm, low contrast, flat minimal, no text"

# (id, class, prompt, seed, width, height)
JOBS = [
    # A — abstract background plates, FLUX.1-schnell fp8, 1216x576
    ("a1-s1", "abstract", "soft abstract texture of layered translucent paper fibres, muted navy and warm grey, fine grain, flat minimal, no text", 20261011, 1216, 576),
    ("a1-s2", "abstract", "soft abstract texture of layered translucent paper fibres, muted navy and warm grey, fine grain, flat minimal, no text", 20261012, 1216, 576),
    ("a2-s1", "abstract", "abstract topographic contour lines, very low contrast, deep ink blue on near-black, subtle flat vector, no text", 20261021, 1216, 576),
    ("a2-s2", "abstract", "abstract topographic contour lines, very low contrast, deep ink blue on near-black, subtle flat vector, no text", 20261022, 1216, 576),
    ("a3-s1", "abstract", "abstract fine grid of thin graphite lines on off-white, institutional document texture, very low contrast, no text", 20261031, 1216, 576),
    ("a3-s2", "abstract", "abstract fine grid of thin graphite lines on off-white, institutional document texture, very low contrast, no text", 20261032, 1216, 576),
    ("a4-s1", "abstract", "soft gradient mesh of calm muted blue to grey with subtle film grain, minimal, no text", 20261041, 1216, 576),
    ("a4-s2", "abstract", "soft gradient mesh of calm muted blue to grey with subtle film grain, minimal, no text", 20261042, 1216, 576),
    # B — generic landscape plates, FLUX.1-schnell fp8, 1216x576
    ("b1-s1", "landscape", "coastal temperate rainforest in mist, generic Pacific Northwest, muted overcast light, no people, no buildings, no roads, no signage", 20261051, 1216, 576),
    ("b1-s2", "landscape", "coastal temperate rainforest in mist, generic Pacific Northwest, muted overcast light, no people, no buildings, no roads, no signage", 20261052, 1216, 576),
    ("b2-s1", "landscape", "distant mountain range above a low cloud layer, muted blue-grey, generic, no people, no buildings, no roads", 20261061, 1216, 576),
    ("b2-s2", "landscape", "distant mountain range above a low cloud layer, muted blue-grey, generic, no people, no buildings, no roads", 20261062, 1216, 576),
    ("b3-s1", "landscape", "dry interior plateau grassland above a river valley, muted, generic British Columbia interior, no people, no buildings, no roads", 20261071, 1216, 576),
    ("b3-s2", "landscape", "dry interior plateau grassland above a river valley, muted, generic British Columbia interior, no people, no buildings, no roads", 20261072, 1216, 576),
    ("b4-s1", "landscape", "calm river valley at dawn with mist, muted, generic, no people, no buildings, no roads", 20261081, 1216, 576),
    ("b4-s2", "landscape", "calm river valley at dawn with mist, muted, generic, no people, no buildings, no roads", 20261082, 1216, 576),
    # C — flat editorial illustrations, SDXL 1.0 base + flat LoRA, 1024x1024
    ("c1", "illustration", "Minimal flat editorial illustration of a neat stack of blank documents, thin uniform outlines, limited palette of muted navy and warm grey, flat vector shapes, no shading, no gradients, plain off-white background, generous negative space, restrained civic infographic style, no text, no lettering, no numbers", 20261091, 1024, 1024),
    ("c2", "illustration", "Minimal flat editorial illustration of a magnifying glass held over blank ruled lines, thin uniform outlines, limited palette of muted navy and warm grey, flat vector shapes, no shading, no gradients, plain off-white background, generous negative space, restrained civic infographic style, no text, no lettering, no numbers", 20261092, 1024, 1024),
    ("c3", "illustration", "Minimal flat editorial illustration of a simple two-axis grid with a few unlabelled dots, thin uniform outlines, limited palette of muted navy and warm grey, flat vector shapes, no shading, no gradients, plain off-white background, generous negative space, restrained civic infographic style, no text, no lettering, no numbers", 20261093, 1024, 1024),
    ("c4", "illustration", "Minimal flat editorial illustration of oversized quotation marks, thin uniform outlines, limited palette of muted navy and warm grey, flat vector shapes, no shading, no gradients, plain off-white background, generous negative space, restrained civic infographic style, no text, no lettering, no numbers", 20261094, 1024, 1024),
    ("c5", "illustration", "Minimal flat editorial illustration of a plain lidded archive box, thin uniform outlines, limited palette of muted navy and warm grey, flat vector shapes, no shading, no gradients, plain off-white background, generous negative space, restrained civic infographic style, no text, no lettering, no numbers", 20261095, 1024, 1024),
    ("c6", "illustration", "Minimal flat editorial illustration of a table of empty rows and columns, thin uniform outlines, limited palette of muted navy and warm grey, flat vector shapes, no shading, no gradients, plain off-white background, generous negative space, restrained civic infographic style, no text, no lettering, no numbers", 20261096, 1024, 1024),
]


def flux_workflow(prompt, seed, w, h, prefix):
    return {
        "4": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": FLUX_CKPT}},
        "6": {"class_type": "CLIPTextEncode",
              "inputs": {"text": prompt, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode",
              "inputs": {"text": FLUX_NEG, "clip": ["4", 1]}},
        "13": {"class_type": "EmptySD3LatentImage",
               "inputs": {"width": w, "height": h, "batch_size": 1}},
        "3": {"class_type": "KSampler",
              "inputs": {"seed": seed, "steps": 4, "cfg": 1.0,
                         "sampler_name": "euler", "scheduler": "simple",
                         "denoise": 1.0, "model": ["4", 0], "positive": ["6", 0],
                         "negative": ["7", 0], "latent_image": ["13", 0]}},
        "8": {"class_type": "VAEDecode",
              "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage",
              "inputs": {"filename_prefix": prefix, "images": ["8", 0]}},
    }


def sdxl_lora_workflow(prompt, seed, w, h, prefix):
    return {
        "4": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": SDXL_CKPT}},
        "10": {"class_type": "LoraLoader",
               "inputs": {"model": ["4", 0], "clip": ["4", 1],
                          "lora_name": FLAT_LORA,
                          "strength_model": 0.7, "strength_clip": 0.7}},
        "6": {"class_type": "CLIPTextEncode",
              "inputs": {"text": prompt, "clip": ["10", 1]}},
        "7": {"class_type": "CLIPTextEncode",
              "inputs": {"text": SDXL_NEG, "clip": ["10", 1]}},
        "13": {"class_type": "EmptyLatentImage",
               "inputs": {"width": w, "height": h, "batch_size": 1}},
        "3": {"class_type": "KSampler",
              "inputs": {"seed": seed, "steps": 25, "cfg": 7.0,
                         "sampler_name": "dpmpp_2m", "scheduler": "karras",
                         "denoise": 1.0, "model": ["10", 0], "positive": ["6", 0],
                         "negative": ["7", 0], "latent_image": ["13", 0]}},
        "8": {"class_type": "VAEDecode",
              "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage",
              "inputs": {"filename_prefix": prefix, "images": ["8", 0]}},
    }


def esrgan_workflow(remote_input_name, prefix):
    return {
        "10": {"class_type": "UpscaleModelLoader",
               "inputs": {"model_name": ESRGAN}},
        "11": {"class_type": "LoadImage",
               "inputs": {"image": remote_input_name}},
        "12": {"class_type": "ImageUpscaleWithModel",
               "inputs": {"upscale_model": ["10", 0], "image": ["11", 0]}},
        "9": {"class_type": "SaveImage",
              "inputs": {"filename_prefix": prefix, "images": ["12", 0]}},
    }


def log(row):
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
        fh.flush()


def run_comfy(wf, out_png, timeout=900):
    t0 = time.time()
    r = subprocess.run(
        [sys.executable, COMFY_RUN, "--workflow", wf, "--instance", INSTANCE,
         "--out", out_png, "--timeout", str(timeout)],
        capture_output=True, text=True, timeout=timeout + 300)
    wall = round(time.time() - t0, 1)
    stats = None
    for line in (r.stdout or "").splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                stats = json.loads(line)
            except json.JSONDecodeError:
                pass
    return r.returncode, stats, (r.stderr or "")[-1500:], wall


def do_gen(only=None):
    os.makedirs(WF_DIR, exist_ok=True)
    os.makedirs(RAW_DIR, exist_ok=True)
    for jid, cls, prompt, seed, w, h in JOBS:
        if only and jid not in only:
            continue
        out_png = os.path.join(RAW_DIR, jid + ".png")
        if os.path.exists(out_png):
            print("skip (exists): %s" % jid, flush=True)
            continue
        prefix = "bcvm-" + jid
        if cls == "illustration":
            wf = sdxl_lora_workflow(prompt, seed, w, h, prefix)
            model = SDXL_CKPT + " + " + FLAT_LORA + " @0.7"
            sampler, steps, cfg = "dpmpp_2m/karras", 25, 7.0
        else:
            wf = flux_workflow(prompt, seed, w, h, prefix)
            model = FLUX_CKPT
            sampler, steps, cfg = "euler/simple", 4, 1.0
        wf_path = os.path.join(WF_DIR, jid + ".json")
        with open(wf_path, "w") as fh:
            json.dump(wf, fh, indent=1)
        print("RUN %s ..." % jid, flush=True)
        rc, stats, err, wall = run_comfy(wf_path, out_png)
        row = {
            "id": jid, "class": cls, "prompt": prompt, "seed": seed,
            "width": w, "height": h, "model": model, "sampler": sampler,
            "steps": steps, "cfg": cfg,
            "out": os.path.relpath(out_png, ROOT),
            "workflow": os.path.relpath(wf_path, ROOT),
            "comfy_run_rc": rc, "comfy_run": stats, "wall_s": wall,
            "error": err if rc != 0 else None,
            "finished": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }
        log(row)
        if rc != 0:
            print("FAIL %s: %s" % (jid, err), flush=True)
        else:
            print("OK %s -> %s (%ss)" % (jid, row["out"], wall), flush=True)


def do_upscale():
    jobs_path = os.path.join(ROOT, "marketing", "03-comfy", "upscale-jobs.json")
    with open(jobs_path) as fh:
        jobs = json.load(fh)
    os.makedirs(WF_DIR, exist_ok=True)
    os.makedirs(MASTER_DIR, exist_ok=True)
    for job in jobs:
        jid, src = job["id"], os.path.join(ROOT, job["src"])
        out_png = os.path.join(MASTER_DIR, jid + "-esrgan4x.png")
        if os.path.exists(out_png):
            print("skip (exists): %s" % jid, flush=True)
            continue
        remote_name = "bcvm-up-%s.png" % jid
        r = subprocess.run([REPO_HELPER, "--put", INSTANCE, src,
                            "/workspace/ComfyUI/input/" + remote_name],
                           capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            log({"id": jid, "phase": "upscale", "error": "put failed: " + (r.stderr or "")[-500:]})
            print("FAIL put %s" % jid, flush=True)
            continue
        wf = esrgan_workflow(remote_name, "bcvm-up-" + jid)
        wf_path = os.path.join(WF_DIR, "up-" + jid + ".json")
        with open(wf_path, "w") as fh:
            json.dump(wf, fh, indent=1)
        print("UP %s ..." % jid, flush=True)
        rc, stats, err, wall = run_comfy(wf_path, out_png, timeout=1200)
        log({"id": jid, "phase": "upscale", "src": job["src"],
             "out": os.path.relpath(out_png, ROOT), "comfy_run_rc": rc,
             "comfy_run": stats, "wall_s": wall,
             "error": err if rc != 0 else None,
             "finished": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
        if rc != 0:
            print("FAIL up %s: %s" % (jid, err), flush=True)
        else:
            print("OK up %s (%ss)" % (jid, wall), flush=True)


def main():
    phase = sys.argv[1] if len(sys.argv) > 1 else "gen"
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
    if phase == "gen":
        do_gen(only)
    elif phase == "upscale":
        do_upscale()
    else:
        sys.exit("unknown phase: " + phase)
    print("PHASE %s DONE" % phase, flush=True)


if __name__ == "__main__":
    main()
