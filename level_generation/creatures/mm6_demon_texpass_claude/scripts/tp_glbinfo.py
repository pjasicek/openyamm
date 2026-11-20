import sys, json
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glb import Glb
g=Glb(sys.argv[1]); d=g.doc
print('nodes with mesh:')
for i,n in enumerate(d['nodes']):
    if 'mesh' in n: print(' ',i,n.get('name'),'mesh',n['mesh'],'skin',n.get('skin'))
for i,m in enumerate(d['meshes']):
    prs=[]
    for p in m['primitives']:
        a=d['accessors'][p['indices']]['count']//3
        prs.append((p.get('material'),a,list(p['attributes'].keys()), bool(p.get('extensions'))))
    print('mesh',i,m.get('name'),prs, 'extras', json.dumps(m.get('extras',{}))[:200])
for i,m in enumerate(d['materials']):
    pbr=m.get('pbrMetallicRoughness',{})
    def img(t):
        if t is None: return None
        s=d['textures'][t['index']]['source']; return (s,d['images'][s].get('name'), g.image(s).size)
    print('mat',i,m.get('name'),'bc',img(pbr.get('baseColorTexture')),'mr',img(pbr.get('metallicRoughnessTexture')),'n',img(m.get('normalTexture')),'extras',{k:(img(v) if isinstance(v,dict) and 'index' in v else v) for k,v in m.get('extras',{}).items()} , 'alpha', m.get('alphaMode'), 'emis', img(m.get('emissiveTexture')))
print('variants', json.dumps(d.get('extensions',{}))[:600])
print('anims', [(a['name']) for a in d['animations']])
