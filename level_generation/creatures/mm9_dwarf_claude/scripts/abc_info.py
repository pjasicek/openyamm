"""Facts of an ABC: nodes, pieces, clips, events, sockets, child models. Args: <abc>..."""
import sys
sys.path.insert(0,'tools/mm9_import_discovery')
import convert_abc_model as c
from pathlib import Path
for p in sys.argv[1:]:
    m=c.read_abc(Path(p))
    print('FILE',p, 'version',getattr(m,'version',None))
    print(' fields',[k for k in vars(m).keys()])
    print(' nodes',len(m.nodes))
    for i,n in enumerate(m.nodes): print('  ',i,n.name, getattr(n,'parent',None))
    for pc in m.pieces:
        print(' piece',pc.name, 'tex', getattr(pc,'texture_index',None), 'lods',len(pc.lods), 'v',len(pc.lods[0].vertices),'f',len(pc.lods[0].faces))
    print(' anims',[(a.name,len(a.keys) if hasattr(a,'keys') else None) for a in m.animations])
    print(' sockets',[s.name for s in getattr(m,'sockets',[])])
    print(' childs',getattr(m,'child_models',None))
