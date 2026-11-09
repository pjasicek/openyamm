"""Repair perspective-derived limb asymmetry from the fully resolved anatomical right side."""
from pathlib import Path
import bpy,bmesh,json,numpy as np,sys
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'mm6_ogr_claude/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'))
body=bpy.data.objects['Body'];me=body.data
raw=json.loads((P/'work/meshy_joints.json').read_text());(P/'work/meshy_joints_original.json').write_text(json.dumps(raw,indent=2)+'\n')
co=np.array([tuple(v.co) for v in me.vertices]);piece=np.array([v.value for v in me.attributes['piece'].data]);eyes=[co[piece==i].mean(0) for i in (1,2)];plane=float(np.mean(eyes,axis=0)[0])
bm=bmesh.new();bm.from_mesh(me)
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(plane,0,0),plane_no=(1,0,0),dist=1e-6,clear_outer=True)
for v in bm.verts:v.co.x-=plane
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
bpy.context.view_layer.objects.active=body
mod=body.modifiers.new('BilateralNeutralAnatomy','MIRROR');mod.use_clip=True;mod.use_mirror_merge=True;mod.merge_threshold=.0001
bpy.ops.object.modifier_apply(modifier=mod.name)
me=body.data;co=np.array([tuple(v.co) for v in me.vertices]);me.attributes.get('orig_co').data.foreach_set('vector',co.ravel())
J={k:np.array(v) for k,v in raw['joints'].items()}
for n in list(J):
 if n.startswith('L_'):continue
 J[n][0]-=plane
 if n.startswith('R_'):
  J['L_'+n[2:]]=J[n]*np.array([-1,1,1])
 else:J[n][0]=0
# Clavicles originate on the upper chest; the automatic estimate placed their roots near the muzzle.
for side,sgn in [('L',1),('R',-1)]:J[side+'_Clavicle']=np.array([sgn*.12,.045,1.31])
out={'height_m':float(co[:,2].max()),'joints':{k:v.tolist() for k,v in J.items()},'symmetry_plane_before_centre':plane,'method':'Right-side native anatomy mirrored; body axial joints centred. Source estimates retained separately.'}
(P/'work/meshy_joints_symmetric.json').write_text(json.dumps(out,indent=2)+'\n')
(P/'work/joints_final.json').write_text(json.dumps(out,indent=2)+'\n')
body['original_symmetry_plane']=plane
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/step1.blend'))
common.workbench_clay(bpy.context.scene);common.render_views(str(P/'review/geometry/symmetric'),.85,2.5,views=('front','left','back','three_quarter'),resolution=(900,900))
common.render_views(str(P/'review/geometry/symmetric_head'),1.28,.7,views=('front','left'),resolution=(650,650),target=(0,-.4))
assert np.max(abs(co[:,0]))>.7 and abs(co[:,0].min()+co[:,0].max())<1e-5
print('SYMMETRY',plane,'vertices',len(co),'tris',sum(len(f.vertices)-2 for f in me.polygons),flush=True)
