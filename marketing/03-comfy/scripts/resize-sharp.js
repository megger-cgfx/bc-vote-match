#!/usr/bin/env node
/*
 * resize-sharp.js — downscale an upscaled master to an exact target pixel size with
 * sharp (same dependency render-card.js uses; run from the repo root).
 *
 *   node marketing/03-comfy/scripts/resize-sharp.js <in.png> <out.png> <w> <h> [cover|contain]
 *
 * cover  : centre-crop to fill exactly w x h (the plate slot sizes)
 * contain: fit inside w x h, preserving aspect (default; used when the target is a
 *          square master for a square source)
 * Prints one JSON line. Exit 1 on any mismatch between requested and written size.
 */
const sharp = require('sharp');

(async () => {
  const [inP, outP, wArg, hArg, mode = 'cover'] = process.argv.slice(2);
  if (!inP || !outP || !wArg || !hArg) {
    process.stderr.write('usage: resize-sharp.js <in> <out> <w> <h> [cover|contain]\n');
    process.exit(1);
  }
  const w = parseInt(wArg, 10);
  const h = parseInt(hArg, 10);
  const buf = await sharp(inP)
    .resize(w, h, { fit: mode, position: 'centre' })
    .png()
    .toBuffer();
  const meta = await sharp(buf).metadata();
  if (meta.width !== w || meta.height !== h) {
    process.stderr.write(`size mismatch: got ${meta.width}x${meta.height}, want ${w}x${h}\n`);
    process.exit(1);
  }
  require('fs').mkdirSync(require('path').dirname(outP), { recursive: true });
  require('fs').writeFileSync(outP, buf);
  process.stdout.write(JSON.stringify({ out: outP, width: w, height: h, bytes: buf.length }) + '\n');
})().catch((e) => {
  process.stderr.write('resize failed: ' + (e && e.message ? e.message : e) + '\n');
  process.exit(1);
});
