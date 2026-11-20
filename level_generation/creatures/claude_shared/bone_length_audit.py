#!/usr/bin/env python3
"""Bone length audit: per GLB, limb joints whose translation length changes by over 10 % across clips (a stretching limb or sliding hip).
mirror_source.py can cause this on an asymmetric bind. Usage: bone_length_audit.py <glb> .... Prints joint, min, max, clip of each."""
import json,struct,sys,numpy as np,re
def load(p):
    d=open(p,'rb').read(); n=struct.unpack('<I',d[12:16])[0]; j=json.loads(d[20:20+n]); b=d[20+n+8:]; return j,b
def acc(j,b,i):
    a=j['accessors'][i]; v=j['bufferViews'][a['bufferView']]; c={'SCALAR':1,'VEC3':3,'VEC4':4}[a['type']]
    o=v.get('byteOffset',0)+a.get('byteOffset',0); t={5126:'<f4'}.get(a['componentType'])
    if t is None: return None
    s=v.get('byteStride',0) or 4*c
    return np.frombuffer(b,dtype=t,count=a['count']*(s//4),offset=o).reshape(a['count'],-1)[:,:c]
for p in sys.argv[1:]:
    j,b=load(p); nodes=j['nodes']; res={}
    for an in j.get('animations',[]):
        for c in an['channels']:
            if c['target'].get('path')!='translation': continue
            n=c['target'].get('node'); nm=nodes[n].get('name','')
            if not re.search(r'(Thigh|Calf|UpperArm|Forearm|Foot|Hand)$',nm): continue
            v=acc(j,b,an['samplers'][c['sampler']]['output'])
            if v is None: continue
            l=np.linalg.norm(v,axis=1); rest=np.linalg.norm(nodes[n].get('translation',[0,0,0]))
            r=res.setdefault(nm,[1e9,0,rest,'','']);
            if l.min()<r[0]: r[0]=float(l.min()); r[3]=an.get('name','')
            if l.max()>r[1]: r[1]=float(l.max()); r[4]=an.get('name','')
    bad=[(k,round(v[0],3),round(v[1],3),v[3],v[4]) for k,v in res.items() if v[0]>0 and v[1]/v[0]>1.1]
    print(p.split('/')[-1],'checked',len(res),'stretching',len(bad)); 
    for x in sorted(bad,key=lambda x:-x[2]/x[1])[:4]: print('   ',x)
