"""Compare two converted MM9 GLBs joint by joint (names, translations, rotations). Args: <glb a> <glb b>"""
import sys, json, struct
import numpy as np
def load(p):
    b=open(p,'rb').read()
    n=struct.unpack('<I',b[12:16])[0]
    return json.loads(b[20:20+n])
def nodes(p):
    g=load(p)
    skin=g['skins'][0]
    out={}
    for j in skin['joints']:
        nd=g['nodes'][j]
        out[nd['name']]=(np.array(nd.get('translation',[0,0,0])),np.array(nd.get('rotation',[0,0,0,1])))
    return out, len(g['nodes'])
a,na=nodes(sys.argv[1]); b,nb=nodes(sys.argv[2])
print(len(a),len(b),na,nb, 'names equal', list(a)==list(b), set(a)==set(b))
mt=0;mr=0
for k in a:
    if k not in b: print('missing',k); continue
    dt=np.abs(a[k][0]-b[k][0]).max(); dr=min(np.abs(a[k][1]-b[k][1]).max(),np.abs(a[k][1]+b[k][1]).max())
    if dt>1e-4 or dr>1e-4: print(k, 'dt %.5f dr %.5f'%(dt,dr))
    mt=max(mt,dt);mr=max(mr,dr)
print('max dt',mt,'max dr',mr)
