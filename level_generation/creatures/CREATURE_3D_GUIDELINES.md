# 3D creature model and animation guidelines

Historical baseline: 2026-10-06, using the reviewed MM6 demon and verified MM9 model/controller findings.
For current production, Codex and Claude use the [shared creature skill](../../.agents/skills/creature-to-3d/SKILL.md)
and its Claude playbooks. This document supplements that route. Runtime status labels below describe the original
baseline; [Model rendering](../../engine/render/MODEL_RENDERING.md) and the current implementation supersede them,
including implemented head look, impact timing, attachments and material handling.

Create creatures that preserve the original identity and combat readability while gaining convincing movement,
materials and depth in 3D. Use good existing 3D animations as a starting point where they fit the anatomy. Preserve
gameplay timing and characteristic gestures; sparse billboard poses should not force hesitant 3D locomotion.

These guidelines cover asset preparation and its contract with the engine. **Current** means implemented in the
shared demon integration. **Proposed** means a design for later work, not a feature an exported GLB already supplies.
Production and installation still follow the scope of the individual creature request.

## 1. Asset and engine responsibilities

| Asset supplies | Engine supplies |
| --- | --- |
| Recognizable anatomy, materials, a usable skeleton and skin weights | AI, movement, pathfinding, collision, target selection and combat rules |
| Continuous gait and readable action clips on that skeleton | Clip selection, playback clocks, short transitions and movement-driven gait phase |
| A hierarchy suitable for upper-body actions and stable attachments | Combining locomotion with a masked action when the actor is actually moving |
| Named sockets at meaningful anatomical locations | Socket transforms and bounded effects tied to the real gameplay action |
| Geometry LODs and simpler shadow meshes | Projected-size LOD selection, hysteresis, culling, lighting and shadow quality |
| Neck/head controls with reviewed motion limits | Optional procedural looking and its action restrictions, once implemented |

A clip describes how an action looks. It must not decide when damage happens, create another projectile, change
recovery, or move the collision actor independently. Smooth visual rotation follows the gameplay facing.
Allowing attacks while moving is an AI decision; supporting their blended presentation does not enable that behavior.

## 2. What works today

The [demon continuation](mm6_demon_meshy_reference_20261004/animation_controller_20261006/README.md) is the working
example, with its exact binding in [actors.yml](../../assets_dev/worlds/mm6/models/actors.yml).

| Capability | Current state |
| --- | --- |
| Idle/action transitions | Local-pose crossfades; demon uses 120 ms ordinarily and 60 ms into hit. Death visibility applies immediately. |
| Walking/running | Reviewed Meshy `Walking` and `Running`, phased by distance traveled. Blocked actors stop stepping. |
| Moving attack/cast | Locomotion plus one masked upper-body action. Ordinary MM6 combat generally stops to attack. |
| Visual turning | Shortest yaw arc, bounded at 540 degrees/second for the demon; no new turn clip is required. |
| Attack facing | Shared AI follows its current sensed target during windup; presentation smooths that facing. |
| Casting | Separate `Cast_FireBolt`, two palm sockets, charge/release FX synchronized with gameplay. |
| Attachments | Four named eye/palm nodes; optional ranged-hand emitter; shared world-space socket queries. |
| Detail scaling | Four color LODs, merged opaque shadow LODs and configurable sunlight shadows. |
| Independent head looking | **Proposed**; there is no runtime neck/head target-follow layer yet. |
| General animation-key events | **Proposed**; importing a GLB does not install MM9-style event dispatch. |
| Authored backpedal, strafing and foot IK | Additional work. Reversed gait is currently a limited retreat/turn transition. |
| Arbitrary weighted masks or variable-duration cast holds | Additional work beyond the current spine-subtree mask and single retimed cast. |

These demon speeds and transition times are working calibration, not compulsory values for every species.

## 3. Choosing animation sources

Prefer a reviewed preset over rebuilding ordinary locomotion from a handful of sprite anchors. Keep its provenance,
repair anatomy-specific faults, and judge the result at normal game speed. A service preset is a candidate, not an
automatic production acceptance.

