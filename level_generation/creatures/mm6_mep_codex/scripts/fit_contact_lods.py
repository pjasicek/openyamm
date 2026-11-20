import bpy,json,sys,subprocess,os,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import reduce_measured as rm,final_refinements
R=p/'review/reduction';sel=json.loads((R/'selected.json').read_text());curve=[]
for level,target in [(3,3500)]:
 ob,r=rm.reset('body');original=sum(len(f.vertices)-2 for f in ob.data.polygons);pv=[x.value for x in ob.data.attributes['piece'].data]
 print('PIECE_COUNTS',{x:sum(len(f.vertices)-2 for f in ob.data.polygons if all(pv[i]==x for i in f.vertices)) for x in set(pv)},flush=True)
 n,protection=rm.reduce(ob,r,'body',level,target/original,preview=False);tag=f'contact_selected_body_{level}';path=f'work/reduction/{tag}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(p/path));rm.render(ob,r,'body',level,tag)
 score=json.loads(subprocess.check_output(['/usr/bin/python3',str(p/'scripts/reduction_metrics.py'),str(R),f'switch_ref_body_{level}',tag],text=True));row={'part':'body','lod':level,'triangles':n,'blend':path,'protected':protection,**score};row['pass']=score['pooled_iou']>=.97;curve.append(row);print('CONTACT_LOD',level,n,score['pooled_iou'],row['pass'],flush=True)
 if row['pass']:sel['body'][str(level)]=row
 (R/'contact_selected_curve.json').write_text(json.dumps(curve,indent=2));(R/'selected.json').write_text(json.dumps(sel,indent=2))
 bpy.ops.wm.open_mainfile(filepath=str(p/path));ob=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];staff=bpy.data.objects['StaffMesh'];staff.data.attributes.new('piece','INT','POINT').data.foreach_set('value',[100]*len(staff.data.vertices))
 for o in bpy.data.objects:o.select_set(o in [ob,staff])
 bpy.context.view_layer.objects.active=ob;bpy.ops.object.join();final_refinements.apply(r,ob)
 for a in bpy.data.actions:
  if a.name in ['Death','Dead']:a.use_fake_user=False
 pilot=f'work/contact_pilot{level}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(p/pilot));os.environ['GATE_BLEND']=pilot;os.environ['GATE_REPORT']=f'review/reduction/{tag}_dense.json';os.environ['CLOTH_REPORT']=f'review/reduction/{tag}_cloth.json';os.environ['PHYSICAL_REPORT']=f'review/reduction/{tag}_physical.json'
 for script in ['dense_gates.py','cloth_surface_gate.py','physical_gates.py']:runpy.run_path(str(p/'scripts'/script),run_name='__main__')
