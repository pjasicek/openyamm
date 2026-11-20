"""Print node/primitive structure of the three Jarl GLBs to see whether they share a body."""
import sys, hashlib
sys.path.insert(0, 'level_generation/creatures/mm9_yrsa_reduce_claude/scripts')
from glbio import read_glb, prims
from pathlib import Path
for n in ['tryggva', 'sven', 'bjarni']:
    p = Path(f'assets_source/worlds/mm9/models/mm9_{n}.glb')
    print(n, hashlib.sha256(p.read_bytes()).hexdigest()[:12])
    doc, b = read_glb(p)
    for nd in doc['nodes']:
        if 'mesh' in nd:
            pr = prims(doc, b, nd['mesh'])
            print('  node', nd.get('name'), {k: (len(v['T']), len(v['P'])) for k, v in pr.items()})
    print('  variants', bool(doc.get('extensions', {}).get('KHR_materials_variants')), len(doc.get('animations', [])))
