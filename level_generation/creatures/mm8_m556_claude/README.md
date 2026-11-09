# MM8 Wasp Warrior · m556

Complete Claude-playbook production: six-limbed armoured flyer, paired veined wings, articulated antennae,
segmented abdomen, left-hand sword and right-hand buckler. Technical delivery is complete; user artistic acceptance
is not recorded.

[Interactive review](http://127.0.0.1:8912/level_generation/creatures/mm8_m556_claude/review/viewer/)
· [Editable packed master](export/mm8_m556.blend) · [Portable assembled GLB](export/mm8_m556_portable.glb)
· [Native motion study](MOTION_STUDY.md) · [Generation receipts and progress](creature_3d_progress.json)

## Sword and slash revision · m556_slash_v2

The requested correction replaces the narrow sword with a broader tapered blade, distinct bevels and fuller,
swept guard, wrapped grip and tier-coloured fittings. Body and shield LOD0 geometry/UVs are preserved.
Attack winds up on the Wasp's anatomical left, cuts forward across and down, then follows through on its right.
The thorax turns through about 68°, leans into the cut and translates forward; the head counters, abdomen lags
and shield moves aside. The wrist keeps the cutting edge leading. Impact remains at 0.875 s, recovery ends at 1.25 s.
The other six animation channels are byte-identical to the previous export.

The [192 Hz path check](review/slash_path.json) samples 241 poses: 96% transverse motion, 93% cutting-edge alignment,
no detected blade/body or blade/shield intersection during the cut (gripping hand/forearm excluded).
[Recorded slash frames](review/slash_recorded.png) · [Normal-speed video](review/playback/Attack-1.webm)
· [Half-speed video](review/playback/Attack-0.5.webm). The interactive viewer opens Attack.

New native captures cover [outdoor attack](review/ingame/slash_v2/outdoor_attack/attack_08.png),
[indoor attack](review/ingame/slash_v2/indoor_attack/attack_08.png), all tiers and forced LODs in both scenes.
[Revision run records](review/ingame/slash_v2/runs.json). The focused Wasp regression passes.
The new sword made the default far reduction remove the shield centre; equipment now keeps 12% at LOD3
instead of the body's 6%, with blade/disk vertices protected from collapse. All LOD/shadow normals are finite and normalized.

## Source and construction

Native monster descriptors **118/119/120**, Wasp Warrior A/B/C, use aliases m557/m558/m559 and m556 frame art.
Their green/violet/crimson accent palettes are 557/558/559; the gold/black body and amber wings stay shared.
Five generated body views clarify the original sprites; no native sprite was submitted to Meshy.
Three claw digits behind the obscured equipment grips are reconstruction choices, not recovered hidden anatomy.

Meshy Smart Topology supplied the body, followed by a four-view retexture of the corrected local UV mesh.
The unsupported thorax spur was compressed, disconnected middle leg sections rejoined, and thick scalloped wings
replaced with thin closed leaf membranes. The simple sword and buckler were modelled locally from the native views.
A **48-bone** local insect rig articulates all six limbs, neck/head, abdomen, mandibles, antennae and both wings.
Weights use at most two influences at LOD0, four after reduction. No humanoid auto-rig or paid animation was needed.
Meshy consumed **15 of 100 credits**: geometry 5, retexture 10; both jobs completed and their originals are retained.

| Component | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| Body | 9,635 | 4,816 | 1,734 | 575 |
| Sword | 1,734 | 828 | 326 | 300 |
| Shield | 1,488 | 782 | 248 | 182 |

The runtime reducer uses stronger far reductions than the general 50% guideline. Reduced shadow meshes are inset,
with thin wings and rigid equipment excluded from shrinking. Far LODs intentionally simplify fingers, antennae,
facial detail and the round shield; forced close views are retained for inspection.

The body uses a 2K base colour and 1K normal/material/region maps, plus a 128px equipment atlas. All tiers share maps
and palette ramps. MR.R is the runtime specular mask, G roughness, B metallic; mild AO is baked into base colour.
Normal maps were converted once to the glTF convention. Unsupported KHR specular data is removed from runtime files.
The viewer bakes the same ramps into review copies; these are not installed as duplicate tier textures.
The original delivery included a grey-metal shield-centre correction. The later sword/slash revision above
preserves the shield at LOD0 and rebuilds its reduced meshes with the equipment.

## Motion and game binding

| Clip | Seconds | Behaviour |
|---|---:|---|
| Fly | 0.625 | Two wingbeats with lagging abdomen, legs and antennae |
| FlyFast | 0.625 | Forward-leaning flight |
| Attack | 1.250 | Sword anticipation, diagonal cut, recovery; impact at 0.875 |
| Hit | 0.625 | Rearward thorax recoil with raised shield |
| Fidget | 0.875 | Alert head/torso movement while flying |
| Death | 0.875 | Backward roll, curled legs and abdomen, settling wings |
| Dead | 1.000 | Held death endpoint |

The native Standing/Walk loop is 0.625 s, Attack 0.875 s, Hit 0.625 s, Fidget/Death 0.875 s.
Attack keeps its native lead-in and adds recovery through the existing impact-marker runtime; gameplay timing stays
native. Both attack roles use Attack because this family has no ranged spell or missile. Head look is limited to
25° yaw / 15° pitch. Sword and Shield are separate rigid game attachments with the same tier variant as the body.

All three native SFT scales are 0.799988. Mean front flight silhouette area is 8,416 native pixels; matching it to
five model flight renders gives **166.626060719 world units/metre**. No hover offset is added. Flight stride is
1.125274 m at the tier-A 300-unit speed. Collision, health, movement, flying flags and physical combat stay native.
The source and cooked runtime assets are under `assets_source/worlds/mm8/models/` and `assets_dev/worlds/mm8/models/`;
only Wasp Warrior A/B/C are added to the MM8 actor bindings.

## Verification

- UV audit: zero overlap pixels, 38.91% occupancy, head density 2.21 times the body at 1K; retained in
  [UV audit](review/uv_audit.json). The paid texture return matched all 9,635 body triangles and their UVs.
- Final GLB reimport: all seven durations, 63 sampled pose comparisons and 192 Hz floor/loop checks pass.
  Maximum surface difference is 0.0021 mm. The held corpse is 2 mm above its plane; live interpolation stays within
  1 mm of the plane. Death was corrected to rotate around the thorax and settle without a floating body.
  [Export parity](review/export_parity.json) · [Delivery hashes and LOD checks](review/delivery_validation.json).
- Viewer: all **21 tier/clip switches** pass without console errors. Fourteen normal/half-speed recordings and their
  timestamped samples were inspected for wing/body coordination, grip, joint deformation and death continuity.
  These recordings show the current sword/slash revision; the extracted Attack strip includes the release and follow-through.
- The focused Wasp regression passes with the revised installed assets. The original delivery ordinary build passed;
  its wider MM8 actor suite was **38 passed, 1 failed** (not repeated for this asset-only correction):
  `mm8_juggernaut_actor_models_keep_rollers_tiers_and_roles` reports a missing model or changed simulation state.
  Juggernaut assets and its check were not changed by this task.
- Native NVIDIA/OpenGL 3.3 captures at MM6 `oute3.odm` and `6d19.blv` compare identical model/sprite cameras, all three
  tiers, all four LODs and close materials. A private hard-link fixture preloads native MM8 sprites; production maps
  remain unchanged. Static tours freeze simulation; separate live single-actor captures verify the death transition
  and ordinary loot satchel. The held Dead pose remains in the portable model/viewer.

| Review | Model | Original sprite | Live death / remains |
|---|---|---|---|
| Outdoor | [tiers](review/ingame/outdoor_models/01-party.png) | [native](review/ingame/outdoor_sprites/01-party.png) | [death](review/ingame/outdoor_live/dying.png) · [remains](review/ingame/outdoor_live/corpse.png) |
| Indoor | [tiers](review/ingame/indoor_models/01-party.png) | [native](review/ingame/indoor_sprites/01-party.png) | [death](review/ingame/indoor_live/dying.png) · [remains](review/ingame/indoor_live/corpse.png) |

[Run records](review/ingame/runs.json) · [Viewer check](review/viewer_check.json) · [Playback review](review/playback_review.json)

## Rebuild

Claim the project and use its lease with the shared wrappers. The retained `work/rig_uv.blend` is the original weighted,
unwrapped body/equipment checkpoint. `revise_sword.py` creates `work/rig_uv_sword_v2.blend`;
`animate.py` reads that revision and builds `work/anim_v1.blend`; `compose_textures.py` uses retained
Meshy maps and the local AO/UV raster. `export_wasp.py` packs the editable master and LOD0.
Run `tools/prepare_actor_glb.py`, then `build_lods.py` and `finish_runtime.py` for normal-map preparation, LODs,
shadow correction, region variants and equipment splitting. `refresh_lod_images.py` is only for map revisions
with byte-identical geometry/animation accessors; otherwise rebuild LODs. `export_parity.py` and `delivery_check.py`
verify the exports; `review_slash.py` verifies edge path and body/shield clearance. Install all three final GLBs through `tools/install_model.py --world mm8`.
`viewer_tiers.py` and `update_viewer_manifest.py` refresh the shared review viewer.

No Vulkan or Android build was run. Native captures are visual checks, not performance benchmarks.
