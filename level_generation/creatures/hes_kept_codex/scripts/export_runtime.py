"""Export the retained animated bodies and fitted rigid equipment in their carrier bone spaces."""
import bpy,bmesh,sys,os,json,math
from pathlib import Path
import numpy as np
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1];kind=os.environ['KEPT_BODY'];code='m' if kind=='male' else 'f';style=os.environ.get('KEPT_STYLE','ragged' if kind=='male' else 'freed');T=P/'textures';E=P/'export';E.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'work'/kind/('rig_uv_hairfixed.blend' if kind=='female' else 'rig_uv.blend')))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;scene=bpy.context.scene
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();hd=np.array([a.value for a in me.attributes['head'].data]);pc=np.array([a.value for a in me.attributes['piece'].data]);co=np.array([v.co[:] for v in me.vertices]);props=[];propinfo={}
if kind=='male' and style=='ragged':
 with bpy.data.libraries.load(str(P/'work/props/props.blend'),link=False) as (src,dst):dst.objects=['hes_kept_'+n for n in ('collar','pick','club','plate')]
 propdict=dict(zip(('collar','pick','club','plate'),dst.objects))
 for o in propdict.values():scene.collection.objects.link(o);o.hide_set(False);o.hide_render=False
 # Fit a collar perpendicular to the anatomical neck axis, using the vertices in its band for its ellipse.
 neck=rig.data.bones['B_Neck'].head_local;head=rig.data.bones['B_Head'].head_local;axis=(head-neck).normalized();zlen=(head-neck).length;centre=neck.lerp(head,1.06)
 X=Vector((1,0,0));X=(X-axis*X.dot(axis)).normalized();Y=axis.cross(X);rot=Matrix((X,Y,axis)).transposed().to_4x4();rot.translation=centre
 inv=rot.inverted();local=np.array([inv@Vector(v) for v in co[pc==1]]);band=local[np.abs(local[:,2])<.018];assert len(band)>3
 ext=np.max(np.abs(band[:,:2]),axis=0)+.006
 # Polygonal ring inner radii need to cover the diagonal of the actual cross-section.
 radial=np.sqrt((band[:,0]/ext[0])**2+(band[:,1]/ext[1])**2).max();ext*=max(1.,radial)*1.035;ext+=np.array([.010,.006])
 scale=Matrix.Diagonal((ext[0]/.073,ext[1]/.063,.034/.068,1));collarmat=rot@scale
 # Solved hand grip, the same transform used in the pretexture contact gate.
 G=json.loads((P/'work/male/handle_R.json').read_text());A=Vector(G['handle_axis_hand_local']);S=json.loads((P/'work/male/source_rest.json').read_text());X=Matrix(S['B_R_Hand']['rot']).inverted()@(Vector(S['B_R_Finger2']['head'])-Vector(S['B_R_Hand']['head']));X=(X-A*X.dot(A)).normalized();grip=Matrix((X,A.cross(X),A)).transposed().to_4x4();grip.translation=Vector(G['handle_centre_hand_local']);grip=rig.data.bones['B_R_Hand'].matrix_local@grip
 # Chest plate placed outside the front shirt. Its two straps follow the shirt's cross-section.
 chest=rig.data.bones['B_Spine2'].head_local;platecentre=Vector((float(np.median(co[pc==0,0])),0,1.255));front=co[(pc==0)&(abs(co[:,0]-platecentre.x)<.13)&(abs(co[:,2]-platecentre.z)<.13),1].min();platecentre.y=float(front)-.020;platemat=Matrix.Translation(platecentre)
 for name,M,parent in [('collar',collarmat,'B_Head'),('pick',grip,'B_R_Hand'),('club',grip,'B_R_Hand'),('plate',platemat,'B_Spine2')]:
  o=propdict[name];o.data.transform(M);o.matrix_world=Matrix.Identity(4)
  bone='Kept_'+name.capitalize();bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');eb=rig.data.edit_bones.new(bone);eb.head=rig.data.edit_bones[parent].head;eb.tail=eb.head+Vector((0,0,.08));eb.parent=rig.data.edit_bones[parent];bpy.ops.object.mode_set(mode='OBJECT')
  o.vertex_groups.clear();o.vertex_groups.new(name=bone).add(list(range(len(o.data.vertices))),1,'REPLACE');mod=o.modifiers.new('Carrier','ARMATURE');mod.object=rig
  propinfo[name]={'bone':bone,'parent':parent,'matrix':[[float(x) for x in row] for row in M]};props.append(o)
 # Two continuous thin leather chest straps, formed from the shirt cross-section in the torso region.
 o=propdict['plate'];bm=bmesh.new();bm.from_mesh(o.data);mat=bpy.data.materials.get('Kept_Wrap');o.data.materials.append(mat);slot=len(o.data.materials)-1
 for z in (1.18,1.32):
  pts=co[(pc==0)&(abs(co[:,2]-z)<.035)&(abs(co[:,0]+.025)<.19)];cx=(pts[:,0].min()+pts[:,0].max())/2;cy=(pts[:,1].min()+pts[:,1].max())/2;rx=(pts[:,0].max()-pts[:,0].min())/2+.015;ry=(pts[:,1].max()-pts[:,1].min())/2+.020
  rings=[]
  for r,h in [(1,z-.014),(1,z+.014),(.97,z-.014),(.97,z+.014)]:rings.append([bm.verts.new((cx+rx*r*math.cos(i*math.tau/16),cy+ry*r*math.sin(i*math.tau/16),h)) for i in range(16)])
  for a,b in [(0,1),(3,2),(2,0),(1,3)]:
   for i in range(16):f=bm.faces.new((rings[a][i],rings[a][(i+1)%16],rings[b][(i+1)%16],rings[b][i]));f.material_index=slot
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.vertex_groups[0].add(list(range(len(o.data.vertices))),1,'REPLACE')
 print('COLLAR',dict(neck=list(neck),head=list(head),centre=list(centre),radii=ext.tolist()),flush=True)
