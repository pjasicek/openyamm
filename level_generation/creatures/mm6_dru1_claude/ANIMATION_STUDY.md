# MM6 Druidess native motion and production clips

Source: `../mm6_dru1/` (native frames `native/`, sheets `references/`), descriptors 517/518/519 (Druid / Great
Druid / Grand Druid), palettes 722 (A green), 723 (B rose), 194 (C blue). All tiers share shape, sprites and frame
scale; only the hood and cloak change colour. Movement speeds 160/180/200. Ranged attackers (missile Fire / Water /
Earth, "Miss" column) with spells Harm (A), Deadly Swarm (B), Fireball (C): every tier needs Attack (missile) and a
distinct Cast clip. The native sprite reuses one sequence (`dru1ata`) for melee, missile and spell.

## Native observations

- **Standing:** upright, feet together, arms hanging relaxed at the sides, hood up, cloak closed behind the body.
- **Walk:** six holds, upright, short steps, arms swing a little in front of the open cloak.
- **Attack / spell (`ata`, six holds):** (a) both hands brought together in front of the belt, spell threads between
  them; (b) a glowing orb between the palms at chest height; (c, d) the RIGHT hand raised high above the shoulder,
  the spell gathered in the raised palm, the left arm low; (e) the right hand flung forward and up (the release);
  (f) the right hand back down by the hip, last sparks.
- **Hit (`wi`):** recoil with both hands pulled up to the head / face (c-d hands over the brow), then lowered.
- **Fidget (`fi`):** the right hand rises to the side of the head / hood and goes back down.
- **Death (`dy`):** hands to the head, sinks to her knees, slumps forward, lies face down with the cloak over her.
- **Corpse:** prone, cloak spread over the body, feet toward the viewer.

## G1 selection (local humanoid set, previews in `review/g1_*_sheet.png`)

| Role | Source clip | Why | Adaptation |
|---|---|---|---|
| Standing | Relax Idle | upright relaxed idle, matches the native stand | none |
| Walking | Relax Walk Female | upright feminine walk, arms low | check stride against speed 160-200 |
| Running | (Walking) | speeds 160-200 stay under the run threshold (check with the final scale) | bind run to the walk |
| Attack (missile) | Unarmed Cast R Buff 2 | low gathering of both hands, right hand raised high overhead, flung forward: the native ata sequence | legs/pelvis planted in the Standing stance (the Unarmed set crouches in a boxing stance); arms eased in from Standing |
| Cast (spells) | Unarmed Cast Dual Attack 2 | both hands gather, then push forward at chest height with the palms together (native frame b, orb between the palms) | same stance plant and ease-in; glow between the palms |
| Hit | Unarmed Get Hit F1 | short recoil, arms pulled in | stance plant; keep within the native 0.75 s |
| Death | Relax Laydown LayDown | kneels, then lies face down: the native death | none; cloak flattened on the floor at the end |
| Fidget | Relax Drink 1 | right hand rises to the head and back: the native fidget | fingers keep the open rest pose (no cup) |

ROM (`work/rom.json`, `scripts/rom_extract.py`): elbow flexion up to 120 (attack/cast) and 129-133 (death);
upper-arm twist up to 90 (attack), 71 (fidget), 61 (death); clavicle swing up to 41 (hit); wrist bend up to 87
(cast), 61 (death). The source forearm never twists (all roll in the hand bone) - twist bones as in the barbarian.

## Cloak

Full-length open cloak hanging behind the arms, hood up. Follow the thief/cleric cloak route
(`mm6_thf_claude/scripts/cloak_rig.py`, `cloak_sim.py`): dense chains on the cloak mid-surface, hood on Head, verlet
simulation baked per clip with one-sided capsule collisions, flattened onto the floor in the death.
