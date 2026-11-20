# MM6 demon A/B/C skins — 2026-10-06

The installed [actor bindings](../../../../assets_dev/worlds/mm6/models/actors.yml) select three skins from one
GLB. A retains its selected Meshy texture; B/C were retextured in Meshy using the corrected neutral model and
four **restored** appearance views. Geometry, UVs, skin weights, sockets, all ten clips, four color LODs and
independent shadow meshes are preserved.

[Compare front and face views](review/variants_contact.png).
Native NVIDIA/OpenGL 3.3 captures at 1600×900: [A](review/ingame_demon_a.png),
[B](review/ingame_demon_b.png), [C](review/ingame_demon_c.png).
Matching-camera profile/back renders are in [review/](review/).

| Native table actor | ID | Skin | Native iris sRGB | Appearance |
|---|---:|---|---|---|
| Devil Spawn / Demon A | 502 | demon_a | 231, 156, 156 | Dark gray skin, green harness, salmon eyes |
| Devil Worker / Demon B | 503 | demon_b | 250, 102, 102 | Green skin, olive harness, red eyes |
| Devil Warrior / Demon C | 504 | demon_c | 250, 176, 62 | Muted red skin/harness, amber eyes |

Eye colors come from original palettes 688/687/686. Separate iris materials select the native colors;
near-black pupils and white claws are shared. Matching eye FX colors are explicit binding data.
B/C also use `scale_reference: Demon A`: their standing sprite-frame scales make B approximately 7% and C
approximately 14% larger than A. The ratios are resolved from the loaded table once, retaining A's reviewed size
and composing with runtime height/Shrink changes; attached effects scale proportionally.
Meshy's B/C skins remain generated interpretations, especially the muted C skin/harness and tinted abdomen;
their artistic acceptance is pending user review.

## Selected files and provenance

- Editable [variants master](mm6_demon_variants_master.blend), with packed images and all variant materials.
- Portable [animated GLB](mm6_demon_animated.glb), with standard `KHR_materials_variants`.
- Installed [runtime GLB](../../../../assets_dev/worlds/mm6/models/mm6_demon.glb).
- [Reference provenance](references.json): restored front/profile/back frames, native palette mapping,
  and a mirrored right profile because the native set stores only one side. No imagegen skin generation.
- [Neutral upload](demon_neutral_upload.glb) and [upload record](upload.json): the existing rest geometry/UVs,
  neutral irises and separate pupils, without rig, animation or death plume.
- Meshy requests: [B](demon_b_request.json), [C](demon_c_request.json).
  Original downloads and hashes remain in the project [progress record](../creature_3d_progress.json).

Meshy B task `01a110f3-de8b-7242-bc1d-9a3ce537965b` and C task
`01a110f4-60da-700d-82b2-60c6afbeb2c3` succeeded, consuming 10 credits each: **20 total**.
Both used Meshy 7, original UVs, PBR maps and four references.
See the [official retexture API](https://docs.meshy.ai/en/api/retexture).

[Assembly](assemble.py) transfers materials onto the existing animated binary; it does not replace the
animated geometry or regenerate LODs. Returned geometry is used only to verify correspondence. Original 2K
downloads are retained; runtime B/C base color is 2K,
normal and roughness maps are 1K. Metallic is zero for skin/leather/bone. Images use the existing PNG/mipmap path.
The Blender master defaults to A; portable viewers must support/select material variants to see the other skins.

## Engine selection and FX contract

`skin` resolves once at binding load; each actor caches an integer selection at creation.
Each primitive has a default/variant material table, used for both color and shadow submission.
There are no additional geometry buffers, draw calls, shader branches or per-frame skin-name searches.
The extra B/C textures occupy approximately **64 MiB of RGBA8 GPU memory including mipmaps**, shared across actors.
They also add file/loading memory; this is not a claim of literally zero runtime cost or a controlled FPS result.

The existing shared indoor/outdoor presentation selects a distinct cast clip for native spell actions.
Modeled spellcasters must supply that clip. Elemental ordinary ranged attacks use a matching named hand effect
from `ranged_hand_effects` and one or two `ranged_hand_sockets`. Recipes are resolved from native
Attack1/Attack2 missile tokens once at binding load. The demon's fire Attack2 uses its right palm;
its melee Attack1 and spell actions do not acquire that trail. Physical arrow/cannon/blaster attacks are excluded.
No generic effects for unused elements were added: other creatures supply matching existing recipes.
Runtime bolster overrides that change a missile element would need separate binding support.

Existing gait, blends, turning, higher attack windup, charge/trail sizes, AI, timing and death behavior are retained.
See [creature guidelines](../../CREATURE_3D_GUIDELINES.md) for the reusable authoring contract.

## Checks and review

[Verification](verification.json) checks triangle winding and UV correspondence after Meshy's uniform recentering.
Maximum position/UV error is 1.70e-7; nodes, skins, animation/accessor data and original binary prefixes match.
No body topology, animation or LOD edits were introduced.

[Recorded checks](checks.json): normal desktop/unit builds passed, 15 unit cases / 3,056 assertions and all four
focused headless cases passed. The shared-asset test spawns IDs 502/503/504 with native HP 100/280/540;
the existing FX test checks spell gestures, fire Attack2, physical Attack1 exclusion, interruption and death.

From the repository root:

```sh
cmake --build build --target openyamm openyamm_unit_tests -j25
./build/tests/openyamm_unit_tests --test-case='*ModelAnimation*'
OPENYAMM_REGRESSION_FILTER=mm6_demon_actor_models \
  ./build/game/openyamm --world mm6 --headless-run-regression-suite actors
./tools/run_demon_3d_test.sh
```

The default trial spawns three A, two B and two C demons. Its automatic console sequence adds B/C
beside the A group, reports the counts and returns to gameplay after a few seconds.
For a single tier, disable that sequence and select the desired ID:

```sh
./tools/run_demon_3d_test.sh --set debug.menu_input_tour_path= --set debug.actor_spawn_id=503
./tools/run_demon_3d_test.sh --set debug.menu_input_tour_path= --set debug.actor_spawn_id=504
```

Additional manual spawns use the ordinary in-game console:

```text
actor spawn 503 1 -9528 -11919 161
actor spawn 504 1 -9328 -11919 161
```