| Motion | Starting choice | Review or adaptation |
| --- | --- | --- |
| Walking/running | Meshy or another compatible, good 3D gait | Stance, weight transfer, stride, foot contact, loop seam, talons and attachments |
| Idle/ready | Compatible preset or restrained custom motion | Preserve creature posture and personality; avoid conspicuous human breathing/gestures |
| Hit | Compatible preset if available, compared with native recoil | Direction, head tilt, arm response, magnitude, balance and return to the next action |
| Melee/ranged attack | Native gesture adapted into continuous 3D motion; suitable preset may supply a base | Reach, active hand, anticipation, contact/release and creature-specific posture |
| Spell cast | A separate, readable gesture appropriate to the creature | Charge location, palms, release direction and recovery; distinguish ordinary ranged attacks |
| Fidget | Native personality gesture or reviewed custom motion | Small head/foot/hand changes, support and a clean return to ready |
| Death/remains | Creature-specific motion and effect | Collapse/disintegration, visibility, interruption, corpse and reset behavior |

For the demon, the supplied Meshy download contained **Walking and Running only**. It supplies no verified hit,
attack or cast candidate. Keep the current hit until a better candidate has been obtained and reviewed.
Its disintegration death should retain that identity rather than acquire a generic human fall.

The [higher attack windup](mm6_demon_meshy_reference_20261004/attack_windup_20261006/README.md) is a scoped example:
raise the active arm to make preparation readable while retaining the same strike timing and compatible skeleton.

The [demon rig repair](mm6_demon_meshy_reference_20261004/meshy_rig_review/README.md) illustrates necessary adaptation:
shoulder spikes needed correct parents; humanoid toe curls and sideways foot roll needed correction for talons.
These were offline repairs, with the resulting transforms baked into the clips.

The reconstructed `Walk_Native` repeatedly eases toward six sprite anchors. That slows controls at each anchor;
more baked frames do not restore a continuous stride. Meshy's reviewed gait has more coherent support and swing.
In the [sampling comparison](../../output/performance/demon_animation_20261006/locomotion-sampling.txt), native walk,
Meshy walk and Meshy run each took about 5.5 microseconds for clip sampling plus hierarchy evaluation on the same
85-joint asset. Differences were below 1% and within run variation. This excludes blending, bounds, rendering,
shadows and AI; it is not an FPS result. Better authored motion does not inherently cost more to play.

Native sprites remain the reference for identity, distinctive poses and action ordering. Explicit native-motion
reconstruction or directional sprite delivery still needs the requested source timing. An in-game 3D gait can use
a selected preset with movement-driven timing while preserving the original gameplay speed.

## 4. Minimum animation delivery

Use semantic bindings rather than requiring every source file to rename its clips. The current manifest maps
`standing`, `walking`, `attack_melee`, `attack_ranged`, `hit`, `dying`, `dead` and `fidget`; its optional `animation`
block also selects `run` and `cast`. Compatible actions can share a clip: the demon's two attack bindings use
`Attack`, while its spell uses `Cast_FireBolt`. `dead` selects `Ash_Remains`.

Deliver a gait appropriate to the anatomy, a ready state, all gameplay actions that can occur, and the required
death/remains behavior. Aliases and held poses are valid where deliberate. Do not invent flying, running, two hands,
or a humanoid fall for a creature that lacks them. Additional attacks, left/right casts, strafe and backpedal clips
are optional until a real gameplay/presentation need justifies them.

Every delivered clip should have:

- A recorded role, source, duration, loop/held-end behavior and important action phases.
- Continuous rotations and plausible joint lengths; no stop at every sampled reference pose.
- Correct support, planted/swing feet, anatomical clearance and stable attachments throughout interpolation.
- A root suitable for engine-driven placement. Locomotion should not accumulate forward translation or root yaw;
  preserve hip bob and useful local body motion. Any deliberate root-motion action needs separate integration.
- A clean loop or usable recovery pose. Transitions cannot hide a bad loop seam or a wildly different skeleton.

Use the same skeleton, bind pose, orientation and node identities across the creature's clips. Retarget and bake
in authoring tools. Blender constraints, IK and simulations must produce exported motion; the game does not run
the authoring rig. No universal bake rate is required: preserve motion at useful sampling density and inspect
the exported interpolation. Do not resample good clips merely to reach 48 fps.

## 5. Rigging for animation blending

Blending support comes from compatible clips, a useful hierarchy and engine composition. Exporting a clip named
`RunAttack` does not establish any of those. Three distinct operations matter:

1. **Crossfade:** transition between whole poses, such as walking to standing or attack to recovery.
2. **Masked action:** retain gait in the legs/pelvis while an attack/cast controls selected upper-body bones.
3. **Procedural offset:** add a bounded look rotation to the sampled head/neck; this remains proposed.

