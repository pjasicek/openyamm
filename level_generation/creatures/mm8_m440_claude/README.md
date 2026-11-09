# MM8 Ogre Warrior — m440

Created with the shared Claude humanoid playbook for the request to preserve weight, attack anticipation and recovery and fit the motion to the club. Native source family `mm8:m440`; runtime sprite groups m441/m442/m443, merged monsters 31/32/33 (Ogre Brawler, Ogre Warrior, Ogre Warleader), descriptors Ogre Warrior A/B/C.

The source Ogre has a broad brown body, black iron helmet and cheek flanges, tusks, crossed studded straps, one front-left shoulder plate/ring/two spikes, chainmail at the back and a green cloth apron. All five digits on each hand and foot are present. The wooden club has its own textured rigid attachment. Green, blue and red cloth/wrist-wrap variants share geometry, skin, clips and materials.

## Motion and scale

| Role | Source / fit | Duration |
|---|---|---:|
| Standing | ArmedIdle; native crouch, broad stance, club ready | 2 s |
| Walking | Mixamo Orc Walk; original knee/ankle paths, low heavy steps, 1.654336 m stride | 1.2 s |
| Running | Mixamo Standard Run; source foot paths fitted to a 1.5 m stride, stable club carry | 0.733333 s |
| Attack | Mixamo Standing Melee Attack Downward; original anticipation and strike, fitted recovery | 1.366667 s |
| Hit | ArmedGetHitF1; fitted guard entry and recoil | 0.5 s |
| Death | ArmedDeath1; continuous entry from guard, grounded prone finish | 1.333333 s |
| Dead | Final Death pose held | 1 s |
| Fidget | ArmedIdleAlert1; planted stance and supported head turn | 2 s |

Attack impact is 26/30 s, measured from the club-head strike. The engine maps anticipation to the native one-second wind-up; the remaining 0.5 s follows through and returns to guard. Total runtime action is 1.5 s, fitting the fastest Ogre's 90-tick recovery (ticks / 60). Slower tiers retain their longer gameplay recovery. Attack2 uses the same fitted melee motion. No gameplay timing was changed.

The 164-pixel native standing body at SFT scale 1.399994 is 229.599016 game units. The fitted standing body measures 1.487885632 m, yielding scale 154.3122744375 for all three native tiers. The taller walking sprite bounds include the raised club, so they are not used to stretch the body. Head look is limited to 25° yaw / 15° pitch.

The source-frame humanoid rig has four axial helpers plus a Club joint (57 joints). The right fingers are fitted to the real handle surface; the left hand retains source motion. Curves are sampled at 60 Hz with quaternion sign continuity. Feet and wrists received a separate 48 Hz continuity review.

## Selected editable and delivery files

- `work/rig_uv_master.blend`: final fitted motion/geometry and frozen body/head UV layout before texture transfer.
- `work/rig_textured_uv.blend`: same fitted rig, transferred body and head UVs.
- `work/m440_textured_master.blend`: packed editable textured master with club and eight export clips.
- `export/mm8_m440_lod0.glb`: portable combined textured body/club, eight clips.
- `export/mm8_m440.glb`, `export/mm8_m440_club.glb`: runtime-ready body/attachment with variants and colour/shadow LODs.
- `textures/`: body, head, club base colour, normal and material masks; shared cloth region mask and native palette ramps.
- `review/viewer/`: existing shared review UI with three colour tiers, eight clips, native pose anchors and frame feedback.
- `references_native/`, `references_hd/`, `meshy/`: original source provenance, selected/rejected HD references and immutable paid returns. These are retained, not replaced by the fitted export.

Body/head maps merge into 2080×1024 atlases with a 32-pixel gutter. Club maps are 1024×1024 before the attachment crop. Runtime ORM uses R=specular mask, G=roughness, B=0. Measured Meshy normal maps are converted once to glTF +Y. Skin, eyes, ivory, iron, leather and cloth have separate masks. Skin grading preserves texture contrast; native PAL441/442/443 ramps recolour only cloth/wrist wraps.

Meshy omitted two body faces during retexture. The original geometry and rig are retained, with explicit shared-edge UV extrapolation on those two faces; see `work/texture_return_missing_faces.json`. All other corners match the return within 0.1 mm. The independently painted head return retains all 9,262 faces.

## LOD modelling exception

| Level | Body triangles | Club triangles | Total |
|---|---:|---:|---:|
| 0 | 18,752 | 1,387 | 20,139 |
| 1 | 10,649 | 1,059 | 11,708 |
| 2 | 6,400 | 899 | 7,299 |
| 3 | 4,238 | 793 | 5,031 |

