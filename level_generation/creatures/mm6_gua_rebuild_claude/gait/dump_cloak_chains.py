"""Dump the MM6 Thief's cloak chains (scene['thf_cloak'] of ../../mm6_thf_claude/work/rig_v3.blend: bone names, rest points
in Blender axes, chain angle) to JSON for cloak.py. Read-only (the blend is not saved).

    blender --background --factory-startup --python dump_cloak_chains.py -- <out.json> <rig_v3.blend>
"""
import json
import sys

import bpy

out = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 2])
ch = json.loads(bpy.context.scene['thf_cloak'])
arm = bpy.data.objects['Thief_Rig']
data = {'chains': ch, 'arm_world': [list(r) for r in arm.matrix_world],
        'bones': {b.name: {'head': list(b.head_local), 'tail': list(b.tail_local)} for b in arm.data.bones}}
open(out, 'w').write(json.dumps(data))
print('DUMPED', len(ch), list(ch[0].keys()))
