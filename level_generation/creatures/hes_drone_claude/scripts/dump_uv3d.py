"""Per-triangle UVs (atlas and TileUV), rest positions, normals, part and mat ids of HDR (work/gear_v1.blend) -> work/uv3d.npz"""
import bpy, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'gear_v1.blend'))
m = bpy.data.objects['HDR'].data
m.calc_loop_triangles()
uvl = m.uv_layers['UVMap'].data
part = np.zeros(len(m.polygons), int); m.attributes['part'].data.foreach_get('value', part)
tile = m.uv_layers['TileUV'].data if 'TileUV' in m.uv_layers else uvl
mat = np.zeros(len(m.polygons), int)
if 'mat' in m.attributes:
    m.attributes['mat'].data.foreach_get('value', mat)
tri_uv, tri_co, tri_n, tri_part, tri_tile, tri_mat = [], [], [], [], [], []
for t in m.loop_triangles:
    tri_tile.append([tuple(tile[l].uv) for l in t.loops]); tri_mat.append(mat[t.polygon_index])
    tri_uv.append([tuple(uvl[l].uv) for l in t.loops])
    tri_co.append([tuple(m.vertices[v].co) for v in t.vertices])
    tri_n.append(tuple(t.normal)); tri_part.append(part[t.polygon_index])
np.savez(os.path.join(HERE, 'work', 'uv3d.npz'), uv=np.array(tri_uv), co=np.array(tri_co), n=np.array(tri_n),
         part=np.array(tri_part), tile=np.array(tri_tile), mat=np.array(tri_mat))
print('DUMP', len(tri_uv))
