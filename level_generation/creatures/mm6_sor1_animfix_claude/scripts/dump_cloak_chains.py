"""Dump a project's cloak chains (a scene property written by its cloak_rig.py: bone names, rest points in Blender
axes, chain angle) to JSON for cloak.py. Read-only (the blend is not saved). Package h03 generalisation of h01's dump
(the MM6 Thief's scene['thf_cloak'] of Thief_Rig).

    blender --background --factory-startup --python dump_cloak_chains.py -- <out.json> <rig.blend> <scene key> <rig object>
"""
import json
import sys

import bpy

args = sys.argv[sys.argv.index('--') + 1:]
out, blend, key, rig = args[:4]
bpy.ops.wm.open_mainfile(filepath=blend)
ch = json.loads(bpy.context.scene[key])
arm = bpy.data.objects[rig]
data = {'chains': ch, 'arm_world': [list(r) for r in arm.matrix_world],
        'bones': {b.name: {'head': list(b.head_local), 'tail': list(b.tail_local)} for b in arm.data.bones}}
open(out, 'w').write(json.dumps(data))
print('DUMPED', len(ch), list(ch[0].keys()))
