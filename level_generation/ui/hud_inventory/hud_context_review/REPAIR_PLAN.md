# HUD x2 magenta repair status · 2026-09-23

The [review browser](index.html) covers 725 HUD and UI names: 332 exact-x2 candidates, 392 native fallbacks and one
generated minimap surface. The user's 49 pasted flags remain visible as an incomplete first review. The original
[flag audit](user_flag_audit.csv) and [whole-candidate audit](all_candidate_alpha_audit.csv) remain keyed to the
unrepaired x2 sources. Their 137 attention marks among the 332 candidates are heuristic inspection leads, not
automatic rejection.

| Repair group | Current review output | Remaining check |
| --- | --- | --- |
| Uniform magenta matte on transparent cutouts | [94 true-alpha RGBA files](alpha_repair/manifest.json), made with the existing spatial matte extractor and per-family parameters | Inspect silhouette, material color, edge softness and pair/animation consistency. `butn4u/d` retain green backing behind the key; decide whether that plate is intrinsic. |
| Pink spill on opaque outer borders | [159 color-repaired files](opaque_edge_repair/manifest.json), guided by the native opaque border; candidate alpha and pixels outside the outer-edge mask are unchanged | Inspect the repaired rail/line color on dark and light backgrounds, especially tiny arrows, follower controls and button families. Keep these panels opaque. |
| Wrong `manaFRM` filled tube | [New imagegen true-alpha frame](targeted_repairs/manafrm-report.json), fitted to 20 × 102 with both fill channels open and 0.9535 silhouette overlap against native | Visually approve the dark rail painting and [empty/half/full composition](diagnostic_alpha/manafrm-contract.png). The separate green health and blue mana fills remain raw-only. |
| Inconsistent `but20`–`but26` U/H/D state emphasis | [One regenerated 21-state sheet](button_triplets/README.md), fitted into 21 exact-x2 opaque review previews; native H brightness range 13.88–21.13, prior x2 2.57–22.43, new x2 12.87–18.12 | Inspect wording, texture, frame geometry and the visual feel of hover/pressed in the browser. No runtime installation yet. |
| Unfitted raw returns | `topbar`, `npcpnl`, `status_bar`, `manaB`, `ManaG`, `joystick_base_default` among 332 raw-only names | Fit the retained art to exact native x2 canvases. `topbar` and `npcpnl` should stay opaque; no alpha cleanup can substitute for fitting. |
| Other visual/state defects | Follower arrow symbols, map zoom states, buff panel variants and other second-pass notes | Review each original/repaired state in context. Pink removal alone does not establish correct symbol, color, shape or position. |

The default browser display uses repaired review files only when the original candidate, native source and repair
output hashes match. **Display → Original x2 before repair** shows the prior art. The
[post-repair audit](post_repair_summary.json) found review repairs for all 43 user-flagged exact-x2 assets; six flags
still lack a fitted x2 asset. Across all 332 default x2 images, no opaque near-key pink area exceeds 0.03% of an
image. This does not establish that every subtle color cast or
geometry defect is gone; the browser's flags and second-pass notes remain active.

The first two repair groups are deterministic because the art had an extraction matte or localized edge spill. The
`manaFRM` art itself was wrong, so it received a targeted built-in imagegen return with actual transparency. A broad
regeneration of all HUD sheets would risk changing identities and clipping cells that only needed alpha or edge
cleanup. The imagegen prompt and raw master are retained under [targeted_repairs](targeted_repairs).

None of these files has been staged as runtime `icons_x2` or accepted by the restoration queue. Use the browser and
the [alpha](alpha_repair/contact-01.png) and [opaque edge](opaque_edge_repair/contact-01.png) contact sheets to
approve art and registration before installation.
