"""Dump the head faces' UVs (face attribute `head`) with their part names: work/head_uv_layout.json.
Usage: blender --background work/rig_v3.blend --python dump_head_uv.py"""
import bpy, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
me = bpy.data.objects['Thief'].data
parts = json.loads(bpy.context.scene['thf_parts'])
part = np.zeros(len(me.polygons), int)
me.attributes['part'].data.foreach_get('value', part)
head = np.zeros(len(me.polygons), int)
me.attributes['head'].data.foreach_get('value', head)
uv = me.uv_layers.active.data
faces = [[parts[part[p.index]], [tuple(uv[li].uv) for li in p.loop_indices]] for p in me.polygons if head[p.index]]
json.dump({'faces': faces}, open(os.path.join(common.WORK, 'head_uv_layout.json'), 'w'))
print('HEADUV', len(faces))
