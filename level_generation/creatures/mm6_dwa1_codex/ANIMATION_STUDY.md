# Dwarf motion study

Native authority: `../mm6_dwa1/native/` and `references/{standing,attack,hit,fidget,death_corpse,walk_0..4}.png`; descriptor/timing summary in source/native_summary.json. Right-hand short axe is mandatory. Native attack: ready low; raise axe in front/right; chamber beside head; drive down and forward; recover low across thighs. Feet take short alternating steps, trunk stays broad and upright. Open left hand balances. Native fidget spreads arms/looks around; death collapses to floor.

G1 reviewed on source mannequin front/side/three-quarter before modelling: Standard Idle, ArmedWalk, RelaxRunForward, Sword And Shield Slash (planted), UnarmedGetHitF1, ArmedDeath1, Standing Taunt Battlecry (planted). Axe to replace preview stand-in; motion judged by actual blade path, with signed edge and peak forward-facing tip speed checked after fitting. Retarget retains 30 fps. Own Standing eases into one-shots; attack/taunt retain roughly 20% leg motion using discrete IK steps. Hit uses the local 0.5-second source clip; native gameplay timing is not edited. Death/Dead hold on floor.

Inferences: three-dimensional hidden surfaces and independent finger anatomy are reconstruction choices. User choice: full production within batch boundary, 100 credits. No native gameplay timing changes.

Final corrections, exact clip durations, measured blow time and runtime boundary are recorded in README.md.


## Review round 2 replacement

The original G1 choices above are historical. Hit now uses the upright, in-place Mixamo `Hit Reaction (4).fbx`
(index id `mx/hit_reaction_3e95a7`), selected from the index and inspected on the dwarf front/side/three-quarter.
The source runs 0.433 seconds at its original 30 Hz; the adapted reaction returns to the creature's relaxed
Standing pose at 0.5 seconds, below the 0.75-second native hit window. The short pelvis movement is reduced to
20% and both feet stay planted; arm changes are adapted for the axe and checked against the tunic/body.
Source record, hash and decisions: [round 2 source](review/round2/hit_source.json). Current sheets: [Hit](review/Hit_sheet.jpg).


## Review round 3 locomotion correction

Retained ArmedWalk / RelaxRunForward upper-body actions and 0.8 s durations. Re-solved short legs to explicit
stride-synchronous contacts, with walking heel/toe clearance about 9.4 cm and 56–57° mid-swing knee flexion.
Run pelvis lowered to 0.673–0.704 m; lowest sole 3.7–8.4 mm at 48 Hz. No library purchase or source change.
New locomotion exports sample at 120 Hz for stable planted interpolation; accepted non-locomotion streams stay exact.
