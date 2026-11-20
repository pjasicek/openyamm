# MM6 Demon Queen — native study and production plan

Source: `../mm6_qfi/native/` (24 unique frames, palette 834, logical canvas 454x341, pivot bottom centre, frame scale
2.0) and the restored set `../mm6_qfi/redo_2x/`. Monster 646 `zDemonQueen`: level 100, 1300 HP, speed 0
(stationary), melee 2D8+20 Physical with Drain SP, Incinerate (Fire, master, 40 %). One pre-placed actor in
`hive.blv` sector 77 at (3328, 26880, -2256), at the dead end of a narrow room, seen from the east (+x). One palette:
no tiers.

## Native actions (all front-only, one image for every direction)

| Action | Frames | Length | Observed |
|---|---|---|---|
| Standing / walk / fidget | qfia0–qfif0 | 1.125 s loop | upright, arms hanging beside the abdomen, long claws open; small breathing and head motion |
| Attack (= attack2, also the spell) | qata0–qatf0 | 1.125 s | (a) her right arm swings out wide and low; (b) the right arm rises high and back, the left hand comes across; (c) right hand up beside the head, left forearm across the abdomen; (d) she leans forward-right and drives the claw down and forward; (e) arms close in; (f) recover |
| Hit | qwia0–qwif0 | 1.125 s | the torso twists to one side, arms flail out and up, head turns; recovers |
| Death | qdea0–qdee0 | 0.94 s | arms flung out wide, then raised straight up in a V; the whole rock collapses (its top drops from 655 to about 425 units while the base stays) and she sinks into it until only her head and claws show at its foot |
| Dead | qdef0 | held | flattened rock dome; her head and hands at its base |

The rock alcove is part of the sprite; it does not exist in the map geometry.

## Anatomy (observed)

Red reptilian-scaled demon woman; forearms darken to blue-black hands; five long digits with long pale claws;
two long ivory horns and a ring of shorter spikes; violet eyes; two fangs; lavender-silver breastplate cups on black
studded straps with ivory hooks below the cups; no legs: a long ribbed silver-lavender insect abdomen from the waist,
ending in the rock's niche. The rock: a lumpy olive-tan stone mound, about 770 x 650 units, with a shallow niche
at the front centre.

## Production plan (user-approved route, 2026-10-13)

- Two parts in one actor GLB: the queen (Meshy Smart Topology from Codex HD masters, locally rigged) and the rock
  (Meshy multi-image-to-3D from Codex rock masters, rigid on its own leaf bone).
- Rig: source-frame upper body (humanoid set frames: pelvis, spine, neck, head, clavicles, arms, hands, fingers) on
  an abdomen chain; abdomen tip pinned in the niche; `Rock` leaf bone; palm sockets for Incinerate.
- Clips (G1, `review/g1/sheet_front.png`): Standing = Mixamo *Breathing Idle*; Attack = *Standing Melee Attack
  Downward* (one-arm overhead claw strike, matching frames b–d); Cast = *Standing 1H Magic Attack 01*; Hit =
  *Standing React Large From Front* (1.0 s); Death = the arms-overhead part of *Victory Idle* plus an authored sink
  and rock collapse; walking and fidget = Standing. Upper body only: the pelvis stays planted on the abdomen, which
  adds its own procedural sway.
- Engine: `actors.yml fixed_yaw_degrees` (added) keeps the rock against the wall; a `look` block turns her spine,
  neck and head toward the party.
