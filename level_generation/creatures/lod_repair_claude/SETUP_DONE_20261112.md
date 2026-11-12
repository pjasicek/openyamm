# LOD repair setup done (2026-11-12, lod-step1)

Part A of step 1 of the LOD plan works end to end (scratch run `work/scratch_m158/mm7_m158/`, Bat, not installed:
build, strip, unwrap, UV-correspondence transfer, apply, culled audit for all four ladder steps; `verify_far_only.py`
OK on each step).

- **Venv** (durable, git-ignored by `level_generation/.gitignore` `*venv/`):
  `/home/pjasicek/github/OpenYAMM/level_generation/creatures/lod_repair_claude/venv` (Python 3.14.4, pymeshlab
  2025.7.post1, xatlas 0.0.11, numpy 2.5.4, scipy 1.18.1, Pillow 13.0.0). Setup:
  `python3 -m venv level_generation/creatures/lod_repair_claude/venv && level_generation/creatures/lod_repair_claude/venv/bin/pip install pymeshlab xatlas numpy scipy pillow`
- **Source option**: `repair.py [--source installed|original|<glb>] <stem>...`. Default `installed` = the current
  `assets_source/worlds/<w>/models/<stem>.glb`; `original` = the old `originals/` behaviour (stale, do not use);
  a `.glb` path for one stem. The source is copied to `work/<run>/<stem>/installed.glb`, its sha256 goes in
  `result.json`.
- **Strip old far materials**: automatic. `build_lods.py` now calls `strip_lod_materials.strip_unused_lod_materials()`
  after replacing the far meshes: the old `<material>_LOD<N>` copies (no longer referenced) and the textures/images
  only they used are dropped, so `apply_bake.py` accepts reruns on installed GLBs. Log line:
  `STRIPPED old far materials: ...`. Standalone: `scripts/strip_lod_materials.py <in.glb> <out.glb>`.
- **Check**: `scripts/verify_far_only.py <work/<run>/<stem>/installed.glb> <work/<run>/<stem>/<step>.glb>` must print
  `OK: only the far levels differ` (nodes, skins, clips byte for byte; LOD0/LOD1/shadow/effect meshes and LOD0
  materials with images resolved; each `_LOD<N>` copy's ramps and properties equal its LOD0 material's).

Example (one process per stem, at most 2 per agent at a time):

```sh
cd /home/pjasicek/github/OpenYAMM/level_generation/creatures/lod_repair_claude
LOD_REPAIR_PYTHON=$PWD/venv/bin/python LOD_REPAIR_RUN=<run> LOD_RENDER_CULL=1 \
  venv/bin/python scripts/repair.py mm8_m572      # -> work/<run>/mm8_m572/result.json, <step>.glb, <step>.built.glb
venv/bin/python scripts/verify_far_only.py work/<run>/mm8_m572/installed.glb work/<run>/mm8_m572/<step>.glb
```

Bat note for lod-step1b: the scratch ladder on the installed Bat missed the gate at every step (LOD2 outline / colour
30.3/21.7, 26.2/20.8, 22.7/18.4, 20.2/17.2; LOD3 29.7/15.3, 24.2/13.0, 28.5/12.7, 18.4/7.6; installed LOD1 8.6/17.6),
so the wing bones need more than the ladder. Scratch results stay in `work/scratch_m158/` for reuse.

**Leases**: `creature_workspace.py claim` refuses sub-folders and allows one lease per project folder (overlapping
folders count), so `lod_repair_claude/` cannot hold several. Claim with the model's own top-level project, e.g.
`--project level_generation/creatures/<stem>_texpass_claude --identity mm8:m572` (its `creature_3d_progress.json` must
name the same identity), and back up to `<project>/work/before_lodrepair/`. lod-step1 holds `mm6:gua`, `mm6:pfem`,
`mm6:thf`, `mm6:mer1` through their `mm6_<id>_rebuild_claude` projects; `mm7:m158` is released.

**Skirts with a dark lining** (added after the pfem install): if a far LOD's hem turns dark or streaked (lining joined at
the hem by a rim), rerun that model with `LOD_LINING_FIX=1` in the environment (opt-in; README "MM6 rebuilds' far
LODs"). The default path is unchanged.
