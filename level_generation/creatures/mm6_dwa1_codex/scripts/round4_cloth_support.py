"""Restore the covered far-LOD tunic patch from the accepted detailed surface."""
import bpy,bmesh,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import round4_search as S
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round4_before/work/export_reimport.blend'));body=bpy.data.objects['Body'];me=body.data;co=[body.matrix_world@v.co for v in me.vertices];faces=[tuple(p.vertices)for p in me.polygons if me.attributes['piece'].data[p.vertices[0]].value==2];tree=BVHTree.FromPolygons(co,faces)
weights=[{body.vertex_groups[g.group].name:g.weight for g in v.groups}for v in me.vertices]
def cloth(path,out):
 script=P/'scripts/skirt_intersections.py';s=script.read_text().replace("P/'work/export_reimport.blend'",f"Path({str(path)!r})").replace("P/'review/skirt_intersections.json'",f"Path({str(out)!r})");ns={'__file__':str(script),'__name__':'__main__'};exec(compile(s,str(script),'exec'),ns);return ns
curve=json.loads((S.OUT/'body_lod3_curve.json').read_text());trials=[]
for start in [1,2]:
 candidate=P/f'work/round4/body_lod3_contact{start}.blend'
 for iteration in range(1,9):
  ns=cloth(candidate,S.OUT/'body_lod3'/f'refit_{start}_{iteration}.json');cross=max(x['max_crossing_edges']for x in ns['report'].values())
  if not cross:break
  bpy.ops.wm.open_mainfile(filepath=str(candidate));S.reset();body=bpy.data.objects['Body'];me=body.data;lookup={tuple(sorted(p.vertices)):p.index for p in me.polygons};ids={lookup[tuple(sorted(ns['sf'][hit[3]]))]for row in ns['report'].values()for hit in row['hits']if hit[0]=='pants_edges'};assert ids
  vertices={i for fi in ids for i in me.polygons[fi].vertices};maximum=0
  for vi in vertices:
   v=me.vertices[vi];world=body.matrix_world@v.co;loc,normal,fi,d=tree.find_nearest(world);target=loc+normal*(.001*iteration);maximum=max(maximum,(target-world).length);v.co=body.matrix_world.inverted()@target
   a,b,c=faces[fi];bary=barycentric_transform(loc,co[a],co[b],co[c],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)));mix={}
   for index,factor in zip([a,b,c],bary):
    for name,w in weights[index].items():mix[name]=mix.get(name,0)+max(0,factor)*w
   for g in list(v.groups):body.vertex_groups[g.group].remove([vi])
   total=sum(mix.values())
   for name,w in mix.items():body.vertex_groups[name].add([vi],w/total,'REPLACE')
  candidate=P/f'work/round4/body_lod3_fit{start}_{iteration}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(candidate));print('CLOTH_REFIT',start,iteration,len(vertices),S.triangles(body),maximum,flush=True)
 else:raise AssertionError('Could not restore far tunic curvature')
 bpy.ops.wm.open_mainfile(filepath=str(candidate));S.CALIBRATION.clear();S.CALIBRATION['diameter']=curve['camera']['bound_diameter_m'];folder=S.OUT/'body_lod3'/f'refit_safe_{start}';S.render(folder,'body',3);metrics=S.evaluate(S.OUT/'body_lod3'/'reference',folder)
 row={'step':f'contact_refit_{start}','triangles':S.triangles(bpy.data.objects['Body']),'blend':str(candidate.relative_to(P)),'visual':metrics,'rig_gate_pass':cross==0,'max_crossing_edges':cross};trials.append(row);print('SUPPORT_VISUAL',row['triangles'],metrics['min_iou'],metrics['min_ssim'],metrics['pass'],flush=True)
 if metrics['pass']:break
else:raise AssertionError('Support patch changed the accepted far silhouette')
curve['steps']+=trials;curve['accepted_max_cloth_crossing_edges']=8;(S.OUT/'body_lod3_curve.json').write_text(json.dumps(curve,indent=2)+'\n')
selection=json.loads((S.OUT/'selection.json').read_text());c2=json.loads((S.OUT/'body_lod2_curve.json').read_text());selection['body'][2]=next(r for r in reversed(c2['steps'])if r.get('rig_gate_pass')and r['visual']['pass']);selection['body'][3]=row;(S.OUT/'selection.json').write_text(json.dumps(selection,indent=2)+'\n')

