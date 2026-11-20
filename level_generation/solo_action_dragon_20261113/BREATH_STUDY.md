# Solo dragon breath: look and spawn point study (2026-11-14)

How the solo MAW dragon's ranged breath should look from its own eyes, and where it should start. Study only:
nothing here is built. Frame strips, overlays and real engine stills are on the private study page
https://claude.ai/artifact/3yCmVDUdvxbQ7iu6xD2gTD (option A is real engine captures; B–E are composites painted onto
real frozen captures with the engine's own flame sprites).

Today (option A): at the press the solo dragon fires the party dragon breath at once: one always-hit Fire Bolt
(`fire_bolt` flight, `fire_small` impact) from the party ranged source, no windup, forelegs idle, a 0.035 rad kick.
Hard rule for every option: party games (MAW and Standard, party dragons included) stay exactly as they are.

## Options

| | Option | Rules | Forelegs | Work |
|---|---|---|---|---|
| A | Party Fire Bolt, no windup (now) | unchanged | idle | none |
| **B** | **Breath from below** (recommended) | unchanged | 0.25 s flare apart with the shot, never before it | small–medium, 1–2 days |
| C | Snout lunge | unchanged | drop apart about 0.4 s | medium, 3–5 days with the snout art |
| D | Gout cone | **rule change**: area damage in a 900 u, 13° cone | spread and braced | large, about a week |
| E | Held stream (Grandmaster "Searing Breath") | **rule change**: damage per tick, SP per second, about 3 s, cooldown | braced for the hold | largest, 1–2 weeks |

- **A:** reads as rising from between the forelegs (the source is at chest height) and never fills the view. But it
  is a wizard's bolt; the first 40–50 ms show nothing, so the bolt pops in at the bottom edge.
- **B:** solo-only presentation on the same projectile.
  - At the press a flame plume rises from the bottom centre between the forelegs. It reaches about a third of the
    screen height in 20 ms, stays below the crosshair and is gone by 150 ms.
  - The drawn bolt starts on the bottom-centre ray 150 u out (visible from frame 0 at about 130 px radius) and joins
    the real path by arrival.
  - Optional solo-only look: `dragon_fire` flight with a `fire_large` impact, via a recipe override passed only when
    `party.soloRun()`. `dragon_fire` is a slim bolt, so nothing grows or morphs.
  - Engine:
    - a small plume effect spawned in the solo breath branch beside the camera kick;
    - a per-projectile draw offset that decays with the travel fraction;
    - an optional recipe override;
    - an optional short foreleg clip.
- **C:** B plus a snout/jaw view-model piece that thrusts into the bottom of the view for about 0.3 s. Flame bursts at
  its tip and the drawn bolt starts there. It gives the clearest "from the mouth" read, and the bite lunge can share
  the piece. It needs new art (about 10–15 Meshy credits plus a rig) and hides the bottom centre (short targets) for a
  third of a second. The page uses a render of `mm8_m492`'s head as prototype art.
- **D:** looks most like breath and hits groups (Skyrim Fire Breath; Divinity OS2 Dragon's Blaze; BG3 Dragonborn
  breath). It is a rule and balance change, though: solo and party dragons would differ unless both change. It fills
  about 40 % of the screen at the ranges the breath is used most, and corridors fill at close range.
- **E:** the breath players imagine (Skyrim Flames, Elden Ring Dragonfire). It needs hold input, tick damage, SP
  drain, a turn-based answer, a continuous effect with aim lag, and a cap on opacity near the camera. It fits the
  Grandmaster special DRAGON.md already lists, not the basic breath.

## Spawn point

Paths of the bolt head (radius 25 u, measured from engine stills) at 4000 u/s, on captures with the goblin exactly 300,
720 and 1500 u away; 1600×900, 60° vertical view.

| Candidate | First seen | Radius then | Rise on screen at 300/720/1500 u | Collision |
|---|---|---|---|---|
| Party ranged source (now): party centre, 64 above the feet | 41–44 ms | 110–118 px | 236 / 379 / 433 px | Inside the party cylinder (r about 37), ignored by party projectiles; never starts in a wall |
| Eye / crosshair | 0 | fills the view | 0 (a dot that shrinks) | Inside the cylinder; sprite on the camera |
| Jaws, just below the crosshair (48 fwd, 6 below the eye) | 0 | 406 px | −152 / −6 / 48 px | Against a wall the bolt starts 11–27 u inside or past it |
| Bottom centre between the forelegs (60 fwd, 28 below) | 0 | 325 px | 110 / 256 / 310 px | Same wall problem, worse |
| Old Mouth node (32 u toward the bottom edge) | 0 | 703 px | 201 / 346 / 400 px | Bolt radius reaches 44 u forward: touches a wall the dragon stands against |
| Visual: jaw ray 150 u out, real from party source | 0 | 130 px | −152 / −6 / 48 px | As party; on screen it only shrinks under the crosshair ("from the head") |
| Visual: bottom-centre ray 150 u out, real from party source | 0 | 130 px | 101 / 246 / 300 px | As party; recommended |
| Visual: FPS tracer blend from the bottom ray over 300 u | 0 | 130 px | 101 / 246 / 300 px | As party; here the same as fraction-synced. From the jaw ray it would dip and come back |

Findings:
- Any source near the eye is drawn huge: 400–700 px at the jaws or the Mouth node, the whole view at the eye. This
  explains today's first report, a full-screen flame at close range.
- Near the eye the path runs almost along the view ray. At 720 u a bolt from the jaws moves 6 px on screen and just
  shrinks at the crosshair. This explains the second report: "from the head/crosshair".
- The party source already rises about 380 px from between the forelegs. Its only gap is the first ~45 ms before it
  clears the bottom edge.

**Decision proposed:** the real projectile stays at the party ranged source for every option (collision and party
parity unchanged). Only the drawing moves:

    drawn = real + (start − source) × (1 − travelled / total)

With this the drawn bolt lands where and when the real one does, misses and wall hits included.

Per option:
- **A:** party source.
- **B:** drawn from the bottom-centre ray at 150 u.
- **C:** drawn from the snout-tip ray at 150 u.
- **D:** hits from a cone at the party centre; drawn from the bottom-centre ray.
- **E:** hits from a capsule at the party centre; drawn from the bottom-centre ray.

## Recommendation

Build B for the solo basic breath: keep the rules, keep the real projectile and add solo-only presentation (plume,
bottom-ray visual offset, optional `dragon_fire` look, non-blocking foreleg flare). Consider C's snout later as an art
upgrade if the plume alone does not read as the mouth. Keep E as the Grandmaster special (a rule change). D is not
recommended for the basic breath.

Not visualised: the camera kick, sound, heat shimmer, live motion for B–E (stills over frozen frames) and the real
foreleg flare clip (the existing breath clip at 0.05 s stands in). The breath at 300 u is not real either: claws take
the attack there in game. Captures and scripts are in the session scratchpad (`breath_study/`), not in the repository.
