import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path[:0]=[str(P/'scripts'),str(P.parent/'claude_shared/gates')];import run_gates as G,common,reduction_common as C
cfg=json.loads((P/'gates.json').read_text());g=G.Glb(P/'export/mm6_natm.glb');m=next(m for m in G.load_meshes(g)if m.label.endswith('colour0'));G.configure_mesh(m,cfg,G.Report(cfg));a=next(a for n,a,s,e in g.clips()if n=='Death');pose=g.pose(a,np.array([99/48]))[0];points=m.posed(pose);rows=[]
for name,surf,samples,cont in m.cloth:
 surf.build(points,pose);ids=np.flatnonzero(samples);ds,faces=surf.signed(points[ids]);k=int(ds.argmin());v=ids[k];q,n,fi,d=surf.tree.find_nearest(Vector(points[v]));row={'name':name,'depth_mm':float(max(0,-ds[k])*1000),'leg_point':points[v].tolist(),'closest':list(q),'normal':list(n),'face':int(fi),'capped':fi in surf.caps,'floor':float(points[m.regions[name],2].min()),'rest_leg':m.rest[v].tolist()};rows.append(row)
(P/'review/cloth_problem.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows),flush=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_lod0.blend'));C.cleanup();common.workbench_clay(bpy.context.scene,textured=True)
for name,f in [('Cast',21),('Death',99),('Standing',0)]:
 C.activate(name,f/48);common.render_views(str(P/f'review/problem_{name}_{f}'),.85,2.7,views=('front','left','three_quarter'),resolution=(650,650))
C.activate('Standing',0);common.render_views(str(P/'review/problem_grip'),.85,.65,views=('front','left','three_quarter'),resolution=(700,700),target=(-.30,-.12))