Uniform 50% reductions opened the club grip and removed reliable sole contacts. The final LODs therefore preserve the 1,099-triangle right hand, both bare feet (999 triangles total) and 735-triangle wooden shaft. Armour, head, free hand and club iron still simplify. Shadow insets exclude these contact surfaces. This is an explicit engine-driven exception to the approximate half-per-level target; each chain strictly decreases and has an absolute triangle budget. The original failed run is retained in `review/decimated_contact_failures/`; it is not acceptance evidence.

## Reproduction

Use the owned creature workspace and its lease for all project writes. Start from the selected frozen master, not the intermediate experimental motion scripts. Texture jobs have already completed; do not resubmit them.

1. `scripts/transfer_textures.py` transfers UVs, writes UV membership rasters and bakes short-range AO.
2. `scripts/compose_textures.py` creates classified maps and native colour ramps; `scripts/preview_textures.py` previews them.
3. `scripts/export_runtime.py` writes the packed master and combined export.
4. Run `tools/prepare_actor_glb.py` to `export/mm8_m440_runtime_lod0.glb`, then Blender `scripts/build_lods.py`.
5. `scripts/finish_runtime.py` preserves contacts, insets shadow casters, applies variants, splits Club, then merges head/body materials.
6. `scripts/run_final_gates.py` checks the actual exported body and attachment; `scripts/viewer_tiers.py` bakes portable review colours.
7. `tools/install_model.py` installs each final GLB to the MM8 source scope and cooks its desktop runtime copy.

The old fitting scripts and intermediate blends are provenance, not a second active branch. Final motion is authoritative in `work/rig_uv_master.blend`. Original source clips stay in the ignored animation library, not in the runtime package.

## Verified delivery

[Interactive review: all three tiers and eight clips](http://127.0.0.1:8912/level_generation/creatures/mm8_m440_claude/review/viewer/).
Technical production and installation are complete. User artistic acceptance is deliberately separate and is not claimed.

- Final exported body, club and every colour/shadow LOD pass the shared gates; counts and hashes are in `delivery_receipt.json` and `review/final_gates/gates.json`.
- Ordinary desktop game and unit-test targets build. All 48 MM8 cases pass (4,321 assertions), including the new merged-ID/club binding and cooked motion/recovery checks. The broader ModelAnimation run passes 20/22; two unrelated MM6 demon cases have stale death/visibility and triangle-count expectations. Their complete log is preserved.
- Viewer: all 24 tier/clip combinations load without console errors. Normal and half-speed playback sequences, face/both-hand close views, wind-up, impact, recovery, gait, hit, fall, held corpse and fidget were inspected. The final cloth-mask/AO polish changes materials only.
- Real desktop OpenGL captures ran on the NVIDIA GPU via Wayland. Matching cameras compare all three native sprites with the installed models in New Sorpigal and Agar's Laboratory. Native debug-pose captures also cover all eight roles and five attack/recovery poses. These captures are visual checks, not performance measurements.
- Source and runtime installs are `assets_source/worlds/mm8/models/mm8_m440{,_club}.glb` and `assets_dev/worlds/mm8/models/mm8_m440{,_club}.glb`, with bindings in `assets_dev/worlds/mm8/models/actors.yml`. The installer cooks the desktop texture payloads. The private indoor preload fixture does not alter the production map.

| Location | Original sprites | Final 3D |
|---|---|---|
| New Sorpigal | [native](review/ingame/outdoor_sprite/party.png) | [model](review/ingame/outdoor_model/party.png) |
| Agar's Laboratory | [native](review/ingame/indoor_sprite/party.png) | [model](review/ingame/indoor_model/party.png) |

[Native raised-club anticipation](review/ingame/native_motion/raised_club.png), [impact](review/ingame/native_motion/impact.png), [recovery](review/ingame/native_motion/recovery.png), [ready again](review/ingame/native_motion/ready_again.png).

Body/head AO bakes park the other layout outside the active islands. Final reduced shadow insets are 6/12/20 mm with a 30 mm cap, excluding the retained hand, feet and club, to suppress the moving caster's surface artefacts. LOD3 is intended below roughly 80 projected pixels; forced close-up LOD captures are diagnostics, not its normal viewing distance.

Meshy consumed 50 credits of the 100-credit production budget. No jobs remain pending. Android, Vulkan and performance benchmarks were not run. No commit or staging operation was performed.
