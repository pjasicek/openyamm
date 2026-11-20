# Codex brief: HD modelling references for the Glassback (Hesper)

Scope: image generation only. Write ONLY into `level_generation/creatures/hes_glassback_claude/references_hd/` and
`level_generation/creatures/hes_glassback_claude/references_head/`. Do not edit any other file, do not run builds, do
not call Meshy. Use your built-in image generation tool (Python/PIL only to check sizes and alpha and to make the
contact sheet).

This is a new creature of the Hesper world (an OpenYAMM world in the Might and Magic VI-VIII style), not an MM sprite:
its design authority is the user-approved concept sheet `design/kreegan_world/concepts/monsters/fam_glassbacks.png`.

## Inputs (attached in this order)

1. `references_hd/concept.png` — the APPROVED concept sheet. Right half: the large front three-quarter view (grey
   hide, full glass crest). Left column: a darker variant (top), a near-black variant with rust-red streaks (middle),
   a straight SIDE profile (bottom). Design, proportions, materials and colour authority: reproduce this exact
   creature faithfully, do not redesign. The dark background and the faint floor shadow are not part of the creature.
2. `references_hd/concept_side.png` — crop of the side profile (leg placement, tail, head, crest line).
3. (runs 2 and 3 only) the selected `references_hd/00_three_quarter_crest.png`.
4. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Why two kinds of body view

The glass crest (the black glass spines along the back) is modelled separately, like a prop, so the body is modelled
and textured WITHOUT it. We therefore need:

- `00_three_quarter_crest.png`: the faithful creature WITH its full crest (identity record and crest reference).
- `00_three_quarter.png`, `01_front.png`, `02_back.png`, `03_left.png`, `04_right.png`: the SAME creature, same pose,
  same proportions, with the glass crest REMOVED. Where the crest stood, the back continues as the same thick
  basalt-grey hide plates: a row of slightly raised, rounded plates along the spine from the neck to the tail base and
  over both shoulders (the sockets the spines grow from), with no glass, no spines, no teal light on the back.
- `crest.png`: the crest ALONE, exactly from the creature's left side (head end to image LEFT), as it sits on the back,
  with no body: the row of glossy black faceted glass spines and plates, tallest over the shoulders, shorter toward
  the tail and the neck, with the cold teal-green light inside the cracks and at the roots.

## Deliverables

Body masters in `references_hd/`, one creature each, the whole creature inside the frame with generous margins (tail,
beak and every foot included), unresized returns, **1536x1024 LANDSCAPE**, true transparent background, no floor, no
shadow, no text:

