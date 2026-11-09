# MM6 Cleric — native animation study

Source: `../mm6_cle/native/` (palette 675) and `../mm6_cle/aligned_2x/`; manifest `../mm6_cle/manifest.json`.
Every action is six frames at 125 ms (0.75 s); walk is six frames per view (0.75 s cycle). Frame scale 0.699997.
The staff is always in his LEFT hand (image right in the front view).

Monster data (`assets_dev/engine/data_tables/monster_data.txt` 490–492): all tiers have a ranged Air missile
(Acolyte 2D4, Cleric 2D4+4, Priest 2D4+8). Cleric of Baa casts Harm (20 %), Priest of Baa casts Flying Fist (30 %),
so a distinct cast clip is required. Speeds 160/180/200: below the run threshold (2.4 × scale ≈ 255), so the run
clip is a fallback only.

| Clip | Native keys | Intent |
|---|---|---|
| Standing (`clesta`) | one frame per view | upright; left arm out ~35° holding the staff vertically at the side, butt on the floor beside the left foot; right arm hangs relaxed |
| Walking (`clewal a–f`) | staff carried upright in the left fist, hand at ~elbow height in front of the hip, butt swinging just above the floor; right arm swings slightly; cloak trails | even, calm walk |
| Attack (`cleatt a–f`) | a: stand. b: staff swung down to level, the head (ring) in front of the chest pointing at the target, the shaft running back past the left hip; magic glow at the head. c: same, bigger glow (release). d: staff tilted back up to near vertical by the left shoulder, sparks fading at the head. e–f: back to stand | ranged attack fired from the staff head: socket at the ring |
| Cast | none native (same frames serve) | distinct clip for Harm / Flying Fist: staff raised overhead or forward, right palm forward; glow at the staff head |
| Hit (`clewin a–f`) | a: recoils, right hand up in front of the face, staff tilts out. b–c: right forearm raised across the brow (shielding the face), body turned, staff leaning out at ~20°. d: hand lowering to the chest. e–f: recover to stand | shielding recoil |
| Fidget (`clefi a–f`) | left arm straightens out sideways to ~shoulder height, presenting the staff upright, then returns | staff presentation |
| Death (`cledyi a–e`) | a: sways back. b: slumps, knees giving. c: topples FORWARD, cloak flying back. d–e: falls face down, staff still in hand | falls forward |
| Dead (`cledyi f`) | lying face down, arms out, staff beside the left hand | corpse |
