# Codex brief: HD masters of the Nobles' weapons (Meshy Smart Topology inputs)

Generate one isolated HD master image per weapon with your built-in image generation tool. These are the inputs of
Meshy Smart Topology (image to untextured 3D mesh), so the whole volume of each weapon must read: its thickness,
every hole, the grip and the guard. Write only into this directory (`level_generation/creatures/hes_nobles_claude/
references_hd/weapons/`). No code, no builds.

## Inputs (attached in this order)

1. `fam_nobles.png`: the approved Nobles sheet. The Noble Fang held low in the right hand, the Noble Sidearm holstered
   at the left hip.
2. `boss_court_nobles.png`: the approved Court of Nobles sheet. Left, Lady Ssekh's twin crescent fangs; centre, Lord
   Mraal's two-handed phase cleaver (a broad crescent blade at the top of a long resin/bone haft and a smaller crescent
   blade at its butt); right, Lord Xith's two-handed storm rifle (bone ceramic shrouds, dark resin structure, a glowing
   orange coil barrel).
3. `item_weapons.png`: the item paintings of the same weapons side by side, left to right: Noble Fang, Noble Sidearm,
   Ssekh's Fang, Mraal's Cleaver, Storm Rifle.

The sheets are the design authority (silhouette, proportions, colours); the item paintings show construction detail.
They are references, not edit targets.

## Image contract (every weapon)

- Square 1536 × 1536 PNG, a **plain flat light grey background** (#c8c8c8), no shadow, no pedestal, no floor.
- Exactly ONE complete weapon, no hand, no character, no second copy, no labels, text, arrows or scale bars.
- Three-quarter view from slightly above, the weapon's long axis running diagonally from lower left to upper right,
  turned about 30° so its thickness and both its flat side and its edge read. The whole weapon inside the canvas with
  about 8 % margins.
- Painterly but solid late-1990s Might and Magic science-fantasy rendering with clear broad forms and even studio
  light. Materials: gilded chitin and **ivory bone-ceramic** plates, **black-violet resin** structure, fine gold edges,
  orange energy (edges, cells, coils) as solid orange material with only a restrained glow: no bloom, light streaks,
  sparks or beams that hide geometry. One physically connected rigid object, no floating parts.
- Grips thick enough for a large three-clawed demon hand, with clear space between grip and guard.
- No Earth firearm details (no magazines, no modern sights, no brand marks), no medieval European weapon shapes.

## The weapons (file names)

1. `noble_fang/00_three_quarter.png`: **Noble Fang**, a long one-handed curved fang blade about 75 cm overall: a
   slim ivory-gold blade curving like a tusk, its concave edge glowing orange along a narrow seam, a black-violet
   resin and bone ribbed hilt, a small swept bone guard with two short hooks, a pointed pommel. As image 1's held fang.
2. `noble_sidearm/00_three_quarter.png`: **Noble Sidearm**, a compact one-handed energy pistol about 35 cm long: ivory
   and gold ribbed shroud over a black-violet resin body, an orange cell, a round orange-lit muzzle, a swept bone grip
   with an open trigger guard. As image 3's second painting.
3. `ssekh_fang/00_three_quarter.png`: **Ssekh's crescent fang**, a one-handed duelling blade about 70 cm: a broad
   hooked crescent of ivory-gold chitin curving forward over the hand, the inner (concave) edge a bright orange-white
   glowing seam, black-violet resin ribs along its spine, a short bone-ringed grip with a hook guard. As the twin
   blades of image 2's left figure and image 3's third painting.
4. `phase_cleaver/00_three_quarter.png`: **Mraal's phase cleaver**, a heavy two-handed polearm about 2 m: a long dark
   resin haft with gold and bone bands, at its top a broad asymmetric crescent blade of ivory-gold chitin with dark
   resin cut-outs, two round orange energy nodes and an orange glowing cutting edge; at its butt a smaller curved
   crescent blade. As image 2's centre figure (its weapon, not its pose).
5. `storm_rifle/00_three_quarter.png`: **Xith's storm rifle**, a two-handed energy rifle about 1.5 m: a long body of
   ivory bone-ceramic shrouds with swept spiky fins, a dark black-violet resin frame, a bone stock, a pistol grip and a
   fore-grip for the second hand, and a long exposed **orange glowing coil barrel** ending in a pronged emitter. As
   image 2's right figure and image 3's fifth painting.

## Records

Save each image at its path above; record every generation in `generation_runs.json` here (asset, prompt, source
path, output, sha256, size). Review each image yourself against the contract (one object, background, full volume,
grip clearance, no glow hiding the form). At most one corrective regeneration per weapon. Then stop.
