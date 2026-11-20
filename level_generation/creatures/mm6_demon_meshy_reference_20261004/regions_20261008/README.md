# MM6 demon A/B/C as one shared skin — 2026-10-08

Migration to the shared-skin tier rule (`level_generation/creatures/CLAUDE_CREATURE_TEXTURES.md`).
`build_regions.py <installed mm6_demon.glb> <out.glb>` keeps A's body textures (base colour, normal, roughness).
It adds `demon_region_mask.png` (R = dark-grey skin, G = green harness; cream bone/padding unchanged) and
fits per-tier ramps (`demon_ramps.json`) to the former B/C Meshy body textures over the same texels.
The three body materials `Demon_Body_A/B/C` differ only in ramps. Irises stay separate variant materials.

- Result: B keeps green skin with an olive harness, C keeps red skin and harness. B/C lose their separate Meshy paint
  detail and their own normal/roughness maps (fit error vs. the old textures: mean 11–21 8-bit levels).
- GLB 42.9 → 22.9 MB; about 64 MiB less RGBA8 GPU memory.
- `previous_installed_mm6_demon.glb` is the installed GLB before this migration.
- In-game capture: `region_tiers_20261008.png` (Abandoned Temple hall; left C, middle B, right A).
- Checks: unit `*odel*` 53/53, `OPENYAMM_REGRESSION_FILTER=mm6_` actors 10/10.
- Body materials use `openyamm_specular 0` and metallic 0 (applied with `region_variants.py --extra`).
