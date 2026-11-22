# Codex brief: HD modelling references for the Sand Worm (World of Xeen)

Scope: image generation only. Write ONLY into `level_generation/creatures/xeen_sandworm_claude/references_hd/`. Do
not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

This is the **Sand Worm** of Might and Magic IV: Clouds of Xeen (1992), rebuilt as a 3D creature for an MM6-8-style
first-person RPG. The original game drew it only from the FRONT, as small low-resolution sprites. Your job is a
faithful high-definition reconstruction of that creature as a 3D modelling reference, not a new design.

## Inputs (attached)

1. `native/sheet_codex.png`: four ORIGINAL frames, enlarged 4x with hard pixels, on flat grey (the grey is NOT part
   of the creature): (a) the worm standing upright out of the sand, its round maw on top; (b) the worm half sunk;
   (c, d) the attack: the worm bent forward over its own coils, the round maw facing the viewer. Identity, proportion
   and colour authority. The flying pink-brown rock shards are an effect: leave them out.
2. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Five masters in `references_hd/`, one creature each, the whole creature inside the frame with at least 80 px of
margin on every side, unresized returns, **1024x1536 PORTRAIT**, true transparent background, no floor plane, no
ground shadow, no text, no flying rock shards:

| File | View | Sand mound |
|---|---|---|
| `00_three_quarter.png` | front three-quarter: the worm's front turned about 35 degrees toward image RIGHT, camera at mid height, a little above the top so the maw is seen | **NO mound**: the worm alone, its lowest ring resting on an invisible flat ground |
| `01_front.png` | straight front (the view of the original sprite), symmetric | WITH the low sand mound around the base |
| `02_back.png` | straight back | WITH the mound |
| `03_left.png` | the worm's LEFT side: strict 90 degree profile; the maw tilt (see Pose) leans toward image LEFT | WITH the mound |
| `04_right.png` | the worm's RIGHT side: strict 90 degree profile; the maw tilt leans toward image RIGHT | WITH the mound |

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run 2 (separate invocation): `01`-`04` with the selected `00` as input 2. At most one corrective regeneration per view.

## Prompt content (adapt per view)

TASK CONTEXT - GAME ASSET: a faithful high-definition 3D modelling reference of the Sand Worm from the 1992 game
Might and Magic IV: Clouds of Xeen, reconstructed from its original low-resolution sprite. Not a new design.
Use case: 3D creature modelling reference sheet view. Near-orthographic camera, even soft neutral studio light (no
dramatic lighting, no rim light, no strong shadows: the light is baked into the texture), painterly-realistic game
materials, sharp fine detail, a credible fully three-dimensional creature.

Identity (from the original frames): a GIANT desert WORM standing straight UPRIGHT like a column, about 1.15 m tall
and 0.6 m in diameter. BODY: SIX thick, rounded, bulging RINGS stacked straight on top of each other like a column of
fat rounded tyres, every ring the same width (the top one a little more domed), with deep dark creases between the
rings. SKIN: orange-ochre (warm orange, darker burnt-orange in the creases), rough and PEBBLY: covered in small
irregular lighter-orange stony plates and pebbles separated by dark cracks, like cracked sun-baked rock. SPIKES: on
every ring a row of about EIGHT short, sharp, conical THORNS spaced evenly around its widest point, steel-grey with a
darker base and a pale highlight, pointing outward and curving slightly upward, each about a third as long as a ring
is high. MAW (on the TOP of the worm): one big round mouth filling most of the top ring's upper face: an outer lip of
the orange skin, then a ring of bright RED gums with darker red concentric bands, about TWELVE curved grey-white
pointed FANGS set around the gums and pointing INWARD toward the centre, and a deep BLACK gullet hole in the middle.
No eyes, no face, no limbs, no tail.

Pose (identical in all five views): the worm stands perfectly upright and straight, the rings stacked vertically;
the top ring with the maw is tilted about 25 degrees toward the worm's FRONT, so the open round maw faces up and
slightly forward; the maw is OPEN (gums, fangs and black gullet clearly visible).

Sand mound (views 01-04 ONLY, never in 00): the worm rises out of a LOW, broad mound of pale tan-ochre desert SAND
mixed with a few broken angular ROCK CHUNKS (pinkish-brown stone slabs and pebbles lying on and around the mound).
The mound is about 1.7 times as wide as the worm and only as high as half a ring (it covers just the lower half of
the lowest ring); it is a smooth irregular heap with soft cracks, flat underneath, lying on an invisible flat ground.

Do NOT: draw the flying rock shards, dust clouds or an environment; add eyes, a face, legs, tentacles, a tail, armour
or extra mouths; bend, coil or curl the body; close the maw; change the colours (the skin stays orange-ochre, the
spikes grey steel, the gums red, the fangs grey-white); make it cute or a cartoon; crop the top or the base; draw a
floor plane, a ground shadow, a background or text.

## Per-image checks (re-run before you select a view)

Whole worm inside the frame with at least 80 px margins; six stacked rounded rings of equal width, upright and
straight; pebbly cracked orange-ochre skin; about eight grey conical spikes per ring; the open round maw on top,
tilted toward the front, with red gums, inward grey-white fangs and a black centre; no eyes or limbs; transparent
background; portrait 1024x1536; `00` has NO sand mound; `01`-`04` have the low sand-and-rock mound around the base
and otherwise the same worm, pose, proportions, ring count and colours as the primary; the front view symmetric;
in `03_left` the maw tilt leans toward image LEFT, in `04_right` toward image RIGHT; in `02_back` the maw tilt leans
away from the camera (the maw's back rim faces the camera).

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Contact sheet `references_hd/selected_views_review.png` (the five
selected views), written in run 2.

## Run 2 notes (after run 1)

Claude accepted `00_three_quarter.png` (the second render of run 1) as the primary: six thick rounded rings stacked
straight up, pebbly cracked orange-ochre skin, curved grey steel thorns on every ring, the top ring domed with a big
round open maw (red gums, twelve curved grey-white fangs pointing inward, black gullet) tilted toward the worm's
front. In 01-04 keep exactly this worm: the same proportions, ring count, spike shape and spacing, skin and maw; ADD
the low sand-and-rock mound around the base (see "Sand mound"): broad (about 1.7 times the worm's width), low (it
covers only the lower half of the lowest ring), pale tan-ochre sand with soft cracks, and a few broken angular
pinkish-brown rock slabs and pebbles lying on it and around its edge. Straight views at mid height (camera level with
the middle of the worm, very slightly above so the top of the maw rim is visible in 01). `01_front`: the maw faces the
camera, tilted up (we see into it from slightly below its axis), the worm symmetric. `02_back`: the back of the worm,
the maw's rim seen from behind leaning away. Side views: strict 90 degree profiles, the maw tilt leaning toward image
LEFT in `03_left` and toward image RIGHT in `04_right`. No glow, haze or coloured halo around the worm: a clean cutout
on true transparency (the primary has a faint orange halo in its transparent margin: do not repeat it).

Each run-2 worker generates ONE view only (named in its prompt). Write its record to
`references_hd/generation_runs_<view>.json` (same fields as generation_runs.json), not to generation_runs.json, and do
not write the contact sheet (Claude makes it).
