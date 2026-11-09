# MM6 Ooze (ooz) — 3D model, 2026-10-08

Ooze / Acidic Ooze / Corrosive Ooze (descriptors 589/590/591, palettes 780 green / 781 red / 782 ochre). Built with
the [quadruped/non-humanoid playbook](../CLAUDE_QUADRUPED_PLAYBOOK.md): Codex HD masters → Meshy Smart Topology →
own lump rig (no skeleton) → procedural clips → Meshy retexture → one shared skin with palette ramps.
Runtime: `assets_dev/worlds/mm6/models/mm6_ooz.glb` (3,704 tris incl. the hidden pod; LODs 1,780/640/210, 4.0 MB).
Meshy credits: 15 of 30 (Smart Topology 5, retexture 10).

## Pipeline

| Step | Script / output |
|---|---|
| HD masters | `references_hd/` (Codex, brief `CODEX_BRIEF.md`; inputs `native_views.png` + the native attack frame). Proportions from the native views: length ≈ 1.2 × width, height ≈ 1/5 of the length |
| Model | `meshy/smart_topology_v1` (6,632 tris, watertight, two droplets) → `scripts/load_ooz.py` (length 1.0 m along Y, floor z = 0) |
| Rig | `scripts/rig_ooz.py`: underside to 15 %, rest to 50 % (3,104 tris); pseudopod tube (456 tris); Root → Body → Lump_C + Lump_0..7 (heads on the floor, so bulges never lift or sink the underside) and PodRoot → Pod1..5; heat weights, droplets take their nearest vertex's weights |
| UVs + upload | `scripts/uv_export.py` (Smart UV on the blob; the pod has no texels of its own) |
| Clips | `scripts/anim_ooz.py` (world-space offset/scale/rotation per bone and frame, keyed with no action attached) |
| Textures | `scripts/blob_only.py` + `../claude_shared/bake_creature_ao.py` (AO without the pod), `scripts/compose_ooz.py`, `scripts/tier_ramps.py` |
| Runtime | `scripts/build_runtime.sh --install` (export maps the pod onto a single-island disc of the blob's top surface) |
| Regression | `mm6_ooz_actor_model_tiers_share_a_glossy_skin` (temple `6d07.blv`, summoned tiers) |

## Clips (native timing, 24 fps)

Standing 1.0 s pulse · Walking 0.75 s peristaltic wave (front to back, lumps push forward) · Running 0.5 s ·
Attack 0.75 s (native a–f, user review: pod shoots up to ~2.1× the blob height, bends forward (toward the party; the 2D front-view sprites draw
it sideways) into an inverted L,
arches over into a loop, angles up again, sinks back; per-segment keys `ATTACK_KEYS` in `anim_ooz.py`; pod 0.62 m,
6 segments, radius 9 → 7 cm, lumpy) ·
Cast 0.75 s (B/C Poison Spray / Toxic Cloud: the middle rears into a dome and contracts; glow at `Socket_Spit`) ·
Hit 0.75 s (lumps bubble in two waves) · Death 0.625 s (centre swells and bursts, collapses into a flat spread
residue) · Dead · Fidget 0.75 s (pulse with one bubble). Lowest vertex ≥ 0 in every clip except the Attack strike
(pod tip −1.1 cm).

## Material and tiers

- The one creature that keeps engine specular: wet slime, roughness 0.5 and `openyamm_specular` 0.7 (user review:
  less glossy; 0.32 / 1.0 washed the ochre tier to greyish beige), metallic 0.
- Crease/highlight shading (user review: more white-ish and black so it reads 3D): `scripts/dump_uv3d.py` measures
  the rest mesh's curvature per vertex; `compose_ooz.py` darkens concave creases toward black (0.8) and lifts convex,
  up-facing lump tops toward white (0.7). The ORM red channel is a per-texel specular mask
  (`openyamm_specular_mask`): no sheen in the creases, so they stay near-black instead of mirroring the sky. Tier
  ramps keep the sprites' near-white highlight entries (QMAX 0.995). Captures `review/ingame/cav2_cmp_out.png`,
  `cav2_cmp_in.png` (before / now / sprites).
- One region (the whole slime); ramps from native pixels aligned across 780/781/782 (`transfer_ramps`, top tenth of
  baked highlights excluded). In-game A/B against the sprites set albedo 0.9 (1.35 read ~1.5× too bright with the
  gloss) and chroma 1.4.

## Known limits

- The corpse is a flattened green puddle (native: dark scattered residue); a colour change needs a second material.
- Native shading transfer (`native_shading.json`, height mode; the sprites' camera is almost level) was tried at
  amount 0.6 (`OOZ_SHADE=0.6 scripts/build_runtime.sh`): in same-camera captures it only darkens the lump bases
  slightly, because the sprite's dark band is the bottom ~15 % and Meshy's texture plus AO already darken the lump
  bases. Off by default (captures `review/ingame/ab_outdoor.png`, `ab_indoor.png`).

## Cast = copy of Attack (2026-10-15)

User: "ooze - copy attack anim into cast anim". `../timing_review/copy_clip.py` on the installed source (newer than
`export/mm6_ooz.glb`: its normal map's green channel was corrected after export) -> `export/mm6_ooz_castcopy.glb`,
installed as `mm6_ooz.glb`. Only Cast changed (0.75 s, now equal to Attack). Previous source:
`work/mm6_ooz_source_pre_castcopy.glb`. The timing review's Cast impact follows Attack (0.394).

## Gloss restored (2026-10-30)

The 2026-10-16 material pass had flattened the reviewed slime (specular 1.0, flat mask 0.30, roughness 0.7).
`scripts/restore_gloss.py` puts back specular 0.7, the crease mask and roughness 0.5 on the installed GLB: LOD0's map from
the pass backup, the far LODs' maps re-derived per texel with `lod_repair_claude/scripts/transfer_textures.py` (a run on
the old map reproduced the installed far maps exactly). Only the three maps and the factors changed. `material_pass/revert.sh`
was not used: its backup predates the far-LOD repair. `scripts/make_gloss_viewer.py` builds the before/after viewer (tier
ramps baked, engine specular shown as `KHR_materials_specular`); comparison in `review/shots/cmp/compare.png`.
