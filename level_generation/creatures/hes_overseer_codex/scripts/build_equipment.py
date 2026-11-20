"""Original Overseer weapons from the approved sheets, on shared Kreegan ceramic/metal maps.
Local coordinates: grip at origin; rods +Z, pistol forward -Y, hip saber blade -Z.
These standalone sources precede hand attachment and final LOD processing.
"""
import bpy,bmesh,json,math,os,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
T=P/'textures';pieces=[];records={}
def material(name,glow=False):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.use_backface_culling=True;nt=m.node_tree;b=nt.nodes.get('Principled BSDF')
 if glow:
  b.inputs['Base Color'].default_value=(1,.36,.045,1);b.inputs['Emission Color'].default_value=(1,.36,.045,1);b.inputs['Emission Strength'].default_value=1;b.inputs['Roughness'].default_value=.4
 else:
  def tex(s,cs):
   n=nt.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(T/f'overseer_equipment_{s}.png'));n.image.colorspace_settings.name=cs;return n
  nt.links.new(tex('basecolor','sRGB').outputs['Color'],b.inputs['Base Color'])
  nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('normal','Non-Color').outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],b.inputs['Normal'])
  sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex('metal_rough','Non-Color').outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],b.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],b.inputs['Metallic'])
 return m
plate=material('OV_Equipment');grip_material=plate.copy();grip_material.name='OV_Grip';glow=material('OV_Glow',True)
BOX={'ivory':(.12,.83,.24,.98),'gold':(.105,.455,.112,.465),'dark':(.81,.25,.89,.35)}
def finish(o,name,style='ivory',bevel=0):
 o.name=name;bpy.context.view_layer.objects.active=o;o.select_set(True)
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:
  m=o.modifiers.new('Edge relief','BEVEL');m.width=bevel;m.segments=1;m.affect='EDGES';bpy.ops.object.modifier_apply(modifier=m.name)
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bmesh.ops.triangulate(bm,faces=bm.faces);bm.to_mesh(o.data);bm.free()
 o.data.materials.clear();o.data.materials.append(glow if style=='glow' else grip_material if style=='grip' else plate)
 uv=o.data.uv_layers.new(name='UVMap') if not o.data.uv_layers else o.data.uv_layers.active
 if style!='glow':
  u0,v0,u1,v1=BOX['dark' if style=='grip' else style]
  for f in o.data.polygons:
   drop=max(range(3),key=lambda i:abs(f.normal[i]));axes=[i for i in range(3) if i!=drop]
   lo=[min(v.co[a] for v in o.data.vertices) for a in axes];hi=[max(v.co[a] for v in o.data.vertices) for a in axes]
   for loop in f.loop_indices:
    c=o.data.vertices[o.data.loops[loop].vertex_index].co
    q=[(c[a]-lo[k])/max(hi[k]-lo[k],1e-7) for k,a in enumerate(axes)];uv.data[loop].uv=(u0+q[0]*(u1-u0),v0+q[1]*(v1-v0))
 pieces.append(o);o.select_set(False);return o

def cylinder(name,a,b,r,style='dark',sides=10):
 a,b=Vector(a),Vector(b);bpy.ops.mesh.primitive_cylinder_add(vertices=sides,radius=r,depth=(b-a).length,location=(a+b)/2)
 o=bpy.context.object;o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('Z','Y');return finish(o,name,style)
def outline(name,points,depth,style='ivory',plane='XZ',offset=0,bevel=.002):
 # Extrude a silhouette normal to its two named coordinate axes.
 axes=['XYZ'.index(c) for c in plane];normal=next(i for i in range(3) if i not in axes);v=[]
 for d in [-depth/2,depth/2]:
  for xy in points:
   q=[0,0,0];q[axes[0]]=xy[0];q[axes[1]]=xy[1];q[normal]=offset+d;v.append(q)
 n=len(points);faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 me=bpy.data.meshes.new(name);me.from_pydata(v,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);return finish(o,name,style,bevel)
def ring(name,center,major,minor,style='gold',axis=(0,0,1)):
 bpy.ops.mesh.primitive_torus_add(major_segments=12,minor_segments=4,location=center,major_radius=major,minor_radius=minor)
 o=bpy.context.object;o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector(axis).to_track_quat('Z','Y');return finish(o,name,style)
def rod(name,maul=False):
 cylinder(name+'_shaft',(0,0,-.58),(0,0,.61),.018)
 cylinder(name+'_grip',(0,0,-.11),(0,0,.11),.027,'grip')
 for z in [-.55,-.30,-.12,.12,.29,.45,.57]:cylinder(name+'_collar',(0,0,z-.008),(0,0,z+.008),.023,'gold')
 cylinder(name+'_pommel',(0,0,-.62),(0,0,-.57),.023,'gold')
 cylinder(name+'_neck',(0,0,.57),(0,0,.66),.027,'dark')
 if maul:
  cylinder(name+'_core',(-.092,0,.67),(.092,0,.67),.043,'dark',12)
  for x in [-.065,-.032,0,.032,.065]:ring(name+'_coil',(x,0,.67),.043,.005,'glow',(1,0,0))
  pts=[(.086,.60),(.139,.602),(.161,.622),(.161,.721),(.141,.742),(.086,.742),(.073,.72),(.105,.70),(.105,.64),(.073,.622)]
 else:
  cylinder(name+'_core',(0,0,.65),(0,0,.72),.034,'dark',12)
  for z in [.661,.675,.689,.703]:ring(name+'_coil',(0,0,z),.034,.004,'glow')
  pts=[(.025,.625),(.072,.646),(.079,.742),(.060,.765),(.037,.752),(.045,.704),(.042,.664),(.021,.65)]
 for sign in [-1,1]:
  outline(name+'_contact_trim',[(sign*x,z) for x,z in pts],.068,'gold')
  cx=sum(x for x,z in pts)/len(pts);cz=sum(z for x,z in pts)/len(pts)
  outline(name+'_contact',[(sign*(cx+(x-cx)*.8),cz+(z-cz)*.89) for x,z in pts],.074,'ivory')
  z=.671 if maul else .72;x=sign*(.137 if maul else .061)
  cylinder(name+'_contact_light',(x,-.039,z),(x,-.043,z),.009,'glow',8)
 return {'grip_point':[0,0,0],'grip_axis':[0,0,1],'grip_radius_m':.027,'tip':[0,0,.67 if maul else .765]}

