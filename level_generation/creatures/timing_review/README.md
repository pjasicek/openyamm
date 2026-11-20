# Attack timing review

A browser review of every 3D actor's attack and cast clips against the native billboard timing: pick each attack
sprite's contact frame and each clip's `animation.events` impact, and plan what to change in the clips.

```
level_generation/creatures/timing_review/build_review_data.py --world mm8   # after models, actors.yml or monster data change
level_generation/creatures/timing_review/serve.py               # http://127.0.0.1:8765/level_generation/creatures/timing_review/?world=mm8
```

`--world` (default `mm6`) picks the world's `actors.yml`; each world's data goes to `data/<world>/` and the viewer
loads it with `?world=<world>` (default `mm6`). Native frames come from the retired monster sprites (no monster
billboard is in the runtime since 2026-10-21): MM6's retired runtime sprites, then `assets_legacy/` MM8
(`sprites_mm8_monsters_20261019/`), MM7 (`sprites_mm7_monsters_20261021/`, also the MM7 world's own families: Behemoth,
elementals, Gog, Roc and Wyvern) and the rest (`sprites_monsters_remaining_20261021/`), matched case-insensitively, as
are the attack sounds. A model without attack or cast clips (a fleeing peasant) is left out. All worlds share `decisions.json`: picks are keyed by model, clip and sprite
frames.

The browser shows each model from its accepted source in `assets_source`: the runtime copies in `assets_dev` are
cooked from it, and their `textures/*.oytex` are GPU formats a browser cannot decode. Runtime clips that differ from
the source are flagged. `build_review_data.py` reads the installed
runtime models that `assets_dev/worlds/<world>/models/actors.yml` binds (what
the game plays and what the current markers describe), the monster tables and the native sprite frames, and writes
`data/<world>/` (rebuildable). `serve.py` serves the repository read-only and saves the review to `decisions.json`.
`node check_review.mjs <url>` opens every model and role headless and fails on load or console errors.

## How the game times an attack

- The attack lasts the native sprite attack animation (`SpriteAttackMelee`/`SpriteAttackRanged` length in the
  sprite frame table; spells use the ranged one). The attack sound plays when it starts. The game applies it (the
  blow lands, the missile or spell is released) when the sprite's **contact frame** appears, picked here and stored in
  `assets_dev/engine/rendering/sprite_attack_timing.yml`; a sprite without one applies it when the whole animation
  has played, as MM8 does (`re_mm8/ACTOR_ATTACK_TIMING.md`), unless the clip's `impact` marker falls within the
  action: then the game applies it at the marker (since 2026-11-04, any world; MM9's manifest, `attack_timing: clip`,
  times the whole action by the clip). The monster recovery (`Rec` in `monster_data.txt`) is a timer from the
  attack's start.
- A model clip with an `impact` marker has its wind-up `[0, impact]` fitted to the time until the game applies the
  attack; the rest plays at its own speed, through the rest of the action (whole body) and then as follow-through
  over whatever the AI does next (whole body while standing, the upper body over the walk). A clip without a marker
  plays at its own speed and is cut when the action ends. Every state change is a 0.12 s crossfade. See
  `engine/render/MODEL_RENDERING.md` (Action timing).

## The viewer

`?models=mm6_arc1,mm6_gob2` limits the list (the test run:
`http://127.0.0.1:8765/level_generation/creatures/timing_review/?models=mm6_arc1,mm6_gob2,mm6_pmn2,mm6_ogr`).

- **List**: per model, one chip per bound role (M melee, R ranged, C cast): red = no 3D marker or a source blocker,
  amber = wind-up outside 0.85-1.2x or a tail longer than the gap before the next attack, blue "at end" = no
  billboard contact frame yet, green = fits, grey = never played (no such attack in the monster data, or Wimp AI).
  ✓ = both frames picked.
- **Panel, 1 · Billboard frame**: the native attack frames with their start times. Click the first frame that shows
  the blow or release (the game applies it as that frame appears), or *Original: at the end*. Tiers sharing the same
  frames share the pick.
- **Attack sound delay** (under the billboard frames): seconds after the attack starts that its attack sound plays;
  0 (the default) plays it as the attack starts, as MM8 does. Shared by the sprites with the same frames.
