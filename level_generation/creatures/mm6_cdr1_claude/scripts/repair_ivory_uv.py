"""Separate ivory interiors from overlapping skin UVs without changing any mesh positions or weights."""
import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/before_ivory_v3/export/mm6_cdr1.blend'))
o=bpy.data.objects['Body'];me=o.data;uv=me.uv_layers.active.data
hulls=[np.array(h) for h in json.loads((P/'work/ivory_hulls_v3.json').read_text())]
tiles=json.loads((P/'work/ivory_tiles_v3.json').read_text());counts={l:0 for l in tiles}
co=np.array([list(v.co) for v in me.vertices]);co[:,0]=abs(co[:,0])
def inside(points):
    result=np.zeros(len(points),bool)
    for eq in hulls: result|=np.max(points@eq[:,:3].T+eq[:,3],axis=1)<=.006
    return result
vertex_inside=inside(co)
for face in me.polygons:
    if not vertex_inside[list(face.vertices)].all(): continue
    if not inside(co[list(face.vertices)].mean(0)[None])[0]: continue
    label=['body','head','wings'][face.material_index];tile=tiles[label];x,y,size,pad=[tile[k] for k in ['x','y','size','padding']]
    for loop in face.loop_indices:
        v=co[me.loops[loop].vertex_index]
        # Continuous physical projection keeps subtle enamel grain coherent across adjacent faces.
        u=np.clip((v[0]+(v[1]+1.6)*.2)/2,0,1);w=np.clip(v[2]/1.8,0,1)
        uv[loop].uv=((x+pad+u*(size-2*pad))/2048,1-(y+pad+w*(size-2*pad))/2048)
    counts[label]+=1
assert all(v>0 for v in counts.values())
(P/'review/ivory_v3/uv_repair.json').write_text(json.dumps({'remapped_faces':counts,'positions_weights_animations_unchanged':True,'tiles':tiles},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/ivory_v3.blend'));print('IVORY_UV',counts)
# Use the established exporter with this UV-only source revision.
s=(P/'scripts/export_teeth.py').read_text().replace("P/'work/teeth_v2.blend'", "P/'work/ivory_v3.blend'")
exec(compile(s,str(P/'scripts/export_teeth.py'),'exec'))
