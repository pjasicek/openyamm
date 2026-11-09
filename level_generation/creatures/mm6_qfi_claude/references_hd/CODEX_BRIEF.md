# MM6 Demon Queen — HD modelling references (queen only)

## Scope

Image generation only, with your built-in image generation tool. Write only into
`level_generation/creatures/mm6_qfi_claude/references_hd/`. No builds, no other files, no Meshy.

This is a faithful high-definition reconstruction of an existing Might and Magic VI game creature, the Demon Queen
of the Hive, as a 3D modelling reference. It is NOT a new design. The original game sprite is tiny (the queen is about
125 pixels tall), so you supply the detail, but every design decision comes from the native frames.

## Inputs (attached, in this order)

1. `inputs/native_qfia0_full.png` — the original native standing frame. AUTHORITY for identity. The queen stands in a
   large rock alcove; the rock is NOT part of this reference (it is modelled separately). Transparent background.
2. `inputs/native_qfia0_queen_crop.png` — the same frame cropped to the queen (not enlarged). AUTHORITY.
3. `inputs/native_qdeb0_queen_crop.png` — native death start: both arms raised high and wide. AUTHORITY for arm
   length, the dark forearms/hands and the long claws.
4. `inputs/native_qatc0_queen_crop.png` — native attack: one arm raised, the other across the abdomen. AUTHORITY.
5. `inputs/native_qwib0_queen_crop.png` — native hit twist (three-quarter body). AUTHORITY for the abdomen depth.
6. `inputs/restored_x2_qfia0_queen_surface_only.png` — an AI-restored enlargement of frame 1. Use it for SURFACE
   MATERIAL ONLY (scale texture, breastplate sheen, abdomen ribs). It never sets the design.

In inputs 1–5 the rock, its shadows and the dark background are not part of the creature.

## Deliverables

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter (her right side turned slightly toward the camera), camera at chest height, slightly above |
| `01_front.png` | front |
| `02_back.png` | back |
| `03_left.png` | her LEFT side (her left arm nearest the camera; her face points to the image RIGHT) |
| `04_right.png` | her RIGHT side (her right arm nearest the camera; her face points to the image LEFT) |

Portrait 1024x1536, transparent background, no floor, no shadow, no text, one whole figure per image, generous
margins, nothing cropped (horn tips, claw tips and the abdomen tip fully inside the frame).

This run: generate `00_three_quarter.png` only, unless told otherwise. One corrective regeneration at most.

## The creature (from the native frames)

- **Build:** a slim, tall demon woman. Upper body human-like and upright: narrow waist, small shoulders, very long
  thin arms (the hands hang to mid-abdomen when the arms hang down). No legs at all.
- **Lower body:** from the waist down a long segmented insect/larva-like abdomen, as long as the head-and-torso
  together, about 18–22 broad transverse ribbed segments, pale silver-lavender with soft violet shading between the
  ribs, tapering gently to a rounded blunt end. In this reference the abdomen hangs straight down below the waist,
  then curves slightly forward at the bottom where it rests on the ground; the queen is balanced upright on it.
  A short band of red skin with a paler red-pink belly line joins the breastplate to the first rib.
- **Skin:** saturated crimson red with a fine darker red reptilian scale texture, on the face, neck, shoulders, upper
  arms and waist. The forearms darken through deep red to blue-black, and the hands are blue-black.
- **Hands:** five long slender digits per hand (four fingers and a thumb), each ending in a long thin curved pale
  ivory claw about as long as the finger itself. Spread the fingers apart (open hands, gaps between all digits).
- **Head:** narrow, elegant, demonic female face, red; violet glowing eyes; two small ivory fangs/tusks pointing down
  from the upper jaw at the mouth corners. Two very long straight ivory horns rising almost vertically from the top of
  the head, with a crown of shorter curved ivory spikes ringing the head (about 4–5 per side, pointing outward and
  up, framing the face like a ruff). No hair.
- **Armour:** a fitted lavender-silver metal breastplate shaped as two cups covering the chest, held by black leather
  shoulder straps studded with small silver studs; a black strap edge along the top. Under each cup hangs a short
  curved ivory hook/claw ornament (two or three per side, pointing down and inward). No other armour.
- **Pose:** relaxed A-pose for 3D modelling: arms about 35° out from vertical, elbows slightly bent, palms facing
  forward-down, fingers spread and clear of the body and abdomen. Head straight, looking forward.
- **Camera and light:** near-orthographic, even soft studio light from the front; no dramatic shadows, no rim light,
  no glow halo (the eyes may glow faintly).

## Do NOT

- No legs, feet, tail fins, wings, extra arms, weapons, jewellery, cape, hair or clothing beyond the breastplate.
- No rock, ground, alcove or background.
- Do not change the colours (red skin, blue-black hands, ivory horns/claws, lavender-silver armour and abdomen).
- Do not turn the abdomen into a snake tail with scales: it is a ribbed, segmented insect abdomen.
- Do not crop anything; do not add text, watermark or a floor shadow.

## Per-image checks (re-run before selecting)

- Identity against inputs 1–5: horn pair + spike crown, fangs, breastplate cups with studded straps and ivory hooks,
  red skin, dark forearms/hands, long claws, ribbed abdomen with a rounded end.
- Five digits per hand, all separated; claws pale; both hands fully visible.
- Upright A-pose, abdomen straight down then curving slightly forward at the ground.
- True alpha, 1024x1536, nothing cropped.

## Records

Write `generation_runs.json` (id, prompt, input file sha256, output path, selected flag, reason, superseded runs) and
`selected_views_review.png` (contact sheet of the selected views). Keep every tool return under `superseded/` if not
selected.
