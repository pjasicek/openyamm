# Codex brief: HD modelling references for the Sabertooth (World of Xeen, Darkside)

Scope: image generation only. Write ONLY into `level_generation/creatures/xeen_saber_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

This is the **Sabertooth** of Might and Magic V: Darkside of Xeen (1993), rebuilt as a 3D creature for an MM6-8-style
first-person RPG. The original game drew it only from the FRONT (three-quarter front), as small low-resolution
sprites. Your job is a faithful high-definition reconstruction of that creature as a 3D modelling reference, not a
new design.

## Inputs (attached)

1. `native/sheet_codex.png`: three ORIGINAL frames, enlarged 4x with hard pixels, on flat grey (the grey is NOT part
   of the creature, nor is the dark ground shadow under it): standing (left), walking with a raised forepaw (middle),
   attacking with the mouth wide open and both forepaws thrown forward (right). Identity, proportion and colour
   authority.
2. (runs for 01-04 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Five masters in `references_hd/`, one creature each, the whole creature inside the frame with at least 60 px of
margin on every side (tail tip, ears and paws included), unresized returns, **1536x1024 LANDSCAPE**, true transparent
background, no floor, no ground shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter: the head toward image LEFT and turned about 35 degrees toward the camera (we see the face, the chest and the cat's LEFT flank), camera at shoulder height, slightly above |
| `01_front.png` | straight front: the face toward the camera, symmetric |
| `02_back.png` | straight back: the rump and the tail toward the camera |
| `03_left.png` | the cat's LEFT side: strict 90 degree profile, the head toward image LEFT |
| `04_right.png` | the cat's RIGHT side: strict 90 degree profile, the head toward image RIGHT |

`00_three_quarter`: like the original sprite: the head toward image LEFT, turned about 35 degrees toward the camera,
the body and tail extending toward image RIGHT behind it, so we see the face, the chest and the cat's LEFT flank.

Left and right: the cat's LEFT side is its own left (its left foreleg, left ear). In a strict profile with the head
toward image LEFT we see the cat's LEFT side; with the head toward image RIGHT, its RIGHT side.

Each run generates the view(s) it is told to; at most one corrective regeneration per view, then stop.

## Prompt content (adapt per view)

TASK CONTEXT - GAME ASSET: a faithful high-definition 3D modelling reference of the Sabertooth from the 1993 game
Might and Magic V: Darkside of Xeen, reconstructed from its original low-resolution sprite. Not a new design.
Use case: 3D creature modelling reference sheet view. Near-orthographic camera, even soft neutral studio light (no
dramatic lighting, no rim light, no strong shadows: the light is baked into the texture), painterly-realistic game
materials, sharp fine detail, a credible fully three-dimensional animal.

Identity (from the original frames): a large, lean, muscular sabre-toothed big cat, about 2.0 m long from nose to
rump and about 1.0 m high at the shoulder, built like a lioness or cougar with heavy powerful forelegs and shoulders
(no mane). FUR: short, smooth TAWNY OCHRE / warm tan-brown coat over the whole body, slightly darker along the spine
and in the muscle creases; a PALER cream-tan muzzle, chin, throat and belly; a light, slightly shaggy RUFF of longer
fur on the chest and the front of the neck (much less than a mane: it does not cover the head or shoulders). No
spots, no stripes. HEAD: a broad cat head with rounded-pointed upright ears (tawny, paler inside), large almond
GREEN eyes with black slit pupils, a DARK RED nose, white whiskers. MOUTH: closed lips with only a narrow gap between
the jaws; two very long curved SABRE FANGS from the upper jaw, ivory white, hanging down well below the chin (about
the length of the lower jaw), separated from the chin by clear air. LEGS: four strong legs with big round cat paws;
short golden-yellow claw tips just visible at the front of the toes. TAIL: long (about as long as the body), thin,
tawny, with a slightly darker tip, hanging down behind and curving gently up at the end, clear of the legs.

Pose (identical in all five views): standing square on all four legs on level ground, the legs straight and slightly
apart so each leg is visible on its own with air between the legs (no leg raised), the head level and looking
forward, the mouth only slightly open, the tail held away from the hind legs, curving down then gently up.

Do NOT: draw the grey background or the ground shadow; give it a mane, spots, stripes, armour, a saddle or extra
limbs; open the mouth wide or snarl; hide the fangs; make it cute, a cartoon or a house cat; change the colours (tawny
ochre coat, pale muzzle and belly, green eyes, dark red nose, ivory fangs, golden claw tips); crop the tail, ears or
paws; draw a floor, a ground shadow, a background or text.

## Per-image checks (re-run before you select a view)

Whole cat inside the frame with margins (tail tip included); lean, muscular, lioness-like body, longer than tall;
tawny ochre coat with paler muzzle and belly, light chest ruff, no mane; green eyes, dark red nose; two long ivory
sabre fangs below the chin with air between fangs and chin; four separate straight legs, all four paws on one level;
long thin tail clear of the legs; transparent background; landscape 1536x1024; for 01-04 the same cat, pose,
proportions and colours as the primary; side views: in `03_left` the head points to image LEFT, in `04_right` to
image RIGHT; the front view symmetric.

## Records

Run 1 (`00`): `references_hd/generation_runs.json`, one entry per generation (id, view, prompt, input paths with
sha256, output path, selected flag, reason, superseded runs).
Runs for 01-04 (one invocation per view, possibly at the same time): write your entry to
`references_hd/generation_run_<view>.json` (same fields), NOT to `generation_runs.json` (Claude merges them).

## Notes for the 01-04 runs (after run 1)

Claude accepted `00_three_quarter.png` (the corrected render of run 1) as the primary: lean tawny-ochre lioness-like
body, pale cream muzzle, chest ruff and belly, green eyes, dark red nose, mouth slightly open, two long ivory sabre
fangs hanging below the chin, four straight separate legs with big round paws and golden claw tips, a long thin tail
hanging down and curling up at the end. In 01-04 keep exactly this cat: same proportions, colours, fur, fangs, paws
and tail. Each invocation generates ONE view only:
- `01_front`: straight on the face, symmetric, both forelegs straight and apart, the hind legs visible between and
  behind them, both fangs below the chin; the tail may show behind one hind leg.
- `02_back`: straight from behind: the rump, the tail hanging down the middle and curling up at the end, all four legs
  visible, the ears and the top of the head above the shoulders.
- `03_left`: strict profile at body height, the head toward image LEFT (the cat's left side), all four legs visible
  (near legs in front of the far legs, slightly apart), both fangs below the chin, the whole tail.
- `04_right`: strict profile at body height, the head toward image RIGHT (the cat's right side), otherwise as 03.
Keep at least 60 px between the cat and every edge.
