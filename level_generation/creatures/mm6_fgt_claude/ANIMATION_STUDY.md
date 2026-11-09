# MM6 Thug native motion and production clips

Source: `../mm6_fgt/inventory.json`, retained original-frame PNGs in `../mm6_fgt/native/` (inventory records historical BMP paths), palettes 733/734/735.
Family: FighterLeath A/B/C, IDs 538/539/540 (Thug/Ruffian/Brigand). Grounded human, right-hand mace, sheathed blade at left hip, scarf tail behind neck. No spells or projectile attacks in any tier. All tiers share shape and frame scale 0.799988; movement speeds 200/220/240.

The SFT loader multiplies raw frame lengths by 8 engine ticks, at 128 ticks/s: raw / 16 seconds. Standing/corpse hold is 0.125 s; walk, attack, hit, fidget 0.750 s; native death transition 0.625 s. Native standing/walking store five views plus mirrored rear directions; attack/hit/death/fidget reuse one front view (`Image1`). Observations from those views do not recover hidden depth.

## Native observations

- Standing: upright, feet apart, right hand carries the mace low in front; left hand hangs by the hip.
- Walk: six holds, ordinary upright alternating legs; equipment stays attached.
- Attack: six holds. Right wrist crosses up toward the left shoulder (a/b), drives a backhand sweep across the front (c/d), extends out to the right (e), and returns toward guard (f). Left arm balances. Mace, not a sword thrust.
- Hit: recoil, then return to guard. Keep final production Hit within native 0.75 s.
- Death: falls backward onto the back, releasing the mace above the right hand. Mace tumbles independently and rests by the right side in the corpse. Sheathed blade stays at the hip.
- Fidget: subtle upright shoulder/weight shift with low mace, repeated first native hold. Author this from Standing rather than use the library's sword-raising boost.
- Corpse: supine with mace at right side and feet toward observer.

## G1 selection

Reviewed source mannequin with a short mace stand-in from front, profile and three-quarter. See `review/g1_mace_*`, `review/g1_sweep_*`, `review/g1_backhand_*`. The named Mace attacks are overhead smashes; SwordAttackR3 has the more relevant crossed-hand backhand motion, so it is the selected Attack source. Its lower-body stance is an inference to adapt to our body, not a claim of exact native recovery.

Sources: local humanoid set (30 fps). Standing ArmedIdle (straighten the crouched legs for native posture); Walking ArmedWalk; Running ArmedRunForward if speed threshold needs it; Attack SwordAttackR3; Hit ArmedGetHitF1 shortened only as needed; Death ArmedKnockdown1 with authored mace release and corpse pose; Fidget authored native weight shift; Dead final held Death pose. Attack2 explicitly aliases Attack because the descriptors share the native sequence and no projectile exists. No Cast clip.

Preserve source time and frame rate. Measure weapon-head peak speed, add a short ready lead-in if required, and set the impact marker near native 0.75 s. Follow-through must fit each tier's recovery. Retain the torso-following scarf tail; solve mace fist and release; check every clip and interpolated frame after export. Native likeness, finger/hand stretch, rigid armour, shoulder/head clearance, mace/body contact and grounded feet are delivery gates.
