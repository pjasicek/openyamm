# MM8 Ogre Mage (`m540`)

Rigged and textured Ogre Mage for the shared Claude production workflow. This uses the completed
[MM6 Ogre](../mm6_ogr_claude/README.md) source-frame rig and heavy locomotion, plus the
[MM6 Djinn](../mm6_djn_claude/README.md) casting, hand-fitting and release-socket methods.
The Mage has its own fitted anatomy, high collar, cape and short skull/orb wand. There is no MM8 Ogre Warrior prerequisite.

[Interactive review](http://127.0.0.1:8912/level_generation/creatures/mm8_m540_claude/review/viewer/)
provides all three palettes, nine named clips and native reference anchors.
[Outdoor comparison](review/ingame/lod_tour/lod0.png), [original sprites](review/ingame/outdoor_sprite/party.png),
[indoor models](review/ingame/fixture_in_3d/party.png), [indoor sprites](review/ingame/fixture_in_sprite/party.png),
and [face detail](review/shots/final-face.png) show the selected revision.

## Selected delivery

- Editable packed master: [export/mm8_m540.blend](export/mm8_m540.blend).
- Portable animated body and wand together: [export/mm8_m540_lod0.glb](export/mm8_m540_lod0.glb).
- Runtime body: [export/mm8_m540.glb](export/mm8_m540.glb); rigid [wand](export/mm8_m540_wand.glb).
- Installed sources: `assets_source/worlds/mm8/models/mm8_m540{,_wand}.glb` from the repository root;
  desktop-cooked copies and textures under `assets_dev/worlds/mm8/models/`.
- Bindings: the Ogre Mage A/B/C entries in `assets_dev/worlds/mm8/models/actors.yml`;
  exact family copy in [export/bindings.yml](export/bindings.yml).
- Canonical state, budget and provenance: [creature_3d_progress.json](creature_3d_progress.json).
  Five successful Meshy jobs consumed **65 of 100 credits**; no pending paid jobs.

Descriptors **106 / 107 / 108** share one body, one wand and shared textures. Native palettes
**541 green / 542 ochre / 543 crimson** recolour only the garment region. Brown skin, hair, bone and metal remain shared.
The five-digit hands, tusk detail and hidden anatomy are reconstructions, not recovered original geometry.
Native sources, mirrors, timing and hashes are retained in `native_inventory.json` and `native/`.
The HD body and head generation ledgers retain prompts and selected image hashes.

## Animation and runtime contract

| Role | Seconds | Source and treatment |
| --- | ---: | --- |
| Standing | 2.000 | Local relaxed idle, fitted ready pose |
| Walking | 0.800 | Completed MM6 Ogre motion, fitted Mage joints |
| Running | 0.833333 | Completed MM6 Ogre motion, corrected loin and collar clearance |
| Attack | 1.533333 | Local ArmedCastRAttack1 with native waist charge, left-hand guidance and wand release |
| Cast | 1.533333 | Identical native attack motion, separate engine-required role |
| Hit | 0.500 | Ogre recoil adapted to the Mage ready pose |
| Death | 1.300 | Backward Ogre fall, spread arms and grounded folded cape |
| Dead | 1.000 | Held final Death pose |
| Fidget | 1.500 | Authored wand inspection |

Nine role names represent **eight unique motions**. Native attack and attack2 use the same nine-frame sequence;
this is a smooth adapted animation set, not a frame-for-frame reconstruction. Gameplay tables are unchanged.
Impact is at **1.10 s**; both attack and spell release use `Socket_WandOrb` on the rigid `Wand` bone.
The existing runtime supplies spell-specific charge/release effects. Walking/running strides are 1.390/2.626 metres.
The 1.734734 m upright model is scaled by 151.7228968 to match the native **263.198872-unit** visible standing height.

There are 62 source-frame, twist, cloth, prop and socket bones, with at most eight normalized skin influences.
Optional runtime gaze is omitted: even a small extra yaw collided with this high collar during Running.
Authored head motion remains present and tested.

## Geometry and textures

| Detail | Body triangles | Wand triangles | Total |
| --- | ---: | ---: | ---: |
| LOD0 | 13,068 | 1,499 | 14,567 |
| LOD1 | 8,679 | 748 | 9,427 |
| LOD2 | 5,833 | 374 | 6,207 |
| LOD3 | 3,420 | 201 | 3,621 |

Body and head share one draw per LOD after atlas merging; the wand is a static attachment with its own LODs.
The head's disconnected fine surfaces collapsed under ordinary edge decimation. Bounded spatial reduction
retains its facial silhouette, with maximum vertex displacement 3.1/6.8/16.9 mm across the lower LODs.
This deliberate fidelity deviation keeps approximately 58–66% of the previous level rather than the usual 50%.
All four levels were forced at close range in the native renderer to inspect silhouette and material continuity.

Body/head textures originate as separate 1K sets, merged with padding into **2080×1024** runtime atlases.
The wand uses 512-pixel maps. The head was baked to a clean atlas from its detailed source without changing weights
or geometry. The joined neck's measured colour difference is 2.183/255. Native palette ramps and a padded region
mask supply all tiers. Current runtime MR red is `openyamm_specular_mask`, green roughness and blue metallic;
normal orientation is verified and skin has no metallic response.

## Verification and limits

The ordinary desktop target builds. The focused Ogre Mage regression checks native scale, three variants sharing
one asset, role names/durations, LODs, wand attachment, unchanged simulation state and each tier's Spell1 release
within 0.5 world units of the wand orb. The existing MM6 Djinn casting regression also passes.
The focused test uses the existing eager-descriptor API so unrelated in-progress creature assets are not loaded.

The viewer checked all 27 tier/clip combinations without failures or console errors. All nine roles were played
and recorded at normal and half speed; the agent inspected sampled temporal frames, close-ups and native captures.
The recordings are retained in `review/playback/`. This records the actual review method, not a claim of continuous
human video review. Export/reimport comparison across 83 sampled poses measured at most **0.055244 mm** surface error.
Static validation checks finite data, indices, normalized weights, four decreasing LODs, palette variants, a static
wand and installed-source identity. Current hashes are in `work/static_audit.json` and `review/ingame/captures.json`.

Half-frame contact checks cover arms, hands, wand, cloth and high collar. Grounding the corpse leaves a concealed
cape/skin contact of up to 4.08 mm late in Death (frame 35) and 0.24 mm in Dead; the visible corpse rests on its
folded clothing. These are recorded in `review/settled_contacts.json`, not reported as zero penetration.

Native GPU captures use the normal OpenGL 3.3 renderer on NVIDIA through SDL Wayland, including same-camera
outdoor (`oute3.odm`) and indoor (`6d19.blv`) model/sprite comparisons. The indoor fixture declares the three sprite
families for preload; its copied scene and hashes are recorded in `review/ingame/indoor_fixture.json`.
Native death plays through the grounded pose and then uses the shared loot-satchel presentation.
Production map content is unchanged. Run receipts, capture hashes and the binary hash are retained with the captures.

User artistic acceptance remains separate and has not been supplied. Android, Vulkan and the full unrelated actor
suite were not checked. No commit was made.

## Reproduction

Claim this project with `tools/creature_workspace.py` before writing. Use the shared guarded Blender and review wrappers.
The selected production checkpoint is `work/rig_uv.blend`; `scripts/refresh_role_package.py` exports its packed master,
rebuilds viewer models, verifies export parity, builds LODs and finishes the runtime package.
`scripts/build_lods.py` uses the shared body decimator then `reduce_head_lods.py` for the face.
`finish_runtime.py` applies shared palette ramps, splits the wand and merges head materials.
Install both final GLBs with `tools/install_model.py --world mm8`, then run `scripts/static_audit.py`.
Do not rerun historical fitting, UV-transfer or grounding experiments over the selected checkpoint.