- **Panel, 2 · 3D frame**: in *Raw clip* mode step (←/→) to the clip's blow or release frame and press **I** (or
  *Marker is right*). The marker belongs to the clip, shared by every role and tier bound to it.
- **Warp preview** (under the 3D frame): *Speed up the first N s by k×, easing over r s* previews a retime of the clip
  (its start plays faster, easing back to its own speed so the swing does not hitch; the rest moves earlier). The whole
  app, playback included, then runs on the warped clip; picks stay on the clip's own clock. It changes no model:
  `retime_clip.py` bakes the same warp into the accepted export, which is then reinstalled.
- **Playback** with *Attack sound* on plays the monster's attack sound where the game would: at its delay on the game
  clock, at the chosen playback speed (pitch follows the speed).
- **3D view and billboard**: *In game* plays the attack as the engine does (fitted wind-up, HIT/RELEASE flash at the
  contact, the rest of the action, follow-through, crossfade to Standing; with *Walk after release* the legs walk
  under the follow-through once the action ends). The billboard shows the native frames on the same game clock. With
  *Sockets* on, the charge sockets show as dots: glow sockets in the charge colour, the release as a red ring. During
  the wind-up the charge glows there at its in-game size; after the release, a small slowed marker, tied to the
  release point by a line, leaves toward the party (the Party view camera), so it comes toward you.
- **Panel, 3 · Glow** (melee): optional glow sockets for the blow (a fist, a weapon, the eyes), charging during the
  wind-up and going out with sparks as it lands. A melee attack launches nothing, so there is no release, and the glow
  needs a *Colour* (ticking a glow socket sets an orange one to start from). Same sockets and `fx|<model>` pick as below.
- **Panel, 3 · Charge and release** (ranged attack and cast): the derived charge per tier (missile element or spell,
  with an approximate colour) and the model's sockets. Tick *Glow* for each socket the element charges at. Pick a
  *Release* socket only when the projectile leaves elsewhere; otherwise it leaves the one glow socket, or the middle
  of several. Usual setups:
  - one hand: glow and release on it;
  - both hands: glow on both, release between;
  - staff head, eye or mouth: one socket.

  To add a socket, use *Add socket: click the model*: the click lands on the bone that moves that spot most (or the
  held item's node), with the offset there. A `+ Socket_…` button adds one of the GLB's own socket nodes. *Glow scale*
  sizes the glow, and *Colour* overrides the derived colour. Named `effects` (a fire hand, a staff ring) stay as
  installed. The picks belong to the model (`fx|<model>` in `decisions.json`), and every tier gets them.
- **Timeline**: top row is the clip at its own speed with the tracked point's speed (blue) and horizontal reach
  (amber); S = peak speed (a cut lands about there), R = farthest reach, 95 = 95 % of the reach (a thrust lands about
  there). Bottom row is the attack in game: the attack sound's waveform from the start, the numbered billboard frames,
  the wind-up, the HIT/RELEASE line, the rest of the action, the follow-through and the earliest next attack (melee 0.9
  x recovery from the swing start, at least the action + 0.25 s; ranged and spells 0.9 x (recovery + action)).
- **Suggestions** are recomputed from both picks.

## Workflow

1. Resolve red *source* blockers first (the runtime clip differs from `assets_source`).
2. For each played role pick the billboard frame and the 3D frame. Picks save to `decisions.json`.
3. `apply_decisions.py --world <world>` prints the changes; with `--write` it writes the contact frames and sound delays
   to `sprite_attack_timing.yml`, and the markers and the charge sockets to `actors.yml` (markers: every role bound
   to the clip, every descriptor of the model; sockets: `animation.sockets` and the ranged attack's and cast's
   `glow`, `release`, `glow_scale` and `color` of every descriptor of the model, and the melee attack's `glow`, `glow_scale` and
   `color`). A clip with a warp preview keeps its installed marker until the warp is baked: run
   `retime_clip.py <accepted export> <out.glb> --clip <clip> --end N --speed k --ramp r --time <impact>`, install the
   output with `tools/install_model.py`, then pick the 3D frame again on the retimed clip and remove the preview. Rerun `build_review_data.py`, then check in game. Clip edits go to the creature project and are reinstalled
   with `tools/install_model.py`, with every retime moving its marker.
