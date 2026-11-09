"""Keep the accepted axe head/bit/socket exactly; use the reduced haft's complete components."""
import bpy,os,runpy,json,sys,subprocess
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];R=P/'review/round3';O=R/'protected_axe';O.mkdir(exist_ok=True);sys.path.insert(0,str(P/'scripts'));import compare_exported_lods as C
bpy.ops.wm.open_mainfile(filepath=str(R/'rebake_props_next/lod0.blend'));ob=bpy.data.objects['Axe'];low=ob.data
with bpy.data.libraries.load(str(R/'before/work/final_motion.blend'),link=False) as (src,dst):dst.meshes=[n for n in src.meshes if n.startswith('Axe')]
choices=[m for m in dst.meshes if sum(len(f.vertices)-2 for f in m.polygons)==2440];assert len(choices)==1,[m.name for m in dst.meshes];high=choices[0];eq=json.loads((P/'work/equipment.json').read_text());axis=Vector(eq['axe_axis']);center=Vector(eq['axe_centre']);verts=[];faces=[];uvs=[];normals=[];smooth=[];counts={}
for source,keep_head in [(high,True),(low,False)]:
 parent=list(range(len(source.vertices)))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for edge in source.edges:a,b=edge.vertices;parent[root(a)]=root(b)
 heights={}
 for v in source.vertices:r=root(v.index);heights[r]=max(heights.get(r,-1e9),(v.co-center).dot(axis))
 chosen=[f for f in source.polygons if (heights[root(f.vertices[0])]>.20)==keep_head];ids=sorted({v for f in chosen for v in f.vertices});remap={i:len(verts)+j for j,i in enumerate(ids)};verts.extend(tuple(source.vertices[i].co) for i in ids)
 for f in chosen:
  faces.append([remap[i] for i in f.vertices]);uvs.extend(tuple(source.uv_layers['UVMap'].data[i].uv) for i in f.loop_indices);normals.extend(tuple(source.corner_normals[i].vector) for i in f.loop_indices);smooth.append(f.use_smooth)
 counts['original_head_and_wood_haft' if keep_head else 'reduced_wrap_and_fittings']=sum(len(f.vertices)-2 for f in chosen)
me=bpy.data.meshes.new('Axe_protected_head');me.from_pydata(verts,[],faces);me.update();uv=me.uv_layers.new(name='UVMap')
for a,b in zip(uv.data,uvs):a.uv=b
for f,s in zip(me.polygons,smooth):f.use_smooth=s
me.normals_split_custom_set(normals);ob.data=me;ob.vertex_groups.clear();ob.vertex_groups.new(name='Axe').add(list(range(len(verts))),1,'REPLACE');counts['total']=sum(counts.values());assert counts['total']<2440;(O/'axe_reduction.json').write_text(json.dumps(counts,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(O/'lod0.blend'));os.environ.update(FIGC_EXPORT_SOURCE=str(O/'lod0.blend'),FIGC_EXPORT_DIR=str(O/'export_lod0'));runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
os.environ['FIGC_BAKE_ROOT']='protected_axe';runpy.run_path(str(P/'scripts/rebake_textures.py'),run_name='__main__')
D=O/'export_lod0';subprocess.run(['/usr/bin/python3',str(P/'scripts/rebake_review_materials.py'),str(D/'textures')],check=True);C.O=O/'physical';C.O.mkdir(exist_ok=True);C.PHYSICAL=True;C.TIER_DIR=D/'textures';out=C.render(D/'rebaked.glb',0,'rebaked');subprocess.run(['/usr/bin/python3',str(P/'scripts/measure_reduction.py'),str(R/'rebake/physical/reference_lod0'),str(out),str(C.O/'metrics.json')],check=True)
import shutil
G=O/'gate_input';G.mkdir(exist_ok=True);shutil.copy2(D/'rebaked.glb',G/'mm6_figc_lod0.glb');shutil.copy2(D/'rebaked_authoring.blend',G/'mm6_figc_authoring.blend');os.environ.update(FIGC_EXPORT_DIR=str(G),FIGC_VALIDATION_DIR=str(O/'validation'));runpy.run_path(str(P/'scripts/gates_exported.py'),run_name='__main__')

Q=O/'details';Q.mkdir(exist_ok=True);os.environ.update(FIGC_PROP_VALIDATION=str(O/'validation/export_validation.blend'),FIGC_PROP_TIERS=str(D/'textures'),FIGC_PROP_REVIEW=str(Q));runpy.run_path(str(P/'scripts/render_props_r3.py'),run_name='__main__')
