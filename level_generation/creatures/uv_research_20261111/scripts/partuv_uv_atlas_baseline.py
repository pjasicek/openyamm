"""PartUV study: the baseline - a fresh claude_shared/uv_atlas.py run (imported read-only, defaults of
TEXTURE_QUALITY_PASS.md) on one set object of a partuv_split_sets.py blend.

Args: <in blend> <set object> <out blend> <report json> [head=Bone1,...] [key=value uv_atlas.unwrap options]
      charts_npz=<partuv_run.py npz> runs the hybrid (partuv_uv_atlas_hybrid.py): PartUV charts + uv_atlas merge/pack
"""
import json
import os
import sys
import time

import bpy

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                'claude_shared'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if any(a.startswith('charts_npz=') for a in sys.argv):
    import partuv_uv_atlas_hybrid as uv_atlas  # noqa: E402
else:
    import uv_atlas  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:]
IN, NAME, OUT, REPORT = argv[:4]
opts = dict(a.split('=', 1) for a in argv[4:])
head = tuple(opts.pop('head').split(',')) if opts.get('head') else ()


def value(v):
    try:
        return int(v)
    except ValueError:
        try:
            return float(v)
        except ValueError:
            return v


options = {k: value(v) for k, v in opts.items()}
bpy.ops.wm.open_mainfile(filepath=IN)
obj = bpy.data.objects[NAME]
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o != obj:
        bpy.data.objects.remove(o)
start = time.time()
report = uv_atlas.unwrap(obj, head_groups=head, **options)
report['seconds'] = round(time.time() - start, 1)
print('UV_ATLAS', json.dumps(report))
json.dump(report, open(REPORT, 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
