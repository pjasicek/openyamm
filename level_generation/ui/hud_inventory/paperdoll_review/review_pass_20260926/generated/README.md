# Retained generation masters

`batches.json` maps each equal-cell reference sheet to native asset targets. Each batch directory retains
`native.png`, `current.png` where used, `manifest.json`, `prompt.txt`, and the unmodified tool-return `raw.png`.
Reference-native identities and duplicate mappings are retained. Generation used the built-in image-generation tool.

Processing uses the native foreground bounds and native canvas at 2×; raw returns are never installed directly.
`chipped_blades` deliberately overrides item001, item011 and item006 from earlier identity batches after the user's
clarification: chipped worn edges, not regular serrations. `chain_complete` replaces a raw-clipped 6chain2v2a.
The large-quality master remains unchanged; the gold sleeve cutout is applied during extraction in `repair_assets.py`.

`7item221-master.png` is the separately requested sword regeneration: silver/blue blade, gold guard and slim handle,
using the original item as the identity reference. Its exact submitted prompt was not retained as a file; this is a
purpose note, not a reconstruction of that prompt. Its master SHA-256 and method are recorded in `repairs.json`.
Earlier interpretations are retained for provenance and are superseded by the later batches in manifest order.
