#!/usr/bin/env node
/*
 * render-card.js — rasterise an SVG card source to an exact-pixel PNG.
 *
 * The marketing assets are authored as SVG *source* (diffable, reviewable, no browser
 * involved) and rasterised here with sharp, which is already a repo dependency
 * (libvips + cairo/pango). Density 72 is what makes the output match the SVG's declared
 * width/height exactly; density 96 overscales by 4/3.
 *
 * Usage:
 *   node marketing/tools/render-card.js <in.svg> <out.png> [--w N --h N] [--plate img.png] [--overlay 0.55]
 *
 *   --w/--h    assert the rendered size; exit 1 on mismatch so a bad card never ships quietly
 *   --plate    raster image composited *behind* the SVG (the SVG must have a transparent
 *              background). Cover-cropped to the target size, so a 1024x1024 generation can
 *              back a 1200x630 card.
 *   --overlay  0..1 darkening applied to the plate before the SVG goes on top. Text over a
 *              photographic plate needs this; without it legibility depends on luck.
 *
 * Prints one JSON line to stdout. Exit codes: 0 ok, 1 bad args or size mismatch, 2 render error.
 */
const fs = require('fs');
const path = require('path');

function die(code, msg) {
  process.stderr.write(msg + '\n');
  process.exit(code);
}

const argv = process.argv.slice(2);
const positional = [];
const opts = {};
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === '--w' || a === '--h' || a === '--plate' || a === '--overlay') {
    opts[a.slice(2)] = argv[++i];
  } else if (a.startsWith('--')) {
    die(1, 'unknown flag ' + a);
  } else {
    positional.push(a);
  }
}

const [inSvg, outPng] = positional;
if (!inSvg || !outPng) die(1, 'usage: render-card.js <in.svg> <out.png> [--w N --h N] [--plate p.png] [--overlay 0..1]');
if (!fs.existsSync(inSvg)) die(1, 'no such svg: ' + inSvg);

let sharp;
try {
  sharp = require('sharp');
} catch (e) {
  die(2, 'sharp not resolvable from ' + process.cwd() + ' — run from the repo root: ' + e.message);
}

async function main() {
  const svg = fs.readFileSync(inSvg);
  const wantW = opts.w ? parseInt(opts.w, 10) : null;
  const wantH = opts.h ? parseInt(opts.h, 10) : null;

  // Render the SVG first. Its own dimensions are the target when --w/--h are absent, and
  // they are the ground truth we later assert against.
  const rendered = await sharp(svg, { density: 72 }).png().toBuffer();
  const meta = await sharp(rendered).metadata();
  const targetW = wantW || meta.width;
  const targetH = wantH || meta.height;

  let out;
  if (opts.plate) {
    if (!fs.existsSync(opts.plate)) die(1, 'no such plate: ' + opts.plate);

    // Resolve the plate to the target size in its own step. Do not read metadata() off a
    // pipeline that has pending .resize() on it: metadata() reports the *input* image and
    // you end up building an overlay at the wrong size.
    let plate = await sharp(opts.plate)
      .resize(targetW, targetH, { fit: 'cover', position: 'centre' })
      .png()
      .toBuffer();

    if (opts.overlay !== undefined) {
      const o = Math.max(0, Math.min(1, parseFloat(opts.overlay)));
      if (!Number.isFinite(o)) die(1, '--overlay must be a number between 0 and 1');
      plate = await sharp(plate)
        .composite([
          {
            input: Buffer.from(
              `<svg xmlns="http://www.w3.org/2000/svg" width="${targetW}" height="${targetH}">` +
                `<rect width="${targetW}" height="${targetH}" fill="#000" fill-opacity="${o}"/></svg>`
            ),
            blend: 'over',
          },
        ])
        .png()
        .toBuffer();
    }

    out = await sharp(plate)
      .composite([{ input: rendered, top: 0, left: 0 }])
      .png()
      .toBuffer();
  } else {
    out = rendered;
  }

  fs.mkdirSync(path.dirname(path.resolve(outPng)), { recursive: true });
  fs.writeFileSync(outPng, out);

  const finalMeta = await sharp(out).metadata();
  const report = {
    out: path.resolve(outPng),
    svg: path.resolve(inSvg),
    plate: opts.plate || null,
    width: finalMeta.width,
    height: finalMeta.height,
    bytes: out.length,
  };

  if (wantW && finalMeta.width !== wantW) {
    process.stdout.write(JSON.stringify(report) + '\n');
    die(1, `size mismatch: expected width ${wantW}, got ${finalMeta.width}`);
  }
  if (wantH && finalMeta.height !== wantH) {
    process.stdout.write(JSON.stringify(report) + '\n');
    die(1, `size mismatch: expected height ${wantH}, got ${finalMeta.height}`);
  }

  process.stdout.write(JSON.stringify(report) + '\n');
}

main().catch((e) => die(2, 'render failed: ' + (e && e.stack ? e.stack : e)));
