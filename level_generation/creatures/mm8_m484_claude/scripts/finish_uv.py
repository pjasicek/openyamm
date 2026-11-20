from pathlib import Path
import sys,runpy,bpy,bmesh,json
P=Path(__file__).resolve().parents[1]
def run(n,args=[]):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('finalize_motion.py')
run('repack_head_uv.py')
for layer in ['UVMap','HeadUV']:run('uv_raster.py',[P/'work/rig_textured_uv.blend',layer,1024])
run('check_uv.py')
b=bpy.data.objects['Body'];bm=bmesh.new();bm.from_mesh(b.data);hd=bm.faces.layers.int['head'];uv=bm.loops.layers.uv['UVMap'];huv=bm.loops.layers.uv['HeadUV'];pairs=[]
for e in bm.edges:
 if len(e.link_faces)!=2 or e.link_faces[0][hd]==e.link_faces[1][hd]:continue
 row={}
 for f in e.link_faces:
  layer=huv if f[hd] else uv;ls=[l for l in f.loops if l.vert in e.verts];middle=(ls[0][layer].uv+ls[1][layer].uv)/2;centre=sum((l[layer].uv for l in f.loops),middle*0)/len(f.loops);row['head' if f[hd] else 'body']=list(middle.lerp(centre,.35))
 pairs.append(row)
bm.free();(P/'work/head_seam_uv.json').write_text(json.dumps(pairs))
run('bake_ao.py',[P/'work/rig_textured_uv.blend',1024])