# Merge head/body UVs into one layer; retain separate materials and 1K maps until the runtime atlas merge.
layer=me.uv_layers['RaggedUV' if style=='ragged' else 'FreedUV'];headuv=me.uv_layers['HeadUV']
for p in me.polygons:
 if hd[p.index]:
  for li in p.loop_indices:layer.data[li].uv=headuv.data[li].uv
for name in [x.name for x in me.uv_layers if x!=layer]:me.uv_layers.remove(me.uv_layers[name])
layer.name='UVMap';me.uv_layers.active=layer
me.materials.clear()
def material(name,stem):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.use_backface_culling=True;m['openyamm_specular']=1.;m['openyamm_specular_mask']=True;nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
 def tex(suffix,space):
  n=nt.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(T/f'{stem}_{suffix}_1k.png'));n.image.colorspace_settings.name=space;return n
 nt.links.new(tex('basecolor','sRGB').outputs['Color'],bs.inputs['Base Color']);normal=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('normal','Non-Color').outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs['Normal'],bs.inputs['Normal']);sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex('metal_rough','Non-Color').outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic']);return m
me.materials.append(material('KeptBody_A',f'kept_{code}_{style}'));me.materials.append(material('KeptHead_A',f'kept_{code}_head'))
me.polygons.foreach_set('material_index',hd.tolist())
for p in me.polygons:p.use_smooth=True
if style=='freed':
 for a in list(bpy.data.actions):
  if a.name.startswith('Kept_Armed') or a.name=='Kept_MaceAttack':bpy.data.actions.remove(a)
# Keep the original source rate (30 fps), all action names, and all eight influences.
scene.render.fps=30;scene.render.fps_base=1;body.name=body.data.name='Kept'
for a in ('piece','finger','head','orig_co','source_piece'):
 if a in me.attributes:me.attributes.remove(me.attributes[a])
for o in bpy.data.objects:o.select_set(o in (body,rig))
bpy.context.view_layer.objects.active=rig
stem=f'hes_kept_{code}_{style}';out=E/f'{stem}_lod0.glb'
bpy.ops.export_scene.gltf(filepath=str(out),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_extras=True,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
if kind=='male' and style=='ragged':
 for o,(name,info) in zip(props,propinfo.items()):
  info['triangles']=sum(len(p.vertices)-2 for p in o.data.polygons)
 # Final rigid exports use export_attachments.py then bind_attachments.py in glTF coordinates.
 (P/'review/attachments.json').write_text(json.dumps(propinfo,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work'/kind/f'runtime_{style}.blend'))
print('EXPORTED',stem,len(me.polygons),len(rig.data.bones),flush=True);sys.stdout.flush();sys.stderr.flush();os._exit(0)
