"""Draw the UV layout coloured by part to review/uv_layout.png (Pillow, outside Blender is not possible -> export coords)."""
import bpy, json, numpy as np, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
me = bpy.data.objects['Peasant'].data
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
uv = me.uv_layers.active.data
polys = [[tuple(uv[li].uv) for li in p.loop_indices] for p in me.polygons]
json.dump({'polys': polys, 'part': part.tolist()}, open(os.path.join(common.WORK, 'uv_dump.json'), 'w'))