For a humanoid, keep a clear pelvis/leg branch and an upper spine branch containing arms and head. The current
binding names an `upper_body_root`; that node and all its descendants receive action weight 1, with other nodes
at 0. It is a binary subtree mask, not a general per-bone weight-set asset. The demon uses `mixamorig:Spine`.

Keep pelvis and legs outside that action subtree. Give tails, wings, shoulder armor and held props parents suited
to their anatomical ownership. Decide whether each secondary structure should follow locomotion or the action;
if the hierarchy cannot express that decision, an explicitly authored weighted mask is future engine work.
Do not distort anatomy or reparent a useful existing rig solely to imitate Mixamo names.

Review the action twice: full-body while stationary, and combined with gait while moving. The upper-body version
must work without relying on an attack's leg lunge or large pelvis rotation. Repair the action or author a variant
only if the combination fails. Share compatible full-body/action motion where it works; avoid a separate clip for
every gait × attack combination. Hit, death and fidget currently remain full-body.

Evaluate one final pose, then use it consistently for skinning, shadow geometry, bounds and attachments. Extra
layers add pose-sampling work; they should not require duplicate model instances or a draw for each animation layer.
The current engine sampler and masked composition are sufficient for this baseline. Add an animation library only
for a demonstrated missing capability or measured bottleneck.

## 6. Naming and placing sockets

Sockets are named attachment frames parented to the relevant bone, exported as ordinary glTF nodes. They need no
deforming vertices and should not be added to the skin's joint list solely to locate an effect. Preserve their
names, parents and local transforms through export and LOD generation. Left/right always mean the creature's
anatomical left/right.

| Semantic role | Preferred node name | Placement and status |
| --- | --- | --- |
| `palm_left`, `palm_right` | `Socket_Palm_Left`, `Socket_Palm_Right` | Center of the palm's effect space; current cast and hand FX |
| `eye_left`, `eye_right` | `Socket_Eye_Left`, `Socket_Eye_Right` | Just outside the visible eye surface; current eye embers |
| `wrist_left`, `wrist_right` | `Socket_Wrist_Left`, `Socket_Wrist_Right` | Wrist attachment, distinct from palm center; proposed role |
| `mouth` | `Socket_Mouth` | Breath/projectile emitter outside the mouth; proposed role |
| `weapon` or a weapon-specific role | `Socket_Weapon` or documented equivalent | Actual grip/muzzle/effect attachment; proposed role |

Existing source node names can be retained through semantic mapping. The core requirement is stable meaning, not
renaming every deforming bone. For an eye with no separate eye bone, parent its socket to the head. For a weapon,
parent the socket to the actual weapon/hand owner so its motion matches the visible object.

Document the socket's outward direction and its finger/weapon direction in local axes, and verify the exported
world frame in multiple poses. Current demon FX uses socket positions; standardized orientation-driven emitters
are proposed. Do not infer an emitter direction from arbitrary source bone axes. glTF is Y-up; the demon faces
glTF +Z and declares an explicit runtime yaw offset. Preserve the model's documented conversion.

`animation.sockets` names points on the skeleton: a node (`palm_left: Socket_Palm_Left`), or a node plus an
offset in its space (`eye: {node: Head, offset: [0, 0.12, 0.2]}`), so a point needs no new node in the GLB. The
sockets `eye_left` and `eye_right` carry `eye_color`. The ranged attack and cast events name their charge sockets
(section 7). The animation block still requires cast/run clips, stride length and a mask root. Do not invent fake
eye/hand nodes for creatures without them; place an offset socket on the bone that carries the spot instead.
Sockets are placed in the timing review (`timing_review/`, section 3) and written by its `apply_decisions.py`.

## 7. Casting and attached effects

Every bound spellcaster must select a cast clip, by default distinct from its melee and ordinary ranged clips. One
suitable cast gesture may serve several spells, retimed to their existing gameplay action clocks. The loader rejects a
spellcaster binding without `cast`; this changes presentation without changing combat timing. Where the user prefers
the attack gesture for spells, `cast` names the attack clip and the cast event carries that clip's impact marker
(user decision 2026-10-19: MM8 Centaur, Dark Elf Warrior, Wererat human form `mm8_m444` and Naga).
For the demon, melee and the ordinary fire missile share `Attack`; only that fire missile gets the right-palm
trail. Spellcasting selects the separate two-handed `Cast_FireBolt`.

Charge and release sockets are event keys of the ranged attack and the cast:

