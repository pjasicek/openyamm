#!/usr/bin/env python3
"""Step 3 of the Oblivion weapon skins (README.md): the Meshy upload and the retexture request of one weapon tier.

  python3 meshy_request.py <template> <tier> [version] [--pieced]

--pieced (the bow, README.md "Bow v2: pieced upload"): prep_pieced.py's upload (work/<template>/pieced/) and the
masters in work/<template>/masters_t<tier>_<version>/.

work/<template>/upload_meshy.glb: prep.py's upload with its triangles wound to agree with their normals (layouts made
before fix_winding.py carry the templates' old winding, against them; Meshy gets a consistent mesh). UVs and positions
unchanged.
requests/<template>_t<tier>_<version>.json: meshy-7, original UVs, PBR, 4K, the tier's Codex masters as multiview.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import glb_io

PIECED = '--pieced' in sys.argv
args = [a for a in sys.argv[1:] if a != '--pieced']
name, tier = args[0], int(args[1])
version = args[2] if len(args) > 2 else 'v1'
work = os.path.join(PROJECT, 'work', name)
base = os.path.join(work, 'pieced') if PIECED else work
upload = os.path.join(base, 'upload_meshy.glb')
if not os.path.exists(upload):
    doc, binary = glb_io.read(os.path.join(base, 'upload.glb'))
    views = [glb_io.view_bytes(doc, binary, i) for i in range(len(doc['bufferViews']))]
    prim = doc['meshes'][0]['primitives'][0]
    a = doc['accessors'][prim['indices']]
    flip = glb_io.share_wound_with_normals(doc, binary, prim) < 0.5
    idx = np.array(glb_io.accessor(doc, binary, prim['indices'])).reshape(-1, 3)
    if flip:
        idx = idx[:, [0, 2, 1]]
    views[a['bufferView']] = np.ascontiguousarray(idx.ravel()).tobytes()
    a.pop('byteOffset', None)
    glb_io.write(upload, doc, views)
# The v2 masters (codex_masters_pieced.py) live in masters_t<tier>_<version>/, for pieced and original uploads alike.
versioned = os.path.join('work', name, f'masters_t{tier}_{version}')
masters = versioned if PIECED or (version != 'v1' and os.path.isdir(os.path.join(PROJECT, versioned))) \
    else os.path.join('work', name, f'masters_t{tier}')
order = ['01_front.png', '03_left.png', '02_back.png', '04_right.png']
images = [f'@file:{masters}/{f}' for f in order if os.path.exists(os.path.join(PROJECT, masters, f))]
request = {'model_url': '@file:' + os.path.relpath(upload, PROJECT), 'ai_model': 'meshy-7', 'enable_original_uv': True,
           'enable_pbr': True, 'texture_resolution': '4k', 'target_formats': ['glb'], 'multiview_image_urls': images}
path = os.path.join(PROJECT, 'requests', f'{name}_t{tier}_{version}.json')
json.dump(request, open(path, 'w'), indent=1)
print(path, len(images), 'views')
