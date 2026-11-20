import sys, math
from pathlib import Path
sys.path.insert(0, str(Path('tools').resolve()))
from build_actor_lods import generate
p = Path(__file__).resolve().parents[1]
# Preserve the thin cutting surface; otherwise the reducer spends its budget on the grip rings.
points = []
for y, w, h in [(-.145,.013,.0032),(-.181,.016,.0030),(-.285,.014,.0025),
                (-.391,.009,.0019),(-.440,.003,.0009)]:
    points += [(.263-w,y,.459),(.263-.70*w,y,.459+h*.50),(.263,y,.459+h),
               (.263+.70*w,y,.459+h*.50),(.263+w,y,.459),(.263+.70*w,y,.459-h*.50),
               (.263,y,.459-h),(.263-.70*w,y,.459-h*.50)]
points.append((.263,-.466,.459))
# Keep the two disk rims separate so the buckler stays closed at every distance.
for i in range(32):
    angle = i * math.tau / 32
    for y in [-.115, -.107]:
        points.append((-.263 + .079 * math.cos(angle), y, .459 + .079 * math.sin(angle)))
# Thin shield faces also need a higher far budget than the body.
generate(p/'export/mm8_m556_runtime_lod0.glb', p/'export/mm8_m556_lods.glb', 'Wasp',
         max_influences=4, protected_points=points, material_ratios={'WaspEquipment': (.5, .18, .12)})