```yaml
animation:
  # Other animation fields as in the demon manifest.
  sockets:
    palm_left: Socket_Palm_Left
    palm_right: Socket_Palm_Right
  events:
    attack_ranged:
      impact: 0.5
      glow: [palm_right]                   # one hand: it charges there and the missile leaves it
      effects: {Fire: openyamm:fx/creature_fire_hand}   # optional named effect instead of the glow, per element
    cast: {impact: 0.87, glow: [palm_left, palm_right]}  # both hands: the spell leaves between them
```

The usual setups: one hand (glow and release on it), both hands (glow on both, release between), a staff, an eye or a
mouth (one socket). `release` names a different leaving point (a staff head while the palms glow); `glow_scale` sizes
the glow and `color` overrides its colour. The colour is derived from the projectile the action releases (the spell, or
the Attack1/Attack2 missile token through `monster_projectiles.txt`, with the enhanced flight light when the monster's
projectile binding has one), so tiers with other elements or spells charge in their own colour. Arrows, rocks and other
physical missiles charge only in an authored `color`. `effects` keys are Air, Earth, Fire, Water, Body, Mind, Spirit,
Light and Dark, resolved against the monster table's missile tokens at loading. Impact, interruption, death and leaving
the eight-actor attachment budget stop emission and let the short trail expire.

Named effects on sockets (MM9's `DoFX`/`EndFX` keys, which play a monster's FX0–FX2 such as `bluedots` on its hands)
are event keys of every role, with or instead of the glow, and of any other clip:

```yaml
  events:
    attack_melee: {impact: 0.36, effect: {id: mm9:redyeldots, sockets: [palm_left, palm_right], start: 0.36}}
    attack_ranged:
      impact: 0.833
      release: palm_left
      effects:                             # a list: several effects
        - {id: mm9:greenyeldots, sockets: [palm_left, palm_right], start: 0.133, end: 1.266}
    cast: {impact: 0.833, release: palm_left, effect: {id: mm9:greenyeldots, socket: palm_left, start: 0.133}}
    taunt: {effect: {id: mm9:greenyeldots, sockets: [palm_left, palm_right], start: 0.141, end: 0.817}}
    resurrect: {effect: {id: mm9:GreaterDemon, socket: body}}   # MONSTERS.txt ResurrectFX, as a corpse rises
```

