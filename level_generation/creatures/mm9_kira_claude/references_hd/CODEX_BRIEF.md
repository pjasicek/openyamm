# Codex brief: HD reference views for MM9's Kira the Cold (mm9_kira_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_kira_claude/references_hd/`. Do not edit any other file, do not run
builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the ORIGINAL Might and
Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game character, an adult woman ruler (the Jarl of Thronheim) in medieval armour, a restoration of an existing 2002 game
character for a game mod.

## Inputs (attached, in order)
1. `mm9_views.png`: renders of the ORIGINAL low-poly model with its skin, five views left to right: front three-quarter from the
   figure's RIGHT, front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout,
   proportions and colour authority. The faceting, blur, low resolution and the T-pose arms are NOT the design.
2. `mm9_waist_views.png`: close renders of the cuirass, pauldrons, belt, mail skirt and arms, same five views.
3. `mm9_head_views.png`: close renders of head and shoulders, same five views. Face, hair, braid and earrings authority.
4. `mm9_leg_views.png`: close renders of the legs, greaves and boots, same five views.
5. `mm9_skin_x4.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY.
6. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns, 1024x1536 PORTRAIT)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the figure's RIGHT, camera at chest height slightly above (as input 1 view 1) |
| `01_front.png` | straight front |
| `02_back.png` | straight back |
| `03_left.png` | pure 90-degree profile of the figure's LEFT side: faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the figure's RIGHT side: faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01-04 with the selected 00 as an additional input so all views are
the SAME figure, SAME pose, SAME proportions and colours. At most ONE corrective regeneration per view; then select the better and note any residual fault.
Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs) and, after run 2,
a `selected_views_review.png` contact sheet.

## Common prompt content (adapt per view)
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX "Kira the Cold" from the supplied renders of its original 3D model,
as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional figure with semi-realistic game materials and sharp fine
detail (polished steel, riveted scale and chain mail, engraved gold trim, leather, individual hair strands). ONE complete figure from the crown to the soles,
centred, both hands inside the frame with margin, never cropped.

Identity (exactly the layout of inputs 1-4):
- A tall, athletic adult WOMAN about 1.78 m tall, ordinary female proportions, a slim waist, long legs. Not bulky, not a pin-up.
- HEAD: a handsome, stern woman about 35 with an oval face, defined cheekbones, a straight nose, clear ice-blue eyes WIDE OPEN under dark straight brows,
  a calm firm mouth with closed lips, a complete chin, a smooth slender neck, small silver stud earrings. Natural light skin.
- HAIR: very dark brown, long and straight. A side-swept fringe across the upper forehead parted near the centre, falling to the brow line at the
  sides, its lower edge ending cleanly on the skin (no pale band between fringe and forehead). The sides fall behind the ears; the back hangs as one long
  smooth mass down to the shoulder blades. ONE thin braid hangs in FRONT of the figure's RIGHT shoulder down to the chest, as in input 3.
- CUIRASS: a fitted steel breastplate covered in small overlapping silver scales, with TWO round domed steel breast cups each framed by a raised gold rim,
  a vertical gold-trimmed centre ridge, a round gold medallion with a BLUE gem at the base of the throat over a mail collar. The back is scale mail.
- PAULDRONS: layered rounded steel shoulder plates (two or three lames) edged with engraved gold, sitting on the shoulders and upper arms.
- BELT: a dark red-brown leather belt with small silver rivets and a round gold buckle set with a blue gem.
- SKIRT: below the belt a short chain-mail skirt to mid-thigh, a front panel of vertical narrow steel plates (tasset) over it, and under the mail hem a
  thin band of dark blue fur trim.
- ARMS: dark navy-blue cloth sleeves on the upper arms; from the elbow to the wrist steel-and-gold vambraces with an engraved gold Celtic knot pattern;
  brown leather gloves with FIVE separate fingers (four fingers and a thumb), relaxed, slightly curled, clear air between the fingers.
- LEGS: fitted dark brown leather leggings with a subtle tooled pattern.
- GREAVES: steel-and-gold shin guards with a round domed steel knee cop framed in gold and an engraved gold knot pattern down the shin, strapped over the
  leggings, as in input 4. At the back of the calves a band of black fur at the boot tops.
- BOOTS: brown leather boots to mid-calf, rounded toes, low heels.
- No shield, no sword, no scabbard, no cape, no helmet, no crown, no extra limbs, no exposed midriff, no cleavage.

Pose (identical in all views, the model's bind pose made symmetric): standing upright, feet apart about 30 cm, toes pointing forward and slightly out;
arms hanging down and away from the body about 35 degrees from vertical, elbows nearly straight, wrists straight, palms facing the thighs, clear air
between arms and armour. Exactly the same left and right (except the braid).

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: add weapons, a shield, a cloak or a helmet; change colours (silver steel, gold trim, navy-blue sleeves, brown leather, very dark brown hair);
crop any part; copy the blur or faceting; give her a modern look or make-up; make her younger than about 30; close or narrow her eyes.

Per-image checks (redo at most once): crown to soles in frame; both hands in frame; true alpha; five fingers on each visible hand; eyes open and blue;
fringe meets the forehead cleanly; one braid at the figure's right front; two round breast cups with gold rims; medallion with blue gem; layered
pauldrons; belt with gem buckle; mail skirt with front plate panel and blue fur hem; blue sleeves; Celtic-knot vambraces; greaves with knee cops; boots.
