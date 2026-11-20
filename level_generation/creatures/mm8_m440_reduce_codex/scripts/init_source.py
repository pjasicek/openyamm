"""Snapshot source import and protected-region inventory for the Ogre reduction trial."""
import os, runpy
from pathlib import Path
P = Path(__file__).resolve().parents[1]
os.environ.update(REA_GLB=str(P / 'work/mm8_m440_source_pre_reduce.glb'), REA_NODE='M440')
runpy.run_path(str(P / 'scripts/import_source.py'), run_name='__main__')
runpy.run_path(str(P / 'scripts/dump_mesh.py'), run_name='__main__')
import bpy, numpy as np, json
src = bpy.data.objects['Body']
v = np.array([v.co[:] for v in src.data.vertices])
d = np.load(P / 'work/mesh_in.npz'); f = d['faces']
parent = list(range(len(v)))
def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]; i = parent[i]
    return i
for tri in f:
    for a,b in zip(tri, np.roll(tri,1)):
        a,b=find(int(a)),find(int(b));parent[a]=b
labels=np.array([find(i) for i in range(len(v))]); comp=labels[f[:,0]]
np.save(P/'work/components.npy',comp)
idx={g.index:g.name for g in src.vertex_groups}
weights=np.zeros((len(v),len(idx)))
for vert in src.data.vertices:
    for g in vert.groups: weights[vert.index,g.group]=g.weight
np.savez(P/'work/weights.npz',weights=weights,names=np.array(list(idx.values())))
for code in np.unique(comp)[np.argsort([-int((comp==c).sum()) for c in np.unique(comp)])]:
    ids=np.unique(f[comp==code]);dominant=np.argsort(-weights[ids].sum(0))[:3]
    print('PART',code,'tris',int((comp==code).sum()),'center',v[ids].mean(0).round(3),'bounds',v[ids].min(0).round(3),v[ids].max(0).round(3),'bones',[(idx[i],round(float(weights[ids,i].mean()),2)) for i in dominant])
# Keep head, both hands/fingers, sole patches and small hardware exactly.
locked={g.index for g in src.vertex_groups if any(k in g.name for k in ('Head','Jaw','Finger','Hand'))}
wv=weights[:,list(locked)].sum(1)>.1
keep=wv[f].any(1) | (v[f,:,][...,2].min(1)<.06)
ids,counts=np.unique(comp,return_counts=True)
keep |= np.isin(comp,ids[counts<=80])
np.save(P/'work/keep.npy',keep)
print('KEEP',int(keep.sum()),'of',len(f),'head',int((d['protect']>.5).sum()))
# Runtime merged atlas for the drift check.
for material in src.data.materials:
    for node in material.node_tree.nodes:
        if node.type=='TEX_IMAGE' and node.image and 'base' in node.image.name.lower():
            node.image.save_render(str(P/'work/basecolor.png'));print('BASE',node.image.name);break
