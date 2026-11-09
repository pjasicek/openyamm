# MM8 Dark Elf Warrior — complete native restoration

Open [the complete offline viewer](complete/viewer.html). The delivery contains all **160 native frames**:
5 standing, 40 walking, 40 attacking, 25 hit/recovery, 25 fidget, 20 collapse and 5 corpse poses.
All five stored directions and the original three mirrored directions are retained. The second attack action
reuses the original attack frames. Death retains its native two hit poses followed by four collapse poses.
Unused stored poses remain available without inventing playback bindings.

The three native appearances use palettes **433, 434 and 435**. Base artwork is shared; blue/pink sleeves and
the corresponding disk colors are deterministic enhanced-art mask variants. Skin, silver hair, black armor,
gold fittings, gloves and sword are protected. No originals or gameplay assets are overwritten or installed.

- [Placement/animation manifest](manifest.json), [validation](validation.json), [review acceptance](review/acceptance.json).
- [Five RGBA8 atlas pages and matching R8 masks](complete/atlas/), exported at 2× native logical resolution.
- [Aligned masters](complete/runtime_aligned_2x/), [480 palette previews](complete/previews/),
  [native/base/variant/mask contacts](complete/review/combined/).
- [Exact selected frame provenance](complete/selection.json), [generation history](sequence_restore/generation_history.json),
  [compact job ledger](sequence_restore/jobs.json), [processing/resume instructions](sequence_restore/README.md).

The decoded atlas cost is **96,835,840 bytes** (92.35 MiB): 77,468,672 RGBA8 base bytes plus 19,367,168 R8 mask
bytes, including atlas padding. Stored masters retain a 256×256 logical canvas with native bottom-center
anchoring and a 576×576 padded 2× working canvas. Actual selected generated detail is at least 2.448 pixels
per native pixel after registration; the compact front-attack sheets already exceed 2× before registration.
The native per-step scale, timing, mirror flags and anchors are retained in the manifest.

Checks cover all 160 frames and 480 variants, exact atlas/crop reconstruction, identical mask placement,
alpha preservation, source hashes, base bypass and contour spill. The actual offline viewer passed 192
actor/action/view tracks and 1,008 timing boundary samples. Native sequence contacts and palette overlays
were visually reviewed, including light/dark contour patches and mirrored playback samples.

The earlier [front-attack alignment trial](front_attack_grid_trial/viewer.html) is preserved as historical
review evidence. The complete delivery fixes its first two head directions, foreshortened fifth sword pose,
and positional color-transfer artifacts. Planted front-attack soles match the native baseline exactly;
stance centers differ by at most 0.5 physical pixel. Walking and hit poses retain native moving contacts.
The rear prone poses use a recorded heel contact region so the dropped sword cannot lift the body.

`detail_upgrade/` and the older root processing outputs are retained history. Their pending jobs have been
superseded by the selected compact sequence restoration; do not resume those queues to rebuild this family.
The enhanced art interprets fine surface detail rather than reproducing the old pixels exactly. Native pose,
appearance and motion were the review authority. Renderer installation remains separate work.
