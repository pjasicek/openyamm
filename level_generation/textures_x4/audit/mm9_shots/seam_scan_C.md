# Seam scan C (lichlab, dragonstadium, traininghall), 2026-11-01

Every pair checked (native vs x4, brightened side-by-side, crops where needed, regional mean/hue/saturation measured).
Coordinates are in the 1600x900 frame. No straight repeat seams, broken door joints or black/opaque/placeholder
areas were found in any of the three maps; the suspects below are tone shifts and texture-content problems.

lichlab 05-bulla96a9n-d88-joint-graze.png tone step: thin side/edge face of the fur door turned saturated yellow (hue 27->51, sat 0.22->0.38) against the beige fur face beside it; native edge matches the fur. x 860-900, y 0-600 (between fur face and the blue target)
lichlab 07-lichzdhkt1-d3-closed-front.png tone step: copper tile panels of the neighbouring arched door are clearly more saturated orange than native brown (sat 0.57->0.73) while its pale frame is unchanged. right edge, x 1400-1600, y 260-900
lichlab 09-lichzdhkt1-d3-closed-back.png tone step: same orange tile panels (sat 0.57->0.73) on the arched door. left edge, x 0-190, y 120-900
lichlab 10-outecpb4oj-d1-closed-front.png tone step: same orange tile panels on the arched door (tile sat 0.54->0.72). left, x 120-380, y 340-720
lichlab 12-outecpb4oj-d1-closed-back.png tone step: same orange tile panels on the arched door (sat 0.56->0.72, 0.47->0.60). right, x 1220-1470, y 340-720
lichlab 16-verdrahook-d13-closed-front.png tone step: door tile panels gold-orange instead of dull brown (sat 0.39->0.51) against the unchanged green-grey door frame and stone wall. centre, x 600-1000, y 60-900
lichlab 17-verdrahook-d13-joint-graze.png tone step: same gold-orange door tiles. centre, x 580-1080, y 0-800
lichlab 18-verdrahook-d13-closed-back.png tone step: same gold-orange door tiles (smaller, far door). centre, x 680-900, y 160-750
lichlab 19-verdrahook-d13-open-front.png tone step: same gold-orange door tiles (door renders closed in both native and x4, identical pose to 16). centre, x 600-1000, y 60-900
lichlab 20-yanmleoxzq-d12-closed-front.png tone step (mild): translucent blue door panel more saturated blue than native grey-blue (sat 0.17->0.27) inside the unchanged bronze frame. centre, x 600-1000, y 220-900
lichlab 21-yanmleoxzq-d12-joint-graze.png tone step (mild): same bluer door panel (sat 0.17->0.26). centre-right, x 620-1200, y 240-900
lichlab 45-room3-s.png tone step: double door copper tiles orange (sat 0.57->0.73, 0.60->0.75) against the unchanged pale metal frame. left-centre, x 60-1000, y 0-540
lichlab 53-room15-n.png tone step: orange tile panels of the side door (sat 0.44->0.51, visibly more orange). left edge, x 0-240, y 140-480
lichlab 57-room32-e.png tone step: both small arched doors' tile panels bright orange vs native brown. centre, x 680-1020, y 270-450
lichlab 59-room32-w.png tone step: both arched doors' tile panels bright orange (same texture as above), centre x 840-1160, y 180-440; possible seam (borderline): thin straight light lines on the carpet floor not visible in native, one vertical through x~770 from y 560 to 900 plus lines along the red band edges, y 600-700
lichlab 60-room32-s.png possible seam (borderline): thin straight light vertical line in the carpet floor, x~825, y 560-900, plus lines along the red band, not visible in native
dragonstadium 10-room2-up.png texture artefact (borderline, regenerated rouglu1wpl): blue-grey cave rock shows a hexagonal cell / stained-glass mosaic pattern not present in native. top half, x 0-1600, y 0-450
dragonstadium 11-room1-e.png texture artefact (borderline): same hexagonal cell mosaic on the blue-grey rock wall. top and left, x 0-1600, y 0-650
dragonstadium 12-room1-n.png texture artefact (borderline): same cell mosaic on the blue-grey rock. upper half and lower-left, x 0-1600, y 0-550
dragonstadium 13-room1-w.png texture artefact (borderline): same cell mosaic, strongest close up. whole rock face, x 0-1600, y 0-700
dragonstadium 14-room1-s.png texture artefact (borderline): same cell mosaic. left and top walls, x 0-1600, y 0-650
dragonstadium 15-room1-up.png texture artefact (borderline): same cell mosaic on the overhead rock. x 0-1600, y 0-700
traininghall 12-trai5edeh2-d17-closed-front.png wrong colour: yellow brush head on the jousting horse's lance has bright red patches at its binding end; native shows olive/brown there. x 300-450, y 190-310
traininghall 13-trai5edeh2-d17-joint-graze.png wrong colour: same red patches on the brush binding (bright red blocks at the stick end). x 600-720, y 440-560
traininghall 22-traip5kw7e-d53-closed-back.png wrong colour: same red patch on the brush at the lance tip. right, x 1000-1100, y 350-440
traininghall 23-traiu1tudj-d11-closed-front.png wrong colour: same red patch on the brush at the lance tip. right, x 1460-1570, y 490-570
traininghall 25-traiu1tudj-d11-closed-back.png wrong colour: same red patch on the brush at the lance tip. left-centre, x 530-650, y 360-440

Notes, not counted: the Training Hall targets (`trai39pw68`, shots 10-11) and the Dragon Stadium floors and the
brown cave walls of rooms 2-3 match native in layout and tone, with no seams. The orange tile panels in Lich Lab are one
door-tile texture repeated across several doors; one fix covers all of those lines. Training Hall's yellow wheel spokes
and rims (03-05, 20-22) are slightly more saturated (sat about 0.31->0.37 and 0.47->0.55), which is within tolerance.

lichlab: 61 shots checked, 16 suspects
dragonstadium: 15 shots checked, 6 suspects
traininghall: 59 shots checked, 5 suspects
