# Brood Mother rig and motion

2026-10-23: fitted rig and six clips retained in the textured `export/hes_brood_mother.blend` / `.glb`.
The current numeric evidence is `review/texture_ready_gates.json`; viewer/native acceptance remains external.

## Selected actions

| Role | Duration | Source and adaptation |
|---|---|---|
| Standing | 9.9333 s | Local `Breathing Idle.fbx`, 30 FPS; upper-body delta over the fitted seated rest, fixed palms/base, eased return. |
| Fidget | 4.4667 s | Local `Look Around.fbx`, 30 FPS; constrained head/neck turn with horn clearance, eased return. |
| Attack | 1.50 s | Authored seated acid-spit lean, with fixed palms and belly. The library's Spit Reaction depicts receiving spit and was rejected. |
| Hit | 1.00 s | Local `Standing React Large From Front.fbx`, 30 FPS; constrained upper-body recoil and return. |
| Death | 2.50 s | Authored backward settle into the cradle and head slump, then a small settle. |
| Dead | 1.00 s held | Exact final Death pose. |

Walking/run map to Standing: stationary actors have no locomotion. No paid animation or head-bob work.
Source paths, hashes, rates and adaptations are in `work/clip_sources.json`; raw library files were not copied.
The backward standing death was tried and rejected: it drove the crown into the cradle and introduced a
31.6-degree half-frame rotation jump. That diagnosis justifies the local seated death instead of another paid clip.

## Timing contract

Native reference: `zDemonQueen` descriptor 646, height 300. Standing/walking/fidget `qfia0`, attack `qata0`,
hit `qwia0`, dying `qdea0`, dead `qdef0`. SFT lengths at 16 ticks/s give 1.125 s idle/attack/hit and 0.9375 s
native dying. `qata0` contact_frame 4 follows four 3-tick frames: 0.75 s native release lead.
These inform gameplay timing, not the authored idle duration. Hit finishes within 1.125 s.

The exported `Socket_Mouth` reaches maximum forward spit extension at **0.7667 s**, within the ±20% release
window. Use this measured time for the eventual ranged event marker. The socket is a surface probe at
(-1.0764, 0.2847, 3.6669) m in the initial fitted rest, parented to `B_Head`; the report measures its actual
exported motion. No projectile or gameplay script has been changed.

## Fitting and ownership

The upper-body B_* convention and source frames come from `mm6_qfi_claude/work/source_rest.json`, read-only.
Shoulders/elbows use opposed visible skin hits; wrists use closed mesh cross-sections. Finger branches use
surface connectivity and measured terminal positions, with the missing left little claw restored locally.
`work/joints.json`, `work/fingers_fit.json`, `work/rig.json` and `review/rest_contact_fit.json` retain evidence.

The initial frame comparison is 0.0 degrees and at most four normalized influences. The palms were moved
outward/upward through a two-bone solve, then baked as the fitted rest. Animation retargeting aligns world
rotations to that actual rest, uses source timing, and pins the palms without changing arm lengths.
Fingers preserve their rest chains. The whole horn arcs are rigid on the head, including the low right tip
that the first height-based ownership cut missed. Belly, cradle and socket pads stay on static `Base`.

Every final clip is checked at 60 Hz, including half frames/endpoints: arm and hand stretch, upper-body stretch,
wrist swing ≤60°, forearm roll ≤90°, upper-arm roll ≤60°, step continuity, fixed base, floor contact,
real-surface head/hand versus torso/cradle/belly checks, return/loop endpoints and Death→Dead equality.
The separate sacs are checked through their all-clip bounding cylinder against actual exported queen triangles.
The reports carry the GLB hashes; preliminary passing reports do not certify a later revision.

## Binding handoff

Intended scale 100 gives 450 game units; do not apply ×1.5 again. Keep `upper_body_root: B_Spine`, walking/run
as Standing, a required `animation.cast: Attack` fallback, and the usual six clip role keys. Row 10111 is a
Body ranged attacker, not a spellcaster. Limit or omit runtime head look until the integrator verifies its
additional horn sweep; the current clearance evidence covers the authored clips only.
The binding now uses the supported `fixed_yaw_degrees: 0` (east), matching D9 actor 77. D9 owns sac relocation;
README records the engine-transformed world positions. Runtime head look remains omitted. No engine changes.

Texture transfer, four LODs and binding/staging are complete. `review/delivery_checks.json` proves zero pose
position change across all six clips after texturing and joining; browser/game playback remains with the integrator.
