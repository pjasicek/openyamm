# Posing Attack2 by hand

Open: `blender level_generation/creatures/mm6_gob_claude/posing/attack2_posing.blend` (Blender 5.x).

The file opens in Pose Mode, front orthographic view, frame 1, with the original sprite frame behind the goblin.
The six keys a–f (frames 1, 4, 7, 10, 13, 16) are pre-filled with the current attack as a draft; frame 19 is the
return to the ready pose (leave it).

## Layout (pro blocking setup)

- **Left view: locked front camera** with the original sprite behind the goblin. Judge silhouettes here and don't
  orbit it; if you do, press Numpad 0 (camera) to get back.
- **Right view: free perspective working view.** Pose here and orbit often to check depth.
- **Stepped interpolation:** the clip snaps from key to key (blocking). To preview smooth motion, hover the timeline,
  press A (select all keys), T → Bezier; T → Constant to go back. The ingest only reads the key poses.
- **Sword-tip motion path** (yellow `Tip` marker at the blade end): green line with frame numbers. While stepped it
  shows straight jumps between keys; switch to Bezier to see the swing arc, then Pose → Motion Paths →
  Update Paths after edits. Look for a smooth arc, bunched dots on the wind-up and a big gap on the cut.

## Navigate

| Action | Key |
|---|---|
| Orbit / pan / zoom | middle-mouse drag / Shift + middle-mouse / wheel |
| Front view (the sprite is only visible here) | Numpad 1 |
| Side / top view | Numpad 3 / Numpad 7 |
| Next / previous key | Up / Down arrow (or click a marker a–f in the timeline) |
| Play preview | Space |
| Undo | Ctrl+Z |

No numpad: Edit → Preferences → Input → *Emulate Numpad*, or click the axis gizmo at the top right of the view.

## Pose

| Handle | Colour | What it does |
|---|---|---|
| `CTRL_Hand_R` / `_L` | red / blue | G moves the hand (arm follows), R rotates hand and sword |
| `CTRL_Elbow_R` / `_L` | red / blue | G swings the elbow direction |
| `CTRL_Foot_R` / `_L`, `CTRL_Knee_*` | red / blue | G/R for feet, G for knee direction |
| Hips | green | G shifts or lowers the body, R tilts or turns the pelvis |
| Spine, Spine1, Spine2 | green | R bends/twists the torso (spread it over all three) |
| Neck, Head, Left/RightShoulder | green | R tilts the head, R on a shoulder shrugs it |

After G or R, press X/Y/Z to lock an axis; R twice rotates freely; Esc or right-click cancels.

Auto-keying (red record button) is on in *Replace* mode: changes made on a key frame (a–f) are stored in that
key; changes on any other frame are not recorded. Always stand on a marker frame before posing.

Focus on what you see against the sprite: sword-hand position and blade direction, elbows, torso lean and twist,
head, feet, the left hand. Ignore fingers, the exact grip, small intersections and wrist angles; the ingest
re-solves the fist, rebuilds the arms and checks every frame.

Save with Ctrl+S. No export is needed.

## Ingest (Claude)

`scripts/ingest_posed_clip.py export work/attack2_keys.json Attack2` on the posing file, then
`apply work/attack2_keys.json Attack2` on the rig master, `twist_bones.py bake`, audit, build, viewer.
