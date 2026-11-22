# Xeen Dragon Pharaoh (row 11919, D-56 Q5), 2026-11-21

Lane S sub-agent `xeen-s7-p5` (parent `xeen-s7`). The finale's officiant behind P5's dais and DD-15's quest giver: a
peaceful, placed-only, unkillable figure. Built from a shipped body, as D-56 asks first: the MM8 Lizardman Warrior
(`assets_source/worlds/mm8/models/mm8_m404.glb`, a long-snouted dragon head) copied into Xeen with a gold-and-lapis
skin, its head crest folded under a built striped nemes, and a built open book held in both hands. Judged against A4's
portrait `assets_dev/worlds/xeen/icons_x2/npc15453.png` (a golden dragon-headed pharaoh in a gold-and-blue striped
nemes) in renders and in game: it reads, so **no Meshy** was used (0 of the 30 allowed credits; no lease taken).

**State: installed** (`tools/install_model.py --world xeen`), seen in game (XD-21, through an overlay of the binding).
The binding is **not** merged (the parent owns `actors.yml`): the ready block is
[integration/actors.yml](integration/actors.yml), under A2's descriptor `Xeen Dragon Pharaoh` (it replaces A2's
stand-in, the MM8 lizardman villager). Not accepted by the user.

## Deliverables

| Item | Value |
|---|---|
| Body | `assets_source/worlds/xeen/models/xeen_pharaoh.glb` = `export/xeen_pharaoh.glb` (skin `pharaoh_a`; the source tiers `m404_a-c` stay in the copy) |
| Nemes | `assets_source/worlds/xeen/models/xeen_pharaoh_nemes.glb`, attachment on node `B_Head` |
| Book | `assets_source/worlds/xeen/models/xeen_pharaoh_book.glb`, attachment on node `B_L_Hand` |
| Binding | `integration/actors.yml` (scale 125, `yaw_offset` -90 deg, look 20/10 deg) |
| Specs | `specs/spec_pharaoh.json` (tier), `specs/body_skin.json`, `specs/body_leather.json` (D-10 body regions), `specs/nemes.json`, `specs/clips.json` |
| Review | `work/r/clips_sheet.png`, `work/r/clips2_sheet.png`, `work/r/stand0c_sheet.png` (workbench, the tier baked in), `review/ingame/` (XD-21) |
| Gates | `work/clip_gates.txt`, `work/gate_book.json`, `work/floor_audit.json`, `work/nemes_report.json` |

## Skin (`pharaoh_a`)

