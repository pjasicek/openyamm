#!/usr/bin/env python3
"""A species with "base" (tree06a, the food tree with fruit) is the base species' tree plus its own extras: copy the
base's built tree (tree.blend after the LOD2 clump cards, clumps.json, profile.json and every map) into work/<id>/,
so geometry, clumps, occlusion and textures are identical. Usage: copy_base.py <id>"""
import glob, os, shutil
import common
spec = common.load(); base = common.load(spec['base'])
for path in glob.glob(os.path.join(base['work'], '*')):
    name = os.path.basename(path)
    if name in ('tree.blend', 'clumps.json', 'profile.json') or (name.endswith('.png') and not name.startswith(
            ('impostor', 'rv', 'lc', 'under', 'clump0', 'clump1'))):
        shutil.copy2(path, os.path.join(spec['work'], name))
print('BASE', spec['base'], '->', spec['id'])
