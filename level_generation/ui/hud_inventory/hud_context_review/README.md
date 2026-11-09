# HUD context review

Open [index.html](index.html) in a browser. The page assembles the active gameplay UI YAML into selectable scenes,
including both desktop HUD layouts, mobile HUD, buff panels, character pages, every spellbook school, journal pages,
inspect windows, chest, rest, dialogue, and other in-game views. The expanded HUD shows three illustrative follower
portraits in their dynamic slots. The asset catalogue also includes the states referenced
by those layouts and known dynamic HUD and journal animation names.

The user's 2026-09-23 HUD signoff is enumerated in the [acceptance audit](acceptance/README.md), with all 332
displayed exact-x2 icon names, dimensions, hashes and expected runtime destinations. Native fallbacks remain
outside that x2 set.

The scene uses an exact-x2 candidate when one is available in the second-pass evidence or staged exports. Otherwise it
shows the native icon and marks it as a fallback. The default x2 view now uses hash-bound repaired review files where
available: 94 true-alpha magenta-matte extractions, 159 opaque outer-edge color repairs, one targeted imagegen
true-alpha `manaFRM` reconstruction and [21 regenerated U/H/D button states](button_triplets/README.md). The source candidate, original color-key preview and repaired output remain
separately linked in the detail panel. The **Display** selector can show the originals before repair. None of the
repaired files is installed in runtime assets or marked accepted. Scene placements follow
the YAML at 640 × 480. Party portraits and generated map content provide context; they are illustrative. Conditional
visibility, text, runtime object placement, and game rendering are simplified for visual review.

Click an element or catalogue card to compare native and candidate art, open the source evidence, and record **Looks
good** or **Flag issue** with a note. Decisions live in the browser's local storage. Export review JSON to share or
preserve them; importing that file restores them. These browser decisions do not change canonical second-pass
acceptance or runtime assets.

The **49 pasted flags** filter shows the incomplete user review from 2026-09-23. These flags are shown separately from
new decisions saved in the browser, so the original review stays visible without overwriting later decisions. The
**Alpha audit attention** filter uses a coarse comparison with native transparency and a magenta-pixel check to find
additional pieces worth inspecting. The current audit nominates 137 of 332 exact-x2 candidates; those numbers are
inspection leads, not automatic rejection. Purple materials, changed art bounds, and opaque UI panels need individual
judgment. [user_flag_audit.csv](user_flag_audit.csv) and
[all_candidate_alpha_audit.csv](all_candidate_alpha_audit.csv) contain measurements. **Raw only / not fitted** shows
retained imagegen returns that still lack an exact-x2 export; the scene falls back to native art.

The [alpha repair manifest](alpha_repair/manifest.json) and four contact sheets under `alpha_repair/` record the
94 true-alpha cutouts. The [opaque edge manifest](opaque_edge_repair/manifest.json) and seven contact sheets under
`opaque_edge_repair/` record native-guided color corrections to outer pixels while preserving alpha and all other
pixels. The [post-repair audit](post_repair_summary.json) shows that all 43 user-flagged exact-x2 assets have a
repair preview; the other six flags are raw-only/unfitted. The default browser display has no visible near-key pink
patches over 0.03% of any of its 332 x2 images.
This is a chroma check, not visual acceptance. The [imagegen `manaFRM` report](targeted_repairs/manafrm-report.json)
retains the transparent master, exact-x2 fit and measurements. [Empty/half/full bars](diagnostic_alpha/manafrm-contract.png)
show that the two fill channels remain open. The eleven earlier [dark/light matte pilots](diagnostic_alpha/measurements.json)
remain as additional visual evidence.

The `butn4` key states still contain a green rectangular backing after exterior magenta removal, so that pair needs
a foreground composition decision. `topbar` and `npcpnl` remain opaque raw-only returns without fitted x2 exports;
they should not be made transparent just to clear a diagnostic flag.

[coverage.csv](coverage.csv) lists every name, source, exact-x2 availability, candidate status and YAML use.
[REPAIR_PLAN.md](REPAIR_PLAN.md) records the repair routes for the pasted flags and additional alpha audit leads.

To refresh after the parallel second pass produces new exact-x2 candidates, regenerate the repaired review files,
then rebuild the browser. Every repair is tied to hashes of its original candidate and native source; stale repairs
are ignored by `build.py`:

```sh
python3 level_generation/ui/hud_inventory/hud_context_review/build.py
python3 level_generation/ui/hud_inventory/hud_context_review/alpha_repair.py
python3 level_generation/ui/hud_inventory/hud_context_review/opaque_edge_repair.py
python3 level_generation/ui/hud_inventory/hud_context_review/targeted_repairs/fit_manafrm.py
python3 level_generation/ui/hud_inventory/hud_context_review/bar_contract.py
python3 level_generation/ui/hud_inventory/hud_context_review/button_triplets/prepare.py
python3 level_generation/ui/hud_inventory/hud_context_review/button_triplets/fit.py
python3 level_generation/ui/hud_inventory/hud_context_review/build.py
python3 level_generation/ui/hud_inventory/hud_context_review/audit_user_flags.py
```

The builder reads inventory, current review evidence, acceptance state and active YAML. It writes only this folder's
`data.js`, `coverage.csv`, `native/` and `restored_display/`; it does not edit the restoration queue or the game's
`icons_x2` folders.

To reproduce the eleven earlier cleanup comparisons, run `python3
level_generation/ui/hud_inventory/hud_context_review/matte_pilot.py` before the audit command.
