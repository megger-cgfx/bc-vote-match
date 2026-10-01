import fs from "node:fs";
import path from "node:path";

const OUT = path.join(process.cwd(), "out");
const raw = fs.readFileSync(path.join(OUT, "results/index.html"), "utf8");
const text = raw
  .replace(/<script[\s\S]*?<\/script>/g, " ")
  .replace(/<[^>]*>/g, " ")
  .replace(/&#x27;/g, "'")
  .replace(/&amp;/g, "&")
  .replace(/\s+/g, " ");
console.log(text.slice(0, 2000));
console.log("\n--- markers ---");
for (const m of ["Share this result", "Copy link", "share", "No answers yet", "alignment", "compass", "aria-label"]) {
  console.log(m, "=>", raw.includes(m));
}
