# MM7 Behemoth (mm7_m162): anim fix (2026-11-11)

Stream `anim` of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md), part 3. Before:
`work/before_anim/mm7_m162.glb` and `actors_mm7.yml`.

## Attack: the left claw struck into the floor

**Audit / floor audit:** at the blow (0.83–0.93 s) the left claw went 10–14 cm (16.6–20.8 world units) under the floor;
the October floor pass left it open because raising the root would hop the whole body
([floor README](../claude_shared/floor/README.md)). **Fix:** `scripts/limb_lift.py work/before_anim/mm7_m162.glb
export/mm7_m162.glb --clip Attack --joint B_L_UpperArm --part 'B_L_*'`: per key the left upper arm turns up about the
horizontal axis across its swing by the least angle that brings the lowest claw vertex to 5 mm, as a running maximum,
Gaussian-eased (sigma 1.5 keys); at most 9.4° over 16 keys around the blow. The strike, its timing and the impact
event are unchanged; only the left upper arm's Attack rotation sampler changed.

Result: Attack lowest point -13.8 cm -> -0.2 cm; floor audit `living` -16.6/-18.3/-20.8 -> -1.3/-1.5 world units (ok);
region bad shares unchanged (hand 3.5, arm 4.1 -> 4.2). Checks (`review/finish.txt`): winding 0; gait audits clean;
every-binding regression PASS; viewer check clean; arm and hand gate: hand-inside unchanged, no new deformation.
Sheet `review/attack_viewer_before_after.png` (top installed; the claw rides a little higher at the blow).
