# Codex brief: HD HEAD turnaround for the MM9 Winged Mutant (harpy) (mm9_wingedmutant_claude, rework 2026-10-30)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_wingedmutant_claude/references_head/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are
no native sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders of that model.

Why: the user rejected the face of the first 3D model (a long pointed wedge chin running into the throat, an open
slab mouth with a tongue-like plate, a flat profile, shapeless eye sockets). These head views are used twice: a
head-only 3D model is built from `00_three_quarter.png`, and all four views paint the head texture. So the SHAPE of
the face (jaw line, chin, lips, eye sockets, nose, cheekbones) must be clear and readable in every view.

## Inputs (attached, in order)
1. `references_head/mm9_head_views.png` — close renders of the ORIGINAL Might and Magic IX model's head with its skin
   (front, three-quarter, left profile): FACE, HAIR AND COLOUR AUTHORITY. Its low resolution, faceting, blur and dark
   shading are NOT the design. Flat grey is background.
2. `references_head/input_body_front_head_crop.png` — head crop of the approved HD body master (front): the HD look
   of THIS creature (face, colours, hair). The heads you make must be THIS face.
3. `references_head/input_body_q34_head_crop.png` — head crop of the approved HD body master (three-quarter).
4. `references_hd/mm9_skin_tier1_x4.png` — the original skin texture enlarged 4x (face at the top left), SURFACE
   MATERIAL AND COLOUR ONLY.

## Deliverables (true transparent RGBA background, 1254x1254 or the closest supported square size, unresized)
| File | View |
|---|---|
| `01_front.png` | perfectly straight FRONT bust, face and shoulders square to the camera (generate FIRST) |
| `00_three_quarter.png` | front three-quarter bust: the creature's RIGHT side toward the camera, so the face looks toward IMAGE RIGHT (as input 3), camera at eye level |
| `02_profile.png` | pure 90-degree profile of the creature's LEFT side: the face points to IMAGE LEFT |
| `03_back.png` | straight BACK of the head, hair and shoulders |

Generate 01 first; then make 00, 02 and 03 with your selected 01 as an extra input so all four are the SAME head.
At most ONE corrective regeneration per view; keep raw returns in `raw/`. Write `generation_runs.json` (id, view,
prompt, inputs with sha256, output path, selected flag, reason, superseded runs, size, alpha extrema) and a
`selected_views_review.png` contact sheet of the four selected views.

## Common prompt content
TASK CONTEXT — GAME ASSET: faithful high-definition 3D modelling and TEXTURING head reference of an EXISTING Might and
Magic IX monster, a harpy (inputs 1-3). Not a new design. Output ONE bust only: the whole head with all hair, the
neck, and the top of the feathered shoulders, centred with generous margins, never cropped (all hair inside the
frame). Near-orthographic camera at eye level, the head held LEVEL and upright (not tilted down), even soft neutral
studio lighting, no dramatic light, no rim light, no strong shadows (the image is baked into a texture). Sharp fine
detail: fine skin scales on the forehead and temples, brows, lashes, lips, teeth, hair strands, small feathers.

## Identity
A fierce harpy woman: a beautiful but cruel FEMALE face with pale cyan / blue-grey skin, patches of fine darker
scales on the forehead, temples and cheekbones (as inputs 1-2), angry brows drawn down, narrow almond eyes with
amber-yellow irises, a straight nose, high cheekbones, slightly hollow cheeks.
- Mouth: full dark blue-black lips, parted in a snarl only a little (a narrow gap), showing the upper and lower
  teeth with two small upper fangs, as in input 1. The lips are clearly modelled with a defined upper lip line and a
  rounded lower lip. NO tongue showing, no wide-open mouth, no dark slab.
- Chin and jaw: a SHORT, slightly pointed feminine chin directly below the lower lip, and a clear, clean jaw line
  from the chin to below the ears, so the face is clearly separated from the throat. The underside of the jaw and the
  throat are visible in the profile; the throat is a normal slim neck (not a continuation of the chin).
- Eyes: set in real eye sockets under a defined brow ridge (visible depth in the three-quarter and profile views).
- Hair: long, thick, glossy BLACK hair with a blue sheen in heavy rope-like locks, swept straight back from the
  forehead and the temples and falling behind the head and down to the shoulders on both sides. The forehead, the
  temples, the cheeks and the whole jaw line stay free of hair, so the profile shows the complete face, ear area and
  jaw line. No ears showing (covered by the hair behind the temples). The hair is the same on both sides (symmetric).
- Neck and shoulders: the neck below the jaw is the same pale blue-grey skin, then dark indigo / navy-blue small
  feathers start at the base of the neck and cover the shoulders (as inputs 2-3). No arms, no wings in the frame.

Per-image checks (re-run before selecting): same face as inputs 2-3; the requested view (02 faces IMAGE LEFT, 00 looks
toward IMAGE RIGHT); head level; short defined chin and visible jaw line; lips only slightly parted with teeth, no
tongue; whole head and hair inside the frame; true transparent background; square.

## Do NOT
- change the face, hair, skin or eye colours; add horns, ears, a crown, jewellery, armour, arms or wings; open the
  mouth wide; show a tongue; let hair cover the face or jaw; stylise as a cartoon; add text, a floor, a background
  or a shadow; crop.
