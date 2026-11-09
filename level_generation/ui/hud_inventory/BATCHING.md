# Production batching policy

**2026-09-16 update:** the user chose a **64-cell maximum** for newly prepared dense small-art bundles.
Use [Dense64 batching](BATCHING_DENSE64.md) for the measured pixel envelope, width/height budgeting,
64-portrait reference geometry and return contract. The nine-cell commands and policies below document the
older production route; they do not limit the new dense bundle exporter.

User approved 3×3 on 2026-09-10 after the eight- and nine-item experiments. Use built-in imagegen for all
restoration artwork. A sheet is one generated image and one recorded attempt, even across frozen jobs.
This changes scheduling and packing, not fidelity, exact x2 dimensions, native placement or acceptance.

## First pass first; repairs in later batches

User steering: when most cells pass and one does not, **flag that cell and move on**. Complete the review of
each sheet, accept/stage the passing cells, and record a concrete reason with `queue.py defer CELL --reason ...`.
The checkpoint's deferred cell records are the repair ledger; raw attempts, crops and comparison evidence stay
available. Do not spend the first pass repeatedly regenerating one difficult item or mix repairs into fresh sheets.

`queue.py next` now defaults to fresh unattempted, non-deferred cells. It returns `selected_cells`, so accepted,
submitted or deferred siblings in the same frozen job are not accidentally resubmitted. Use those IDs when
building an execution sheet; do not blindly submit the whole frozen job if it has excluded siblings.

```sh
python3 level_generation/ui/hud_inventory/queue.py next --phase first-pass --limit 9
python3 level_generation/ui/hud_inventory/queue.py next --phase review --limit 9
python3 level_generation/ui/hud_inventory/queue.py next --phase retry --limit 50
```

Review the just-returned sheet before moving on. `review` finds other retained, unaccepted/non-deferred cells;
it is not a request to regenerate them. After the first pass, use `retry` to inspect failure reasons and retained
attempt paths, then group compatible failures into retry sheets using the same size/treatment/dependency rules.
Preserve accepted siblings and record each retry's outcome. A critical page/identity dependency may block its
children; process other eligible first-pass families before revisiting that blocked group. No eligible fresh work
is not proof of completion: deferred, dependency-blocked, retained and missing work remain in the full goal.

## Choose the sheet

- Default to nine related small inventory icons, compatible NPC portraits, or small controls in 3×3.
  Keep complete state sets together; use fewer occupied cells rather than splitting a pair to fill the grid.
- Conservative small-art budget: each final x2 canvas fits within 192×192; largest canvas area is at most
  four times the smallest. These are packing guards, not visual approval. Long thin weapons, dense text,
  elaborate symbols or fragile transparency may need fewer cells even below the limits.
- Large inventory art and portraits: 1–4 cells with sufficient pixels per object. Complete backgrounds,
  spellbook pages and maps remain single-image jobs. Never shrink a large background to fit nine cells.
- Spell icons retain page-first dependencies and complete normal/hover pairs (usually 2 columns, 4–8 cells).
  Player expressions, equipped variants and animation sequences retain identity/pose/timing groups and their
  existing smaller batches. Adjoining borders retain join-aware groups. Do not force these into 3×3.
- Keep namespace, palette/compositing, dependency and visual-treatment contracts compatible. Deduplicate
  only through verified reuse; do not waste a sheet on byte-identical siblings. Inspect queue attempts AND
  experiment manifests before selecting fresh work. An experiment PNG is retained work, not an accepted asset.

## Execute against the current frozen inventory queue

`jobs.json` remains authoritative for target identity and dependencies. Do not regenerate it or reset the
checkpoint to change batch size. The new command prepares an execution layout spanning those frozen jobs:

```sh
python3 level_generation/ui/hud_inventory/queue.py batch-payload CELL_ID_1 CELL_ID_2 CELL_ID_3
```

Supply up to nine actual cell IDs, normally nine. The command currently supports small inventory cutouts
with the `item` profile, common namespace and dependency set, and no identity-seed dependency. Other asset
families keep their existing queue payload path; their future preparation uses up to nine small compatible
cells where applicable. Do not bypass the restrictions by relabeling a treatment.

The returned JSON contains a unique `batch_id`, original `jobs`, `selected_cells`, exact `tool_args` and
`execution_layout`. Native canvases are shown at 4× on a label-free magenta 3×3 reference. `cell_rects`
locates each complete native canvas; `slot_rects` locates its safe extraction slot. Empty slots stay empty.
Review the reference, then claim each listed source job using the ordinary `claim JOB --note ...` command
immediately before submitting ONE built-in imagegen call with the returned `tool_args`. Existing claims
must be resolved through their actual operation; never expire them by age.

```sh
python3 level_generation/ui/hud_inventory/queue.py record BATCH_ID --raw /actual/returned-master.png
```

Recording retains one raw master, exact prompt and references, records every source job in that attempt,
and releases those source-job claims. `next` recognizes retained attempts for every participating job.
Use the returned single attempt ID for ordinary per-cell `compare` / `accept`, followed by `reconstruct`
and `stage`. Unsubmitted siblings cannot be accepted using the batch attempt. Normal registration,
internal-landmark, dependency and full-canvas review requirements remain in force.

## Efficient extraction and review

Inspect the actual master before slicing. Scale the recorded rectangles by actual output/reference size;
imagegen may return 1254×1254 rather than the requested 1920×1920. Check that every object stayed inside its
slot. Preserve the complete native canvas at exactly twice its own dimensions, including margins. Use
the existing matte/unmixing and uniform registration path, with recorded parameters; no local warping,
native-mask substitution or blanket erosion to force a pass. If returned detail is insufficient, reduce
the batch; do not enlarge a tiny object just to pass dimensions.

Process all cells in one script invocation and make one combined original-x2/restored-x2 proof plus light/dark
edge previews. Inspect the whole raw master and every final cell. Use concise per-cell observations and
the existing automated checks; perform closer inspection where a visible defect or warning requires it.
Passing dimensions/alpha checks alone never establishes plausible internal geometry or restored detail.
Record failed cells with specific defects, then defer retries until the first pass is complete. Later retry
only those cells or their inseparable state group, grouped into compatible sheets.
Do not regenerate good siblings or run a game scenario per bitmap. Representative UI runtime reviews remain
the goal's final integration check.

The 3×3 pilot produced nine candidates in one call (~35 seconds), with ~6 seconds of processing; eight
passed footprint checks and one was flagged. This supports batching, not a guaranteed speedup or acceptance
rate. The two experiments remain candidates and must not be silently counted as staged restoration.

## Fitted armour: observed material transfer

`production/plate4_01/` and `production/plate5_01/` show copper/silver cuffs transferred to native all-gold arms across body types, including after an explicit no-transfer prompt. For subsequent fresh sheets and later repair groups, separate body types when their materials or construction differ; keep compatible arm-pose pairs together. Do not resubmit accepted or deferred siblings to fill a sheet. Same-material families may still share a sheet, but require independent geometry/material review (`production/mm7armour66_01/` shows that compatible materials alone do not ensure fidelity). Preserve frozen jobs and use explicit execution selections/layouts for any split.
