import { getDataset } from "../src/lib/data.ts";

const d = getDataset();
console.log(JSON.stringify({
  fixture: d.isFixture,
  note: d.fixtureNote,
  ...d.counts,
}, null, 2));