| File | View |
|---|---|
| `00_three_quarter_crest.png` | front three-quarter, body turned about 35° (we see the front and the creature's RIGHT side), camera at about shoulder height slightly above (we see a little of the back); WITH the crest |
| `00_three_quarter.png` | the same view and pose, crest removed (see above) |
| `01_front.png` | straight front, crest removed |
| `02_back.png` | straight back (rear), crest removed |
| `03_left.png` | the creature's LEFT side, a strict 90° profile: the head points to image LEFT; crest removed |
| `04_right.png` | the creature's RIGHT side, a strict 90° profile: the head points to image RIGHT; crest removed |
| `crest.png` | the crest alone from the left side (head end to image LEFT), 1536x1024, transparent |

Head turnaround in `references_head/`, the head and neck only (cut at the neck behind the jaw, no shoulders, no
crest), 1254x1254 (or the closest square size), transparent background, the same head as the body masters, beak
closed, eyes open: `01_front.png`, `00_three_quarter.png`, `02_profile.png` (the creature's RIGHT side, beak toward
image RIGHT), `03_back.png` (from behind: the back of the head and the neck).

Run 1: generate `00_three_quarter_crest.png`, check it, at most one corrective regeneration, then
`00_three_quarter.png` from it (crest removed, otherwise identical), check, at most one correction, then stop.
Run 2 (separate invocation): `01`-`04` and `crest.png`, with the selected 00 images as inputs. Run 3: the head
turnaround. At most one corrective regeneration per view.

## Prompt content (adapt per view)

TASK CONTEXT — GAME ASSET: a faithful high-definition 3D modelling reference of an approved creature concept, for an
MM6-8-style first-person RPG. Not a new design. Use case: 3D creature modelling reference sheet view.
Near-orthographic camera (no wide-angle distortion, no strong perspective), even soft neutral studio light (no
dramatic lighting, no rim light, no strong shadows: the light is baked into the texture), painterly-realistic game
materials like the concept, sharp fine detail, a credible solid three-dimensional animal.

Identity (from the concept): a heavy alien SIX-LEGGED grazer, low broad armadillo-and-rhino-like body, blunt and
crystalline, not a dinosaur, not a turtle, not a crocodile, not a real animal.
- BODY: long, low and broad, a rounded barrel-shaped back, the deepest point under the shoulders; covered in thick
  rounded overlapping plates of dark BASALT-GREY hide (mottled grey with darker cracks between the plates, matte,
  stony), large saddle plates over the shoulders and the hips, the plate skirt overhanging the upper legs a little.
  A short thick tapered tail, plated, held clear of the ground. PALE GREY belly of smaller soft scales, visible under
  the body and on the chest.
- HEAD: blunt, heavy, armoured, carried low and forward on a short thick neck; a broad armoured brow and cheek plates;
  SMALL deep-set dark eyes (one per side, brown-black with a faint highlight) under the brow; a dark grey-black
  hooked CRUSHING BEAK at the front (upper beak hooked over the lower), no teeth, no horns, no tusks.
- LEGS: exactly SIX legs, THREE PER SIDE: the front pair under the shoulders, the middle pair under the middle of the
  body, the hind pair under the hips. All six are thick, pillar-like, plated in the same grey hide, slightly bent,
  and end in broad feet whose toes are GLASS: four blunt, faceted, glossy BLACK glass claws/toe-caps per foot.
- CREST (`00_three_quarter_crest.png` and `crest.png` only): along the spine from behind the head to the tail base
  and spreading over both shoulders, a crest of GLOSSY BLACK volcanic glass spines and plates, faceted like obsidian
  crystals, the tallest over the shoulders, smaller toward the tail and the neck, a few small ones on the back of the
  head; cold TEAL-GREEN light glows from inside cracks in the glass and from the roots of the spines.

Pose (identical in all body views): standing square and level on flat ground, all six legs straight down under the
body with clear AIR between every pair of neighbouring legs (front, middle and hind legs well separated along the
body; in the side views all three near-side legs are visible as separate legs, the far-side legs partly visible
between them), feet flat, toes forward, the tail straight out behind and slightly down, clear of the ground, the head
level, looking forward, beak closed.

Do NOT: add extra or fewer legs (exactly six), horns, tusks, teeth, a saddle, armour, gear or riders; make it a turtle
shell or a dinosaur; change the colours (basalt-grey hide, pale grey belly, black glass toes, teal glow only in the
crest); draw the crest or any teal light in the crest-removed views; crop the tail, beak or feet; draw a floor,
shadow, background or text.

## Per-image checks (re-run before you select a view)

Whole creature inside the frame with margins; exactly six legs, three per side, every leg separated by air;
black glass toes on every foot; basalt-grey plated hide; pale grey belly; small deep-set eyes; hooked dark beak, closed;
short plated tail clear of the ground; transparent background; landscape 1536x1024. Crest-removed views: no glass
spines, no teal light, the raised spine plates instead. For 01-04 the same creature, pose, proportions and colours as
the primaries (inputs 3 and 4); side views: in `03_left` the head points to image LEFT, in `04_right` to image RIGHT,
strict profiles (one eye visible, legs of the far side partly hidden behind the near ones). Stop after one corrective
regeneration per view and record what remains.

## Records

`references_hd/generation_runs.json` and `references_head/generation_runs.json`: one entry per generation (id, view,
prompt, input paths with sha256, output path, selected flag, reason, superseded runs). Contact sheets
`references_hd/selected_views_review.png` (the seven body images) and `references_head/selected_views_review.png`.