`xeen_tiers.py` copies `m404_a` and sets region 0 (the mantle, worn as a broad collar) to lapis `#2440a8`.
`add_region.py` adds two D-10 channels: 1 = every scale (the grey-blue body and head, the crest's red tips, the
mantle's red edge) as gold `#b8903c` (shadow `#5a3a12`, highlight `#f4dc8c`); 2 = the leather and the loincloth
(vest, bracers, belt, kilt; body atlas only, so the eyes keep their colour) as lapis `#2848a8` whose highlights turn
gold `#f0cc60` (the studs and folds). Claws, teeth and the collar's gold V stay. Ramp fit of the untouched tiers:
5.0/7.5/4.5 of 255 mean (body/LOD2/LOD3 atlases).

## Nemes and the crest

`build_nemes.py`: a bicubic hood through six rows of control points (front edge, side, back midline, mirrored) from
the brow to below the jaw, closed by a pole fan, with two lappets hanging in front of the shoulders and a short drape
behind the neck; a small gold uraeus on the brow. Texture 512 px: horizontal gold `#d8aa3a` and lapis `#1c3c9e` bands
with dark seams, a gold band along every edge, weave noise; metallic-roughness: gold threads metallic. 1,552 / 496 /
160 triangles (its own LOD chain). The attachment is the same mesh in `B_Head`'s space (the inverse bind matrix).

`squash_crest.py` folds the Lizardman's crest under the hood: every vertex of every colour and shadow LOD whose
dominant joint is `B_Head` or `B_Neck` and which lies outside the hood, seen from the head centre, moves along that
ray to 8 mm inside it (274 LOD0 vertices, up to 0.158 m). Bind-space positions only; nothing else changes.

## Clips (`author_clips.py`, 30 fps, no Blender)

The open book (0.34 x 0.24, pages 14 mm) is held at the chest in both hands, palms against its outer edges and
fingers behind it (the "edges" grip, finger yaw 30 deg: the palms-under grip needed 88 deg of forearm twist). Its pose
is fixed in the `B_Spine2` frame (tilted 38 deg toward the reader); both arms are solved per frame by a two-bone IK that
keeps each bone's own roll (minimal swing from the source clip), with the elbow pole in the chest frame; the hand's
twist about its axis is shared half with the forearm twist bone. Fingers: rest (open claw) plus 15 % of the source
grip. The book is an attachment of the left hand, so it follows the solved hand exactly.

| Clip | Length | What | Wrist bend / forearm twist max |
|---|---|---|---|
| Standing | 2.0 s loop | the Lizardman's idle body, reading; seam 0 | 26.7 / 32.0 deg |
| Fidget | 4.0 s | the right hand leaves the edge, hovers palm down over the right page, sweeps to the left page and back (a page turn); the head nods 12 deg; starts and ends on Standing frame 0 | 26.7 / 79.8 deg |
| Bless | 4.0 s | the right hand rises to shoulder height, palm out and forward, holds about 1.4 s, returns; the head lifts 8 deg; starts and ends on Standing frame 0. The cinematic's gesture (`clip: Bless`), also the attack roles | 55.0 / 36.8 deg |
| Walking | 0.8 s loop | the Lizardman's walk with the book held (he is `move: stand`; also the required `run` role) | 26.5 / 42.5 deg |
| Hit | 0.5 s | the Lizardman's hit at 35 % (the book held), raised onto the floor by `floor_fix.py --raise Hit` | 28.1 / 33.8 deg |
| Death / Dead | 1.4 / 0.13 s | the Lizardman's own; the arms ease from the book to the source arms in 0.15-0.6 s; the book stays in the left hand | 29.4 / 49.0 deg |

Dropped: Attack, Attack2, Jog, Sprint. Book gate (`gate_book.py`, the book's box against the posed LOD0 body, 41
samples per clip): no body vertex in it in Standing, Fidget, Bless, Walking; the page turn's claws touch the page
(0.4 mm, one vertex); Hit puts 4 loincloth vertices 7.7 mm into the book's underside for about 0.1 s (accepted).
Floor audit (`floor_audit.audit` on the block): standing 0.24, walking 0.19-0.24, living lowest -0.0, corpse +0.1
world units, no problems. Winding: 0 inverted closed parts on all three GLBs. `--headless-validate-actor-models` with
the block in an overlay: 313 descriptors on 83 models, 0 refused.

## Scale, binding

Scale 125: the nemes top stands 1.85 model m, so about 231 units, a head above Roland (`xeen_kni` at 106.7, about 190).
A2's descriptor height is 160 (collision and the inspect frame): A2 may raise it to about 230. Look nodes `B_Neck`,
`B_Head` limited to 20 deg yaw and 10 deg pitch, because the nemes is rigid on the head and its lower edge sits 2 cm
over the mantle. The attachments have no skin of their own and no variants: they draw their own materials.

## For A5 (P5) and A8 (DD-15)

- One model, one row (11919) for both maps. Standing reads the book; Fidget turns a page; `clip: Bless` (4.0 s,
  hand up at about 1.0-2.8 s) is the cinematic's gesture toward the couple, after an actor `face` cue.
- He needs about 70 units of clear radius for the book and the raised hand; the tail reaches 1.0 model m (125 units)
  behind his feet: keep it off walls (P5: behind the dais, clear on the shrine's paving).
- DD-15: send S any other pose it needs; the clips above are all there are.

## Meshy credits: 0 of 30

No job; no lease was taken.

## Rebuild

```sh
level_generation/creatures/xeen_pharaoh_claude/scripts/build.sh        # skin, nemes, crest, clips, floor fix, book, winding
python3 tools/install_model.py level_generation/creatures/xeen_pharaoh_claude/export/xeen_pharaoh.glb --world xeen
python3 tools/install_model.py level_generation/creatures/xeen_pharaoh_claude/export/xeen_pharaoh_nemes.glb --world xeen
python3 tools/install_model.py level_generation/creatures/xeen_pharaoh_claude/export/xeen_pharaoh_book.glb --world xeen
```

Review: `scripts/review_copy.py` (bakes the tier into a review copy for Blender), `scripts/posed_extras.py` (poses
the attachments at a clip time), `scripts/render_pose.py` + `scripts/sheet_row.py` (workbench views), the in-game
tours `work/ingame/tour*.yml` with an overlay mount (`--extra-mount`) holding a copy of `actors.yml` with this block
in place of the stand-in (`level_generation/decorations/xeen_p5props_claude/scripts/ingame_overlay.py` writes a fresh
one; `lua evt.PlayActorClip(27,[[Bless]],true)` plays a clip). The P5 shrine mock-up on X6 (hands, Cube, Scepter,
cake, bench and the Pharaoh) is in that project's `review/ingame/`.
Survey of shipped reptile bodies: `work/survey/` (MM6 lizard archer, MM7 troglodyte, MM8 serpentman, lizardman
villager and warrior, MM9 lizard-orc and troglodyte; MM9's DragonPharoah prop is a seated throne statue).

## Known limits

- The nemes is rigid on `B_Head`: when the head bends forward (Hit) its lower back edge dips into the mantle.
- Hit pushes the loincloth 7.7 mm into the book's underside for about 0.1 s.
- The Lizardman's long tail and digitigrade legs stay (a dragon); the portrait shows only the head.
- The hands are the Lizardman's claws; the raised Bless hand reads as an open claw, not a flat palm.
- Not looked at in P5 (not installed yet) or DD-15.
