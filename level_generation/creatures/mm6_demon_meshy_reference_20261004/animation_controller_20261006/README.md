# Demon animation and socket continuation

The [higher attack windup revision](../attack_windup_20261006/README.md) now supplies the selected editable master
and animated exports. It changes only the attack's arm lift and retains this revision's accepted cast, gait and sockets.

The selected continuation adds smooth visual turning, clip transitions, movement-driven gait, masked moving actions,
and an authored two-handed casting gesture. It retains the selected anatomy, textures, all nine previous clips,
85 skin joints, four colour LODs and merged shadow LODs. No animation library or new rendering pass is required.

## Selected files

- [Editable master](mm6_demon_animation_master.blend): copied from the selected textured master, with Cast_FireBolt
  and four bone-parented socket empties. Original animation curves and geometry remain intact.
- [Portable animated GLB](mm6_demon_animated.glb): original portable payload plus the cast and sockets.
- [Runtime GLB](mm6_demon_runtime.glb): same additions to the existing PNG-textured, particle-death, four-LOD export;
  installed as `assets_dev/worlds/mm6/models/mm6_demon.glb`.
- [Animation review](index.html), [export preservation checks](export_checks.json).

## Presentation rules

The AI remains authoritative for movement, facing, attack choice, cooldown, damage and projectile release.
The model follows its exact world position but turns along the shortest yaw arc at up to 540 degrees/second.
Ordinary pose transitions take 120 ms, hit transitions 60 ms. Death/remains visibility tracks apply immediately.
Interrupted transitions start from the last displayed local pose. Pausing freezes turning, gait and blend time.
Teleporting reinitializes presentation instead of interpolating across the map.

Meshy's corrected Walking clip follows actual distance travelled: one cycle per 1.5 model units. Blocked actors stop stepping.
The user selected Meshy's locomotion on 2026-10-06 after reviewing Walk_Native and a walking-only trial.
Both manifests select Walking for slower movement and Running above 2.4 model units/second, with a 55% longer stride.
Movement opposite the displayed facing reverses the locomotion cycle, with hysteresis and a short direction blend.
This covers a turn/retreat transition; it does not add a new retreat decision or change fleeing behaviour.

Stationary attacks retain their full authored pose, including feet and tail. Attack windup updates the shared AI
facing toward its current sensed target; presentation smooths that yaw. Release timing and targeting remain native.
Moving attacks/casts combine locomotion
below the spine with the action above it, using a shared per-asset bone mask. Hit, death and fidget remain full-body.
Classic MM6 AI currently stops to attack, so ordinary combat shows walk-to-action transitions; the moving-action
path is exercised by the runtime regression without changing gameplay balance. Foot IK and authored side-step or
backpedal variants remain separate artwork/features; this implementation does not claim those motions exist.

## Cast and sockets

Devil Spawn (Demon A, merged monster 502) has **Fire Bolt**, plus a separate ranged fire attack. Spell actions use
Cast_FireBolt; the ordinary ranged attack retains Attack. The new one-second authored clip gathers the hands during
the first 34%, channels through 84%, then thrusts/releases. Runtime maps it to the actual native action duration,
so it cannot delay a projectile or change recovery. Its body/effect visibility inherits Standing's held values.

Socket_Eye_Left/Right follow the head and are positioned from the existing iris surfaces. Socket_Palm_Left/Right
follow the hands. They are glTF nodes, not additional deforming joints. `nodeMatrix` exposes each socket in world
coordinates; the midpoint of the palms supplies the channel origin.

The existing particle system provides subtle red eye embers, a round charge glow with a bright core, three rising
charge sparks per emission, and a twelve-spark release burst. Charge colour follows the actual spell recipe, including other
spells in the crowd trial. Release observes the AI's impact flag once; interruption/death cancels it. Actual
projectile simulation and its existing chest-height spawn/forward offset are retained; particles do not spawn a
second damaging projectile. Eye and charge emission is limited to 10 Hz and the nearest eight actors in a nearby
camera cone (2,048 units). This gate runs before socket sampling; hidden distant crowds do not acquire per-frame
skeletal evaluations. The cone is conservative, not exact room/frustum visibility.

The user accepted the casting gesture on 2026-10-06, then requested clearer ranged-fire presentation and a larger
charge. Demon A's ordinary fire missile now uses an imported MM9 fire sprite attached to Socket_Palm_Right with
a 180 ms world-space trail; melee has no hand emitter. After the visibility review, hand sprites use five times
their original dimensions (half the enlarged review size). The charge's outer radius reaches 64 world units,
with a 32-unit bright core and 24-unit sparks: twice the round effect's first review size. Glows use the shared
radial particle texture indoors and outdoors; the former untextured rectangular glow pass is removed.
See the [feedback checks and MM9 facing evidence](../../../../output/performance/demon_animation_20261006/feedback/REPORT.md).

## MM9 evidence and scope

The [MM9 investigation](../../../../output/research/mm9_models_20261006/REPORT.md) verifies its independent tracker
and Top/None masks. The verified object.lto also exposes `BackPedaling` (state comparison 0x38 at 0x1001941a),
`Strafing`, `StrafeAttackPct`, and a `CalcRotationRate` script operation (factory at 0x100a08f3). These support
separating movement, facing and animation presentation. They do not establish one universal MM9 turning rate or
prove every monster used masked casting. Our timing/mask are original choices for this demon.

## Review and reproduction

`author_cast.py` writes a new Blender master and casting export. `merge_cast.py` verifies identical bind bases and
appends only animation/socket data to recorded original exports. It preserves the complete original binary prefix,
meshes, UVs, images, materials, weights, native channels, LOD metadata and shadow meshes. `review_cast.py` reimports
the portable output and renders front/profile source times plus a 48 fps playback sequence.

Run `./tools/run_demon_3d_test.sh` to review three native Devil Spawn actors, or
`./tools/run_sorpigal_demon_crowd.sh` for the presentation-only crowd. Validation results and native captures are
recorded in the [validation report](../../../../output/performance/demon_animation_20261006/REPORT.md).
The casting gesture is user-accepted; the latest hand-FX/charge-size feedback pass is available for live review.
The cast is an added motion, not a recovered native sprite animation.

## Cast marker (2026-10-10)

actors.yml `events: cast: {impact: 0.92}`: the spell is released mid-thrust (0.84-1.0 s release phase) and the
thrust finishes as follow-through, instead of the whole 1.0 s clip being squeezed into the 0.75 s cast. The launch
point stays the body's (the hands release symmetrically). See [clip timing audit](../../CLIP_TIMING_AUDIT_20261010.md).
