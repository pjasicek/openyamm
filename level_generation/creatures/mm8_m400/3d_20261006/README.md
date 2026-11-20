> Current selected continuation: [2026-10-15 Peasant A delivery](claude_20261015/README.md), now installed in MM8.
> The record below describes the historical 2026-10-06 asset-only delivery.

# MM8 lizardman villager A

Selected creature: `mm8:m400`, native descriptor 1, palette 401, **Lizardmen Male (Peasant) A**.
This completes FULL 3D asset production. Runtime installation and game-unit scale calibration are separate.

## Deliverables

- `delivery/mm8_lizardman_villager_a.blend`: editable metre-space rig, packed textures and six production NLA clips.
- `delivery/mm8_lizardman_villager_a.glb`: portable GLB with embedded PNG PBR maps, the same clips and OpenYAMM colour/shadow LOD metadata.
- `delivery/mm8_lizardman_villager_a_lod0.glb`: the same portable full-detail asset without LOD metadata.
- `delivery/clips.json`: native semantic bindings, timings, provenance and endpoint rules.
- `delivery/components.json`: anatomy/outfit inventory, variant and effects scope.
- `material_review_v1/`: neutral appearance, extreme-pose, detail and UV checker renders.
- `review/`: all-sample front/profile contacts and native comparisons in all five genuine views.
- `final_playback_v2/`: actual normal/quarter-speed playback captures and measured clip times from the shared viewer.

The selected body has 15,287 triangles, 40 skin joints and one opaque, double-sided material. Lower colour levels
have 11,456 / 9,160 / 7,631 triangles; each has corresponding shared-rig shadow geometry. Review levels at their intended
projected sizes: the renderer's colour thresholds are 500 / 200 / 80 pixels, with hysteresis. This is an asset check,
not an in-game performance measurement. Conservative 75% / 60% / 50% reductions preserve the dense original
UV charts; the more aggressive candidates degraded fins, fingers and pigmentation and were rejected.
The shared LOD helper now joins geometric UV seams before reduction and caps/normalizes the combined
weights to the runtime limit of eight. Its closed-surface and influence regression passes.

## Motion contract

| Clip | Seconds | Playback / native role |
| --- | ---: | --- |
| Standing | 0.125 | Held ready pose; `m401s` |
| Walk | 0.875 | In-place loop; `m401w` |
| Hit | 0.500 | Once; backward head/torso recoil; `m401n` |
| Fidget | 0.500 | Once; right hand to muzzle, then recovery; `m401f` |
| Death | 0.750 | Once; backward fall, knees raised, ground settle; `m401d` |
| Corpse | 0.125 | Held remains, exactly matching Death's endpoint; `m401x` |

Both native attack slots alias `m401w`. Bind `attack_melee` and `attack_ranged` to **Walk played once**; this preserves
the original descriptor. No invented strike, cast or native running action is delivered. Walk adapts Meshy's
walking preset and retimes it to the native duration; its individual poses are not reconstructed bitmap frames.
Standing and Corpse remain held. Source-derived action choreography is a continuous 3D interpretation, not a claim
of identical projected poses across the original artist's directional drawings.

The GLB faces +Z with +Y up. Blender uses +Z up and -Y forward. Authoring height is 1.7 m; object scales are one.
The stable object root is `Lizardman_Rig`; pelvis `Hips`, upper-body subtree `Spine02`. Six production actions are
baked at 48 fps. The retained `Meshy_Walk_Source` action is authoring evidence, excluded from delivery clips.
No authoring constraints or simulations are required by the export. Source actions can interrupt into other
states; outgoing blends remain the caller's responsibility. Death's deliberate local backward displacement is
retained in Corpse. Reset to the selected clip on state changes; no visibility, particle or disappearance track is needed.

## Appearance and scope

Deep teal-blue scales, yellow eyes, ivory claws/teeth, paired tan-webbed head fins, green gold-edged tunic and split
skirt, checkered red/green apron, brown belt, three gold bands on each upper arm and ivory neck/arm/calf ornaments are retained.
Three forward toes are observed. Four hand digits (three fingers and a thumb) are an explicit anatomy inference
where the native views occlude the exact count. Eight two-segment digit controls were added to Meshy's 24-joint rig.
The creature is unarmed and has no observed tail. There is no missing weapon task. Only variant A is requested;
B/C are not generated. Cloth and ornaments follow their corrected anatomical owners; no cloth simulation is claimed.

Four appearance references and the revised primary image constrain the model. Original Meshy downloads remain
immutable in `../meshy/`. Final 2K maps are in `textures/`, packed in Blender and embedded in GLB. Metallic bleed is
removed outside gold; blue skin is nonmetallic with a roughness floor. The rest upload preserves the final UV set:
zero degenerate UV triangles, 49.15% triangle area, and zero overlap at a 512² texel-centre sample. Checker renders
and material/extreme-pose views were reviewed. Service normalization and vertex reordering are explicitly measured;
maps are applied to the retained animated master, never replacing it with the static return.

## Validation and resume

`export_validation.json` records actual exported surface parity across every clip, fractional poses, PNG inputs
and unchanged level-zero/animation accessors through LOD construction. `consumer_check.txt` records OpenYAMM's
real loader and deformation checks at 193 samples per clip at all four colour LODs. `final_playback_v2/playback.json` records normal and
quarter-speed playback, loops and endpoints in front/profile views. Contacts are separate evidence from playback.
User artistic acceptance is **not recorded**; production and agent review are complete.

Canonical resume state is `creature_3d_progress.json`. Meshy usage is **60 / 100 credits**: rejected first body 15,
selected revised body 30, automatic rig 5, final retexture 10. The first body succeeded as a service job and was
rejected during visual review; it was not a refunded/failed job. No repeat paid submissions are needed.

Reproduction uses the existing family lease and isolated wrappers: `author_complete.py`, `finish_materials.py`,
`verify_export.py`, `review_lods.py`, then `review_playback.py`. Acquire a fresh lease before authoring; do not reuse
a released token. `author_pilots.py` supplies the shared pilot construction, and exact requests/hashes are retained
in canonical state. The shared goblin viewer is reused read-only through an isolated local server; its files are
not modified. Runtime mounts and the prior validated 2D restoration remain unchanged.

The older shared demon asset-fixture check differs at four sockets added to that installed demon.
Those assets were not modified; the self-contained seam/weight regression and this creature’s export/loader checks pass.
