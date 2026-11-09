# Decoration review browser

Open [index.html](index.html) in a browser. It works as a local file; no server or API is needed.
If the browser restricts local files, run `python3 -m http.server 8765 --bind 127.0.0.1` from the
repository root and open `http://127.0.0.1:8765/level_generation/decorations/browser/`.

## Flagged sprite changeset

Open [changeset.html](changeset.html) for the approved third review round. It shows 117 groups: 113 revisions
and four entries that now keep the current accepted art, as requested in the first review. The four animated groups
play while visible; the other 113 groups are static. Nine static items received isolated imagegen repairs after
the packed-sheet crop check, eight more received targeted isolated repairs in the second round, and four
packed-cell-edge candidates received isolated repairs in the third round. The four
animation groups use Real-ESRGAN candidates.
Scroll, expand, and change background to inspect the retained review evidence. **Copy review** still exports flags
for future revisits, but the user's approval is recorded separately in the
[installation plan](../../sprites/restoration_jobs/runs/remaining_review_20260923/approved-installation-plan.json).
The installed package contains all 2,531 approved name/palette PNG bindings; 2,520 original BMPs are archived under
`assets_dev/_legacy/sprites_original/`. Each review round used a fresh
local flag store, so older flags do not silently carry into the new export. Exact requests,
raw returns, candidates, and review-only manifests are retained in
[`round2/`](../../sprites/restoration_jobs/runs/remaining_review_20260923/round2/) and
[`round3/`](../../sprites/restoration_jobs/runs/remaining_review_20260923/round3/).

Rebuild the changeset after candidate changes with:

```sh
python3 level_generation/sprites/restoration_jobs/runs/remaining_review_20260923/build_changeset_catalog.py
```

## Remaining restored sprites

Open [remaining.html](remaining.html) to review the restored world items, effects/projectiles and interface overlays
that are not in the installed decoration pack. It uses the same side-by-side 2× canvases, automatic playback,
backgrounds, frame stepping and flags as the decoration page. Filter by category or search by name, ID or image.
Its flags are saved separately from the decoration page. The current catalog shows 611 groups and 1,822 timeline
frames, covering all 1,283 distinct exported non-decoration images. The other 34 registry groups have no restored
art to compare because the source image is missing or deliberately kept native.

The remaining browser is historical review evidence; its catalog compares against the pre-install accepted export.
No files are installed or moved by the browser itself. Refresh its catalog after export changes with:

```sh
python3 level_generation/decorations/browser/build_catalog.py --remaining
```

The catalog contains the 672 decoration groups with available native and accepted restored art.
Three registry groups (`outli1`–`outli3`) have no native image and cannot be displayed. The `noose`
group shows its available views and names its missing views on the card. The source is the current
`groups.json`, `sources.json` and `export.json` under `level_generation/sprites/restoration_jobs/`.
After restoration changes, refresh the ledger/export and run:

```sh
python3 level_generation/decorations/browser/build_catalog.py
```

Scroll normally. Visible animations play at their recorded frame durations; other views rotate
automatically. Select a view to inspect it manually, use the arrows to step frames, or expand a
card for a larger preview. Each pair uses the same maximum 2x native canvas; frames are centered
horizontally and aligned at the bottom, like a standing billboard. Mirrored views mirror both
panes. The native frame is enlarged with nearest-neighbor sampling, while the restored frame uses
its accepted 2x pixels.

Click one or more reason chips to flag a decoration, optionally add a note, and choose whether the
flag applies to the whole decoration, selected view, or current frame. The current-frame scope
pauses playback so the selected frame is stable. Flags save in this browser's local storage. Use
**Copy flags** to copy or download JSON and paste it into the chat for follow-up work. The JSON
includes stable sprite IDs and, when selected, exact view octants and frame asset IDs. No flag is
written to the restoration ledger or sent anywhere automatically.
