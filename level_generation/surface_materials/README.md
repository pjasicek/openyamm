# Surface material maps of MM6–MM8 face textures

Height and material class maps for every BLV and outdoor BModel face texture with an accepted 4× master, so the
renderer can draw relief, roughness, metal, glass and glowing windows (design and runtime:
[surface materials plan](../../devdocs/SURFACE_MATERIALS_PLAN.md)). Same scope as the
[surface texture playbook](../textures_x4/PLAYBOOK.md): no terrain, decorations, sky or liquids.

Claude orchestrates with [`mat.py`](mat.py); Codex only generates images through `codex exec` workers.

## Per texture

1. **Two Codex calls on the accepted master** (`assets_source/worlds/<w>/textures_x4/<name>.png`):
   - a height map, prompted as a renderer's depth pass (white raised, black recessed, no light);
   - a material class map in the flat key colours of [`tools/cook/surface_materials.yml`](../../tools/cook/surface_materials.yml).

   References keep the master's own aspect up to 2:1 (imagegen returns such aspects exactly, measured 887×1774 for a
   1:2 master); narrower trims stack copies, and the copies are averaged (height) or voted (classes).
2. **`process`** aligns and checks the returns and writes the candidates and `review/sheet.png`:
   - height: resized to the master, averaged over copies, made seamless on the axes the texture repeats (inventory
     `wrap`), flagged when misaligned (> 1 % by phase correlation of edges) or when it follows the master's
     brightness (correlation > 0.8: it traced the colours, not the shape);
   - classes: every texel snapped to its nearest key, voted across copies, edges moved onto the master's edges (a
     guided filter per class), specks merged; flagged when more than 4 % was far from every key;
   - family: where the master shares exact pixels with an already accepted relative (wall pieces cut from one
     painted canvas, inventory `relatives`), the relative's maps are copied in and the generated height eased into
     them, so joints between pieces match.

   The sheet shows master, height, classes and two lit renders (grazing light from the upper left and from the
   right). Judge the renders: relief that reads as the depicted shape, no inverted bumps, metal and glass where they
   are painted.
3. **`accept JOB`** installs every unflagged candidate (name them to accept flagged ones) into
   `assets_source/worlds/<w>/surface_materials/` (`<name>_h.png` 16-bit, `<name>_m.png`, and the wrap axes in
   `textures.yml`), together with the texture's exact duplicates. Families are matched again at this point.
   `retry JOB NAME --kind height|classes --note "..."` queues another attempt of one map.
4. **Cook**: `tools/cook_surface_textures.py` (the build target `openyamm_cook_surface_textures`) runs
   `tools/surface_materials.py cook` after the colour textures: normal and detail maps, BC7, into
   `assets_dev/worlds/<w>/surface_materials_x4/`.

Review overrides go into `textures.yml` per texture: `depth` (world units of the black-to-white range; default the
texel-weighted depth of its classes) and `painted_shading` (0–1; weakens relief and occlusion where the master
already paints its relief with shading).

## The loop

```sh
cd level_generation/surface_materials
python3 mat.py status
python3 mat.py next --world mm6 --map oute3.odm      # up to 24 textures, largest wall area first
python3 mat.py gen --world mm6 --parallel 10
python3 mat.py process <job>                         # read jobs/<job>/review/sheet.png
python3 mat.py accept <job>
python3 ../../tools/cook_surface_textures.py         # or build openyamm
```

`tools/surface_materials.py preview mm6/thlgdr out.png` renders one installed texture's maps for a closer look.
Fixes after installing: `next --world mm6 --redo --names a,b` claims installed textures again for new maps;
`relabel mm6/<name> <class> <class>` turns one class of an installed map into another.

Check every texture with glass or the glowing class by night before moving on: stained-glass pictures must be glass
throughout and tinted glass must not be the glowing class (it glows by day). A refused generation (the image safety
filter, e.g. a nude relief) passes with a note that describes the carving as architecture.

## State

| Path | Content |
| --- | --- |
| `ledger.jsonl` | `claim`, `accept`, `release` events; a texture's status is their fold (installed maps count as accepted). |
| `jobs/<id>/` | `job.json` (textures, attempt versions, notes), `refs/`, `raw/` (unchanged returns and worker logs), `candidates/`, `results.json` (checks, family copies), `review/sheet.png`. |