MM9's `DoFX n [loop]` plays FX*n* of the monster's `MONSTERS.txt` row, **0-based** (FX0–FX2; `n` of 3 or more, or an
empty column, plays nothing: `object.lto` `0x1001af90`, record `+0x1a8 + 4n`), until the clip's next `EndFX`; a second
`DoFX` in the same clip replaces the first. `ResurrectFX` plays as a corpse rises (vtable `+0x2f4`, `0x1001acf1`).
Several MM9 models name a column their rows leave empty (Monk, Banshee and Zombie `DoFX 1` with only FX0): those clips
show nothing in MM9 either. MM9's dots effects (`bluedots`, `redyeldots`, `greenyeldots`) put one emitter on `LHand1`
and one on `RHand1` (their library components' `body_anchor`): an effect named on as many sockets as it has such anchors
gives each socket one anchor's emitters, in order (`sockets: [palm_left, palm_right]`), so the two hands together emit
what MM9's one effect does; on one socket every emitter plays there. A `script_clips` role that reuses another role's
GLB clip shares its effects (events follow the clip), so leave out effects MM9 has on one of them only.

`effect: {...}` or `effects: [{...}, ...]` (at most eight; a map `effects` stays the ranged attack's per-element form)
take `id` (in the effect library), `socket` or `sockets` (one to four names from `animation.sockets`, one effect on
each), `start` and `end` in clip seconds (default: the clip's start, and until the clip ends or another starts) and
`scale` (relative to the actor's effect scale). The effect starts once per play of the clip at `start`, follows its
socket and drains at `end`, when the clip changes or restarts, or when the actor's model goes. Clip times are the
model's own (the GLB clip), so a marked clip's effect starts at the same pose however long the native action runs. An
event keyed by a `clips` or `script_clips` role other than the three actions (`fidget`, `taunt`, `resurrect_spell`)
plays that clip's effects only (no impact, glow or release). Every clip with events shows them whoever plays it: the
AI, a behaviour script or a cinematic's `actor ... action: clip` cue (a cue playing an action role's clip also charges
that role's glow up to its impact). Effects start only on actors visible within 4096 units of the party, or playing a
script's or cinematic's clip. Scripts carry effects on an actor with `evt.SpawnActorEffect(actor, effect[, socket[,
seconds[, scale]]])` and end them with `evt.StopActorEffect(actor[, effect])` (MM9: `MM9.actorFx`, `MM9.stopActorFx`);
`socket` is an `animation.sockets` name or a node of the model (a comma-separated list carries one on each, sharing
a hand effect's emitters as above), and without one (or for a sprite actor) the effect follows the middle of the body.

## 8. Facing and independent head motion

Keep gameplay yaw, visual body yaw and optional visual head direction distinct. The engine owns smooth facing and
distance-based gait. Art supplies footwork and any useful turn/backpedal variants. Reversing a forward gait can
cover a brief retreat transition, but a sustained backward gait deserves its own reviewed animation.

Attack tracking should have an explicit action policy. The current demon follows the sensed target during windup,
and gameplay retains release/aim authority. Head tracking should not rotate an already released strike indefinitely
or erase a deliberately authored recoil. Backing away, circling and moving while attacking remain AI decisions.

**Proposed head layer:** name the actual neck/head bones in future binding metadata, preserve their authored motion,
and compose a small relative yaw/pitch offset after clip blending and before hierarchy, sockets and skin matrices.
Smooth the offset and fade it toward neutral when disabled. A practical initial demon trial is ±45 degrees yaw,
±15 degrees pitch and 90 degrees/second, subject to anatomy and playback review. These are proposed tuning values.

Use the actor's existing sensed target rather than searching for targets again or always looking at the player.
Fade out tracking during hit/death and during action intervals that require a fixed head pose. Follow actual pause,
restore and teleport semantics. Neck participation is useful where head-only rotation pinches the skin, but does
not justify a full IK solver for every creature.

Head roll/tilt belongs first in authored hit, fidget and casting motion. Add procedural tilt only for a clear
behavioral purpose; automatic roll on every turn can weaken the creature's posture. Jaw animation and moving eyes
are optional controls, independent of using sockets for effects. A creature without a suitable neck/head should
simply omit procedural looking. This proposed layer adds transforms, not another mesh or complete animation clip.

## 9. MM9 examples and their limits

The [verified MM9 investigation](../../output/research/mm9_models_20261006/REPORT.md) establishes independent
animation trackers and authored `Top`/`None` bone masks. The guard's upper-body mask selects 24 of 35 bones; the
stage-two demon's selects 65 of 105, with lower-body weights zero. `None` disables the extra layer. This is the
useful precedent for gait plus an upper-body action, rather than storing every combined motion as a separate clip.

MM9 also stores clip transition times and action keys. Examples include the guard's `Hattack1` lunge at 134 ms
and attack event at 456 ms, and the monk's `castspell1` `CastSpell; DoFX 1 0` at 500 ms with `EndFX` at 900 ms.
These illustrate coordination between choreography and timed events. Our MM6–MM8 combat clock remains
authoritative; importing those clips alone does not install the original event/controller behavior.

The [head-follow investigation](../../re_mm8/mm9_vfx/HEAD_TRACKING.txt) verifies a separate bounded head controller:
extra yaw clamped to approximately ±70 degrees, with a default 90 degrees/second approach rate. Model keys
`HeadFollowPause` and `HeadFollowResume` give the authored action control. Dragon `Rattack2` and `Rattack3` pause
at 0 ms and resume at 2,000 ms. These are examples of action gates, not instructions to copy those timings.

Capabilities were not universal. MM9's selected demons use custom head names and have `HeadTurn=0`; the capability
query looks specifically for `Bip01 Head`. The sampled banshee's `Top` mask affects its entire rig, while some other
models lack masks. Native scripts decide how capabilities are used. Do not claim every MM9 monster could run,
cast and head-track simultaneously. Adopt the separation of responsibilities with explicit per-creature support.

## 10. Geometry, materials and performance

For an ordinary detailed humanoid, approximately **15,000 triangles at close LOD** remains a working starting
budget. Count all body parts, equipment and material sections together. It is not a universal hard cap or an FPS
guarantee: screen coverage, actor count, draws, skinning, shadows and FX determine actual cost. Preserve silhouette,
face, digit separation and joint deformation; surface grain and small relief can use textures/normal maps.

Prepare three or four reviewed color LODs and cheaper shadow geometry. The demon currently uses four levels:
16,474 / 8,237 / 2,980 / 1,019 triangles, retaining the same skeleton and clips. Those are measured example counts,
not mandatory ratios. Current selection uses projected size with hysteresis; shadow detail is chosen independently.
Use [the existing LOD workflow and tool](../../assets_dev/worlds/mm6/models/README.md#runtime-lods-and-shadow-quality--2026-10-06).
Avoid collapsed fingers, spikes or facial holes at the distances where a level will actually be used.

Use as many bones as the required anatomy and motion justify. The demon's 85 skin joints are a reference, not a
template every creature must reproduce. Keep normalized nonnegative weights and valid bind matrices. The loader
supports at most eight influences per vertex; prefer fewer where deformation remains adequate, and review before
discarding existing weights. Separate sockets need not increase that deforming-joint count.

Deliver verified glTF material inputs: base color, useful roughness/metallic variation and normal maps where they
improve the surface. Skin/leather/bone are ordinarily nonmetallic; eyes can be glossy without metallic skin.
Base color uses the color-texture path; normal and metallic/roughness maps are linear data. Keep UVs attached through
animation and review seams, mirrored charts, normal-map orientation and triangulation in actual moving exports.
The renderer currently uses derivative-based normal mapping; authored tangents are not a new blanket export
requirement. Validate the result before adding another tangent pipeline. Use suitable texture density and filtering.

For A/B/C tiers with the same anatomy, share geometry, UVs, rig, clips and every LOD. Use standard
`KHR_materials_variants` for the complete material sets and select a named `skin` in `models/actors.yml`.
The name resolves once at loading, and each actor caches its selection at creation. The renderer uses the
selected material for both color and shadow draws, including alpha/culling decisions. Unmapped sections retain
their default material. Native palette colors, including eyes, belong to each variant material; keep the pupil
separate and avoid one fixed red iris shared across tiers. `animation.eye_color: [r, g, b]` separately specifies
the variant's sRGB eye-particle color. Do not change table IDs or combat rules to choose a skin.

When variants share a calibrated model size but have different native sprite scales, set `scale_reference`
to the descriptor used for that calibration. The shared loader multiplies the authored `scale` by the ratio
of the variant's standing sprite-frame scale to the reference's, using the already loaded table. It caches
the result and scales attached FX proportionally. Missing/invalid reference frames fail explicitly.

Use generated [HD masters](CLAUDE_HD_MASTER_REFERENCES.md), never restored/native frames, for Meshy retexturing.
Follow the selected playbook's UV-preservation or verified UV-transfer route. Colour-only tiers share every texture
and use region masks/ramps under [Creature textures](CLAUDE_CREATURE_TEXTURES.md); separate baked textures need an
actual pattern/detail difference. The [demon variants](mm6_demon_meshy_reference_20261004/variants_20261006/README.md)
are historical evidence, not a per-tier retexture default. Measure delivered texture memory.

Profile the shared path with the same camera, scene, settings and warmup. Measure frame time and CPU/GPU work as well
as FPS, including a crowd and a scene without visible models. Attribute pose, shadows, draws and FX separately.
Do not turn a clip-sampling microbenchmark into an overall performance promise. The
[LOD/shadow measurements](../../output/performance/demon_lod_shadow_20261006/REPORT.md) and
[animation measurements](../../output/performance/demon_animation_20261006/REPORT.md) are worked examples.

## 11. Per-creature handoff and acceptance

Use the existing creature project, progress record, README and runtime binding; a new general manifest format is
unnecessary. Record the selected editable master and actual export, provenance/hashes, orientation/scale, clip-role
mapping, gait stride, mask root, socket names/parents, action timing and any explicitly unsupported behavior.
Include actual triangle counts per LOD, skin joints, maximum influences, material sections and texture resolution.

Review the delivered export with fixed front/profile/rear cameras and in motion at game size. Check gait contact
and seams; walk/run/idle transitions; attack and cast from stationary and moving poses; hit interruption; death,
remains and state reset; socket alignment; attachments and secondary anatomy; materials and normal maps under
daylight, shade and local lights; and LOD transitions. Proposed head tracking needs separate review once implemented.

When installing, retain existing AI, action timing, picking, collision and save behavior. Exercise both indoor and
outdoor shared consumers where affected. Validate only the changed dependencies after a local repair; full visual
acceptance still covers the selected final set. A correct GLB structure is necessary but does not establish good
animation or likeness.

For the demon continuation, retain the accepted Meshy gait, action/cast distinction, sockets and FX. The next
useful additions are a bounded head-look layer and a reviewed hit-motion candidate if the current hit needs
improvement. Add authored backpedal/strafe or channel loops when actual gameplay uses them. Keep these additions
separate from a redesign of AI, a replacement animation framework, or new paid asset generation.
