# MM8 Ogre peasant — m436

Rigged, textured civilian Ogre made with the shared Claude humanoid workflow. The body stays broad and heavy, with a relaxed idle, deliberate weight shifts and a rolling walk. Empty hands, bare feet, ragged vest/shorts, shaggy ochre hair and the leather pack follow the native family. No weapon or combat-ready idle was added.

Native family `mm8:m436` uses sprite groups m437/m438/m439, palettes 437/438/439 and merged monster IDs 28/29/30. The descriptor names retain the original spelling, `Ogre Pesant Male A/B/C`. All three are named Ogre Peasant in gameplay.

## Review and deliverables

- [Interactive review](http://127.0.0.1:8912/level_generation/creatures/mm8_m436_claude/review/viewer/): three tiers, all seven clips, source references, frame scrubbing and feedback links.
- [Portable game model](export/mm8_m436.glb), [editable packed master](work/m436_textured_master.blend), [textures and palette ramps](textures/).
- [Normal/half-speed playback](review/playback/playback.json), [deformation gates](review/final_gates/gates.md), [UV validation](review/uv_validation.json), [completion receipt](review/completion.json).
- [Native indoor/outdoor captures](review/ingame/), [motion selection and original hashes](work/motion_selection.json).

User accepted the completed seven-clip civilian version (`m436_civilian_v3`, no attack animation) on 2026-10-18. The acceptance and selected artifact hashes are recorded in `creature_3d_progress.json`.

## Motion

| Clip | Seconds | Source and adaptation |
|---|---:|---|
| Standing | 2.0000 | RelaxIdle; broad planted stance, loose hands and breathing |
| Walking | 1.2000 | Mixamo Orc Walk; source foot travel fitted to the Ogre's actual leg lengths |
| Running | 0.8333 | Mixamo Running (5), Standard Run; heavy forward lean, source foot paths |
| Hit | 0.5000 | UnarmedGetHitF1; brief flinch with relaxed entry and exit |
| Death | 1.3000 | UnarmedDeath1; weighted backward fall, legs and arms settle around the pack |
| Dead | 1.0000 | Exact held final Death pose |
| Fidget | 0.6667 | RelaxYes; small nod and weight shift |

The Ogre Warrior m440 was the weight/momentum benchmark. The peasant uses civilian hands and posture. All three native tiers use **Wimp** AI: they flee instead of fighting. The dedicated shove was removed at the user's request, along with both attack bindings and impact markers. The existing runtime accepts omitted attack roles for Wimps. There is no Attack or Cast clip.

Native attack sprite slots alias walking; unused throwing artwork is not a gameplay projectile attack. Hit fits its native 0.625-second action. Gameplay movement speed 140, AI, combat values and original sprite timings are unchanged. These are fitted library motions, not frame-exact sprite reconstructions.

## Production notes

The selected full body used Meshy T2 Smart Topology. A separately generated head replaced the too-fine initial face with an annular neck join. The fitted source-frame rig preserves local hand frames and five digit chains per hand. Anatomical arm weights remove the automatic rig's hip influence at the elbows. Pack components follow the chest; vest collar and lower hair share the neck appropriately. Four twist bones distribute forearm/upper-arm roll; palm and eye sockets are included.

LOD0 has 14,488 authored triangles; lower levels have 7,174, 3,311 and 1,272. A first 12k reduction was rejected because the torso and limbs lost too much volume. The standard cooker can add visible back-face triangles; the authored colour/shadow levels remain in the source. Shadow reduction preserves hands/feet and tucks other reduced surfaces inward.

The body was textured with new Meshy UVs; the head retained its uploaded UVs. Matching returned face corners differ by less than 0.001 mm. Three omitted body triangles use local projections from their adjacent returned surfaces; one omitted hair triangle keeps its uploaded chart. Three body and eighteen head UV patches were translated with their maps, without rotating normal tangents. Final UVs have no overlap, degeneracy or out-of-bounds faces. The animation and geometry remain in the original fitted master.

One 1K body set and one 1K head set merge into a 2080×1024 runtime atlas. Native palette ramps recolour only the vest/shorts: green, blue and red. Skin, hair, leather and brass retain their identity. Skin/leather/cloth are nonmetallic; the buckle is brass. Normals are converted once to glTF +Y, with per-surface roughness and specular masks. Broad skin colour is balanced between the body/head sets while preserving fine texture.

The native standing silhouette is 163 pixels at scale 1.399994, or 228.199022 game units. The measured standing model height gives scale 133.257758. Stride lengths are measured from stance-foot travel, not guessed from the clip names. The corpse rests against the bulky pack with bent knees and lowered arms.

Reproduction follows the project scripts: fitted motion → `settle_arms.py` (reduce and fit recovery) → `export_uploads.py` → recorded Meshy retexture jobs → `sync_motion.py`, `transfer_textures.py`, `diagnose_uv.py`, `repair_uv.py` → `translate_maps.py`, `compose_textures.py` → `build_delivery.py`. The final `export_runtime.py` selection excludes Attack; `remove_unused_attack.py` also removes it from the selected editable masters. Earlier motion checkpoints and attack studies are historical. Service downloads and failed/superseded candidates are retained; do not resubmit them. Meshy consumed 45 credits, including the superseded 10-credit body texture attempt.

## Verification

The current seven-clip export passes 5,210 deformation checks, 21 tier/clip browser combinations and two focused regression cases (109 assertions). A fresh native outdoor run loads and displays all three tiers without combat bindings; see [captures and log](review/ingame/civilian_correction/).

[Preservation checks](review/civilian_correction.json) verify that all retained motion, geometry, materials, skeleton and LOD data match the previous revision. Its normal/half-speed playback, independent Blender skinning comparison (less than 0.001 mm), 16 gate-runner regressions, 53 MM8 tests and indoor/outdoor model/sprite comparisons remain historical evidence for that unchanged content. The old Attack recordings and poses are superseded. [completion.json](review/completion.json) records current hashes and the distinction between fresh and preserved checks. Production map actors are unchanged.

Android, Vulkan and performance benchmarking were not run.
