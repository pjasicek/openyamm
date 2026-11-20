# MM7 visual repairs — 2026-10-04

All seven repair families are complete and locally accepted, including Harpy at 128/128. Blaster Guy was excluded and remains unchanged. The repair scope contains 621 accepted bitmaps out of 621.

| Family | Accepted native bitmaps | Status | Minimum generated sampling |
| --- | ---: | --- | ---: |
| Ghoul A | 160/160 | Complete | 2.056× |
| Treant A | 33/33 | Complete | 1.366× |
| zUltra Dragon A | 172/172 | Complete | 1.358× |
| zchicken a | 49/49 | Complete | 6.972× |
| zdog a | 50/50 | Complete | 3.338× |
| zrat a | 29/29 | Complete | 5.479× |
| Harpy A | 128/128 | Complete | 1.972× |

All exports are physical 2× masters with base/mask atlases, all native palettes and exact animation/placement metadata. Treant, Dragon and Harpy retain reviewed complete sheets at about 1.37×, 1.36× and 1.97× actual generated sampling respectively. Export dimensions do not imply extra generated detail.

The repairs correct the Dog muzzle, Chicken rear anatomy, Rat rolling sequence, Treant hit geometry/placement, Dragon clipped rear wings and missing native flame phases, and Ghoul rear/prone poses plus hair-mask spill onto eyes, skin and clothing.

Every generated repair used built-in imagegen with the required MM7 restoration context, all native frames of one animation/view on one tightly packed sheet, a separate outline-only guide and detailed same-family appearance references. Native colour and alpha remained untouched in the submitted references. Shared native-coordinate union crops start at two pixels of native padding and were enlarged when poses required room. Registration uses one uniform scale per cycle and documented whole-pose translations.

Every pose, independent placement features, unresized 100% material samples, alpha edges, and every palette/mask pose were inspected before acceptance. Submitted native and outline sheets were rebuilt pixel-for-pixel during verification. Timing, mirrors, aliases, unused-art playback exclusion, native runtime scale and fractional anchors are preserved. This is a static visual review, with no claim of watched real-time playback.

The selected Harpy v24 return contains all ten death-animation steps on one packed sheet. Its interleaved cell order prevents different scaling of airborne and prone rows; native playback order remains unchanged. The seven new bitmaps preserve the raised-talon final poses, wing geometry and animation progression. Their common anatomical sampling is 1.975×, with a conservative rounded-pixel minimum of 1.972×. The first three shared hit/death frames retain their existing canonical accepted masters. All previous 121 accepted sprite, mask, atlas and preview PNGs remain byte-identical. Failed and superseded attempts are retained as provenance.

[Open Harpy in the separate repair reviewer](http://127.0.0.1:8817/#mm7_harpy) — seven complete families, 621 frames. Its native images, every palette atlas page and every material-mask channel pass localhost API checks, including the complete 1500 ms death sequence in all eight aliased directions. The final browser render is shown in [reviewer_smoke.png](reviewer_smoke.png). The collection is [hash pinned](../repair_review_collection.json). Local reviewer decisions and fixups are isolated under `repair_review_state/`. Its decision counters reflect new human decisions, separately from frozen restoration acceptance.

The wider audit finds 71/72 MM7 families with complete visual acceptance; Blaster Guy remains partial. It rechecked 48,487 recorded hashes and 97,512 current native animation steps. Four recorded checksums differ for the shared sprite-table container, while every saved native group snapshot for those four families matches current data exactly. Strict whole-file receipts pass for 67 accepted packages; scoped native-group verification supports 71. Accepted artwork has no hash discrepancies. Historical receipts were preserved. Current descriptor rows append three named inspection controls; all 19 original restoration columns match saved snapshots exactly.

39/72 current packages load directly in the unchanged shared reviewer. The remaining 33 require review-format conversion before an all-MM7 collection can be assembled. The older session-04 collection points at the earlier Harpy manifest and is stale; the new repair collection is valid. No gameplay installation was performed.

The earlier Thief mask warning was a checksum-convention error: accepted files and its original sorted-filename/PNG-byte mask digest match the receipt. See [thief_receipt_check.json](thief_receipt_check.json).

Source projects, shared tools/skills, global ledgers and runtime assets were left unchanged by this repair run. Original checkpoints and failed generation attempts remain available.

Detailed coverage and evidence: [repair_report.json](repair_report.json), [all_mm7_post_repair.json](all_mm7_post_repair.json).
