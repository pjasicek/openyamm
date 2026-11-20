# Codex brief: MM9 PC10 head on an existing paperdoll body

Scope: image generation only, with your built-in image generation tool. Write only into `level_generation/ui/hud_inventory/mm9_pc_dolls/pc10`. No builds, no
other edits, no scripts that alter pixels.

## Inputs (attached in this order)

1. `donor.png`: TARGET. The head, neck and shoulders of an existing game paperdoll (a full-body figure in a fixed
   pose), on a transparent background, enlarged 4x from the game asset.
2. `identity.png`: the NEW character's face from its game portrait set, at several head angles: young half-orc woman with cool ashen grey-brown skin (a muted greyish brown, never green and never pinkish-white), no horns; short black hair shaved close at the sides with a short spiky black crest on top of the head and long thin blue-grey streaked strands falling from behind the ears down both sides of the neck; long pointed ears swept back from the sides of the head; one small gold hoop earring in each earlobe; heavy dark smoky shadow around pale green-grey eyes; strong brow, wide cheekbones, broad flat nose, very full dark plum lips, narrow chin, no tattoos.

## What to produce

One square image with exactly the framing of input 1: the same figure, but with the head of input 2's character.

- Replace the head: face, hair, ears, beard, horns and any headdress, hood or crown, and the neck above the collar.
  The new head has the same size, position, turn, tilt and gaze as the head in input 1, and joins the same neck at
  the same place, so it sits naturally on the unchanged body. Where input 1's hair, beard or hood falls onto the
  shoulders or chest, the new character's own hair, beard or hood takes that place, as long as it naturally is.
- Everything else (torso, clothing, arms) stays exactly as in input 1: same pose, colours, shading and edges. It is
  replaced by the original afterwards, so do not restyle it.
- Lighting and rendering of the head match input 1's body: the same pre-rendered game look, light from the same side,
  the same skin tone where the neck meets the body. Identity (hair shape and colour, face shape, eyes, brows, nose,
  mouth, skin tone) comes from input 2. Calm neutral expression, mouth closed.
- Hair stays close to the head: no larger silhouette than input 1's head plus the new character's hair needs.
- Genuinely transparent RGBA background (alpha 0) outside the figure; no backdrop, shadow or halo. Square output
  around 1024x1024. No text or marks.

## Records

- Copy the exact generated file, unmodified, to `raw.png`. If the result changed the body framing or has no real
  transparency, do ONE corrective regeneration and keep the first as `raw_rejected.png`.
- Write `generation.json`: exact prompt, input paths with sha256, output path, sha256, size, mode, and a short
  self-check against this brief.
