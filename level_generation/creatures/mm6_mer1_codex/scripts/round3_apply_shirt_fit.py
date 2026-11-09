import bpy,sys,numpy as np,shutil,runpy
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
fit=np.load(P/'work/round3/shirt_fit.npz');kd=KDTree(len(fit['rest']))
for i,c in enumerate(fit['rest']):kd.insert(c,i)
kd.balance()
for rel in ['work/round3/master.blend','work/round3/body_lod0.blend']:
 path=P/rel;backup=path.with_name(path.stem+'_before_fit.blend')
 if not backup.exists():shutil.copyfile(path,backup)
 bpy.ops.wm.open_mainfile(filepath=str(backup));C.reset();o=bpy.data.objects['Body'];part=[v.value for v in o.data.attributes['piece'].data]
 for v in o.data.vertices:
  if part[v.index]!=1:continue
  c,i,d=kd.find(v.co)
  if d>.02:continue
  for group in list(v.groups):
   if o.vertex_groups[group.group].name!='_reduction_protect':o.vertex_groups[group.group].remove([v.index])
  for j,w in zip(fit['joints'][i],fit['weights'][i]):
   if w>1e-8:o.vertex_groups[str(fit['bones'][j])].add([v.index],float(w),'REPLACE')
 for im in bpy.data.images:
  if im.source=='FILE' and im.filepath and Path(bpy.path.abspath(im.filepath)).is_file():
   if im.packed_file:im.unpack(method='REMOVE')
   im.reload()
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(path))
for name in ['round3_far_lods.py','round3_export_selected.py','round3_package.py','round3_viewer.py','round3_configure_gates.py','round2_final_gates.py']:
 print('REFIT BUILD',name,flush=True);runpy.run_path(str(P/'scripts'/name),run_name='__main__')
