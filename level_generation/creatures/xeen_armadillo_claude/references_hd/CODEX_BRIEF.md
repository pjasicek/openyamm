# Codex brief: HD modelling references for the Armadillo (World of Xeen: Darkside)

Scope: image generation only. Write ONLY into `level_generation/creatures/xeen_armadillo_claude/references_hd/`. Do
not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

This is the **Armadillo** of Might and Magic V: Darkside of Xeen (1993), rebuilt as a 3D creature for an MM6-8-style
first-person RPG. The original game drew it only from the FRONT (a front three-quarter: the face toward the viewer,
the body and tail going back to the right), as small low-resolution sprites. Your job is a faithful high-definition
reconstruction of that creature as a 3D modelling reference, not a new design.

## Inputs (attached)

1. `native/sheet_codex.png`: three ORIGINAL frames, enlarged 4x with hard pixels, on flat grey (NOT part of the
   creature): standing (left), standing with its forked green tongue flicking out (middle), and the start of its
   attack with the front claws raised and the tail lifted (right). Identity, proportion and colour authority.
2. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Five masters in `references_hd/`, one creature each, the whole creature (tail and tail ball included) inside the
frame with at least 60 px of margin on every side, unresized returns, **1536x1024 LANDSCAPE**, true transparent
background, no floor, no ground shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter: the head toward image RIGHT and turned about 35 degrees toward the camera (we see the face and the armadillo's LEFT flank, the tail going back to image left), camera a little above the back |
| `01_front.png` | straight front: the face toward the camera, symmetric (the tail hidden behind the body except the ball maybe) |
| `02_back.png` | straight back (the rump and the tail toward the camera) |
| `03_left.png` | the armadillo's LEFT side: strict 90 degree profile, the head toward image LEFT, the tail to image right |
| `04_right.png` | the armadillo's RIGHT side: strict 90 degree profile, the head toward image RIGHT, the tail to image left |

Left and right: the creature's LEFT side is the side of its left legs. In a strict profile with the head toward image
LEFT we see its left side.

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run 2 (separate invocation): `01`-`04` with the selected `00` as input 2. At most one corrective regeneration per view.

## Prompt content (adapt per view)

TASK CONTEXT - GAME ASSET: a faithful high-definition 3D modelling reference of the giant red Armadillo from the 1993
game Might and Magic V: Darkside of Xeen, reconstructed from its original low-resolution front sprite. Not a new design.
Use case: 3D creature modelling reference sheet view. Near-orthographic camera, even soft neutral studio light (no
dramatic lighting, no rim light, no strong shadows: the light is baked into the texture), painterly-realistic game
materials, sharp fine detail, a credible fully three-dimensional animal.

Identity (from the original frames): a GIANT armoured beast like a heavy armadillo crossed with a pangolin, about
1.8 m from snout to rump plus a 1.5 m tail, only about 0.8 m high at the top of its shell and about 1.3 m wide: low,
heavy, crouched, much broader and longer than tall. EVERYTHING is in RED armour.

- SHELL: a broad, low, domed carapace made of CONCENTRIC OVERLAPPING BANDS of rounded rectangular scutes (each scute
  bright red with a paler pink-red raised centre and darker red seams). Seen from the front the bands form concentric
  arcs AROUND THE HEAD like a hood: the front rim of the shell frames the face. Further back the bands run across the
  back as rings; toward the rump they become narrower, finer banded plates that continue onto the tail base.
- HEAD: set low in the front opening of the shell, covered by a broad plated head shield (small red scales with a
  raised central ridge on the forehead). A small, short REPTILIAN SNOUT pointing forward and slightly down, with a
  small closed mouth (tiny white teeth may show at the lip line) and two nostrils. Two YELLOW-ORANGE eyes with dark
  slit pupils, set on the front of the head above the snout. No ears, no horns.
- LEGS: four short, thick legs covered in small red scales, almost hidden under the shell's rim. Each FRONT foot has
  FOUR large, thick, curved GREY-WHITE CLAWS (pale grey with white highlights and dark grey shading); each hind foot has
  three or four smaller grey-white claws.
- UNDERSIDE: the belly and the inner bands near the legs are a paler red-pink.
- TAIL: long and thick, as long as the body, thick at the base and tapering; finely granular, pebbly dark-red scales
  (with a few banded plates at the base); it ends in a ROUND KNOBBED BALL about twice the tail tip's width, red, with
  small pale knobs and studs on its surface (NO spikes: the spikes only grow out in the attack).

Pose (identical in all five views): standing square on all four short legs on level ground, the body low (the belly
a little above the ground, the shell rim just above the feet), the head level looking forward, mouth closed, tongue
in; the tail stretched straight BACK behind the body, slightly arching, its ball resting just above the ground,
clear of the body and of the legs (not curled, not tucked under, not to the side).

Do NOT: add spikes to the tail ball; draw the tongue; add horns, ears, fur, wings, extra legs or a saddle; make it
cute, a cartoon or a small realistic armadillo; change the colours (the armour stays red with paler pink-red highlights,
the claws grey-white, the eyes yellow-orange); curl the tail or hide it behind the body (except in the front view);
crop the tail ball, claws or snout; draw a floor, a ground shadow, a background or text.

## Per-image checks (re-run before you select a view)

Whole armadillo inside the frame with margins (tail ball included); low, broad, heavy body; red concentric scute
bands around the face; small reptile snout and yellow-orange eyes; four short legs with large grey-white claws (four
on each front foot); long thick pebbly tail ending in a knobbed ball without spikes; transparent background;
landscape 1536x1024; for 01-04 the same armadillo, pose, proportions and colours as the primary; side views: in
`03_left` the head points to image LEFT, in `04_right` to image RIGHT; the front view symmetric.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Contact sheet `references_hd/selected_views_review.png` (the five
selected views), written in run 2.

## Run 2 notes (after run 1)

Claude accepted `00_three_quarter.png` as the primary: low, broad red armadillo with the concentric scute bands
around the plated reptile head, yellow-orange slit eyes, small snout with tiny teeth, pale pink-red belly bands,
short scaly legs with large grey-white claws (five per front foot, four per hind foot: keep exactly these counts), the
pebbly tail stretched straight back ending in the knobbed ball. In 01-04 keep exactly this armadillo: same proportions,
colours, scutes, claws, tail and ball. `01_front`: straight on the face, the two front feet planted symmetric, the
concentric bands framing the head as in the original sprite; the tail hidden behind the body. `02_back`: the rump, the
fine bands narrowing into the tail base, the tail coming straight toward the camera with the ball at its end, the hind
feet at the sides. Side views: strict profiles at body height, all four legs and all claws visible, the tail stretched
straight back with the ball fully visible. Keep at least 60 px between the armadillo and every edge.

## Run 3: a second primary for Smart Topology (after the first Meshy return)

Meshy built a flat, pear-shaped body from `00_three_quarter.png`: the camera was nearly level, so the length of the
shell and the direction of the tail (straight back) could not be read; it fused the tail into the body as a wedge
going off to one side. Generate ONE new image, `00b_three_quarter_high.png` (1536x1024 landscape, transparent, the
same rules), of exactly the same armadillo as `00_three_quarter.png` (input 2) and the other selected views (inputs
3-4: `03_left.png`, `01_front.png`): same colours, scutes, head, claws, tail and knobbed ball, same standing pose.
Camera: a front three-quarter from clearly ABOVE, about 35 degrees down onto the back, the armadillo turned about 45
degrees: the head toward the image lower RIGHT, facing the camera's right side, so we see its face, its LEFT flank,
the whole domed top of the shell from the head bands back to the rump, and the long tail going straight BACK from the
rump toward the image upper LEFT (the tail fully visible over its whole length, clearly behind the body, its ball at
the end, not foreshortened to nothing). The shell must read as a tall dome (about 0.8 m high on a 1.3 m wide body),
not flat. Whole creature inside the frame with 60 px margins. At most one corrective regeneration. Record it in
`generation_runs.json` (selected flag false for `00_three_quarter`'s Meshy role is NOT needed; just add the new entry).
