# MM8 Dark Elf Warrior motion

Native authority: source/native_inventory.json, original m432 BMPs (standing samples hash-verified),
current m433/m434/m435 sprite tables. Descriptors 25/26/27; palettes 433/434/435;
body scale 1.299988, speed 240/260/280. Five stored views; views 5-7 mirror 3-1.
160 stored frames. Attack2 aliases Attack. Standing/corpse hold 0.125s; walk/attack 1s;
hit/fidget 0.625s; death 0.75s, starting with two hit poses before collapse.
All three tiers also cast a spell and need a release socket. Their native cast uses attack art.

Native attack: both hands hold the long straight sword. Raise it at the right side, cross the upper body,
cut forward/down through the target, recover into raised guard. Feet remain close to the original stance.
Death releases the sword onto the floor; this is a separate required prop track.

G1: eleven candidate motions reviewed on the humanoid-set mannequin in front, left and three-quarter
(review/g1/*_contact.jpg). Selected source paths/hashes are in source/selected_clips.json.
Mixamo Great Sword Slash (4) has the useful raised two-handed wind-up and downward forward blow;
Great Sword Attack is rejected from its hilt-strike semantics. Set attacks 6/7 leave the off-hand away
from the grip and are rejected. LowSlash turns/travels too far. DownSlash is a secondary alternate.
Mixamo Great Sword Idle (4), Walk, Run preserve a useful two-handed guard; Run has true running leg paths.
Spell Cast releases the off-hand forward while the right retains the sword, fitting the three tier spells.
Two Handed Sword Death releases the off-hand and falls backward; match the native final corpse after inspection.
The initial crouched Hit candidate is rejected; preview the upright Great Sword Impact (3) before final selection.

Required production adaptation: reduce the mannequin's forward hunch to the native upright posture;
fit both hands to this body's handle; level toe/foot pitch; retain source running paths; ground the soles.
Add a measured ready lead-in to Attack/Cast so release is near the native 1-second action without slowing
mocap motion. Gameplay timing remains unchanged. Hit <=0.625s. Blend one-shots from/to Standing,
Death to a held Dead pose, and author a small native shoulder/weight fidget.
The source mannequin is a motion selection tool, not a final deformation or grip approval.