def pistol():
 cylinder('pistol_grip',(0,.026,-.072),(0,0,.067),.025,'grip',10)
 # The same blunt ceramic sidearm silhouette appears in the family and boss sheets.
 pts=[(-.245,.071),(-.253,.112),(-.232,.151),(-.047,.155),(.031,.125),(.035,.086),(-.013,.055),(-.091,.063),(-.12,.044),(-.18,.044)]
 outline('pistol_frame',pts,.075,'gold','YZ',bevel=.003)
 cy=sum(y for y,z in pts)/len(pts);cz=sum(z for y,z in pts)/len(pts)
 outline('pistol_ceramic',[(cy+(y-cy)*.93,cz+(z-cz)*.86) for y,z in pts],.081,'ivory','YZ',bevel=.003)
 cylinder('pistol_muzzle',(0,-.244,.105),(0,-.273,.105),.034,'dark',12)
 cylinder('pistol_bore',(0,-.274,.105),(0,-.276,.105),.023,'glow',12)
 for x in [-.043,.043]:
  cylinder('pistol_cell',(x,-.09,.085),(x*1.03,-.09,.085),.018,'gold',10)
  cylinder('pistol_cell_light',(x*1.04,-.09,.085),(x*1.06,-.09,.085),.011,'glow',10)
 # Open trigger guard with three bars; never fill the opening with a solid block.
 for a,b in [((0,-.029,-.034),(0,-.079,-.025)),((0,-.079,-.025),(0,-.1,.045)),((0,-.1,.045),(0,-.042,.067))]:cylinder('trigger_guard',a,b,.006,'gold',6)
 return {'grip_point':[0,0,0],'grip_axis':[0,-.18,.984],'grip_radius_m':.025,'muzzle':[0,-.278,.105]}

def saber():
 cylinder('saber_grip',(0,0,0),(0,0,.15),.024,'dark')
 for z in [.005,.06,.14]:cylinder('saber_hilt_ring',(0,0,z),(0,0,z+.008),.027,'gold')
 outline('saber_guard',[(-.075,-.006),(-.09,.025),(-.03,.035),(.04,.026),(.09,-.01),(.07,-.028),(.015,-.006)],.045,'gold')
 blade=[(-.025,-.015),(.031,-.02),(.048,-.16),(.055,-.35),(.047,-.51),(.008,-.67),(-.024,-.73),(-.018,-.52),(-.028,-.33),(-.035,-.14)]
 outline('saber_spine',blade,.021,'ivory',bevel=.001)
 outline('saber_plasma_edge',[(.027,-.02),(.041,-.16),(.049,-.35),(.041,-.51),(.003,-.66),(-.024,-.73),(-.010,-.64),(.027,-.50),(.034,-.35),(.027,-.17),(.018,-.02)],.025,'glow',bevel=0)
 ring('saber_mount',(0,.01,.11),.031,.006,'gold',(0,1,0))
 return {'hip_carried':True,'tip':[-.024,0,-.73]}
def key():
 ring('key_ring',(0,0,.068),.033,.005,'gold',(0,1,0))
 pts=[(-.009,.040),(.010,.040),(.010,-.045),(.031,-.045),(.031,-.060),(.010,-.060),(.010,-.077),(.025,-.077),(.025,-.093),(.010,-.093),(.010,-.112),(-.009,-.112)]
 outline('collar_key',pts,.014,'gold',bevel=.001)
 outline('key_inlay',[(-.004,.021),(.004,.021),(.004,-.093),(-.004,-.093)],.017,'glow',bevel=0)
 return {'belt_carried':True}
for name,make in [('collar_rod',lambda:rod('rod')),('arc_maul',lambda:rod('maul',True)),('pulse_pistol',pistol),('plasma_saber',saber),('collar_key',key)]:
 pieces=[];metadata=make()
 bpy.ops.object.select_all(action='DESELECT')
 for o in pieces:o.select_set(True)
 bpy.context.view_layer.objects.active=pieces[0];bpy.ops.object.join();o=bpy.context.object;o.name=o.data.name='OV_'+name
 bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
 tris=sum(len(f.vertices)-2 for f in o.data.polygons);assert 0<tris<1800,(name,tris)
 metadata['triangles']=tris;metadata['object']=o.name;records[name]=metadata
 bpy.ops.export_scene.gltf(filepath=str(P/'work'/f'{name}_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=False,export_extras=False)
 o.select_set(False)
(P/'work/equipment_info.json').write_text(json.dumps(records,indent=2)+'\n')
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/equipment.blend'))
print('EQUIPMENT_DONE',json.dumps(records),flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
