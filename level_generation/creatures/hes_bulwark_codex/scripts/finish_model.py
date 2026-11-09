"""Finish the shared machine and its separately skinned, state-switched coupling assembly."""
import json,math,sys
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
from geometry import select,shade,triangles
bpy.ops.wm.open_mainfile(filepath=str(P/'work/bulwark_textured_rig.blend'))
body=bpy.data.objects['Bulwark'];rig=bpy.data.objects['BulwarkRig'];scene=bpy.context.scene
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
def material(name,prefix):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.use_backface_culling=True
    n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    for kind in ('basecolor','normal','orm'):
        path=P/f'textures/{prefix}_{kind}.png'
        if not path.exists():continue
        im=bpy.data.images.load(str(path),check_existing=True);im.colorspace_settings.name='sRGB' if kind=='basecolor' else 'Non-Color'
        t=n.new('ShaderNodeTexImage');t.image=im
        if kind=='basecolor':l.new(t.outputs['Color'],p.inputs['Base Color'])
        elif kind=='normal':
            normal=n.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.8
            l.new(t.outputs['Color'],normal.inputs['Color']);l.new(normal.outputs['Normal'],p.inputs['Normal'])
        else:
            sep=n.new('ShaderNodeSeparateColor');l.new(t.outputs['Color'],sep.inputs['Color'])
            l.new(sep.outputs['Green'],p.inputs['Roughness']);l.new(sep.outputs['Blue'],p.inputs['Metallic'])
    return m
body.data.materials.clear()
for name in ('Armour','Trim','Resin'):body.data.materials.append(material('Bulwark_'+name,'bulwark'))
classes=np.load(P/'work/bulwark_face_materials.npy');assert len(classes)==len(body.data.polygons)
for face,c in zip(body.data.polygons,classes):face.material_index=int(c)
cablemat=material('Bulwark_Cable','bulwark_cable')
energy=bpy.data.materials.new('Bulwark_Energy');energy.use_nodes=True;energy.use_backface_culling=True
p=energy.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(.7,.08,.002,1);p.inputs['Roughness'].default_value=.45
p.inputs['Emission Color'].default_value=(.95,.18,.008,1);p.inputs['Emission Strength'].default_value=1

def mesh(name,verts,faces,uvs,weights,materials,indices=None):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    o=bpy.data.objects.new(name,me);scene.collection.objects.link(o)
    for mat in materials:me.materials.append(mat)
    uv=me.uv_layers.new(name='UVMap')
    for i,f in enumerate(me.polygons):
        f.material_index=indices[i] if indices else 0
        for li,co in zip(f.loop_indices,uvs[i]):uv.data[li].uv=co
    names={n for w in weights for n in w}
    for n in names:
        g=o.vertex_groups.new(name=n)
        for i,w in enumerate(weights):
            if w.get(n,0)>0:g.add([i],w[n],'REPLACE')
    shade(o);return o

def lathe(name,centre,axis,profile,band,bone,segments=12,mat=cablemat):
    # Closed radial profile; no fan poles or implicit n-gon triangulation.
    centre=Vector(centre);axis=Vector(axis).normalized();x=Vector((1,0,0))
    if abs(axis.dot(x))>.8:x=Vector((0,1,0))
    x=(x-axis*axis.dot(x)).normalized();y=axis.cross(x)
    verts=[tuple(centre+axis*d+(x*math.cos(2*math.pi*j/segments)+y*math.sin(2*math.pi*j/segments))*r) for d,r in profile for j in range(segments)]
    faces=[];uvs=[]
    for k in range(len(profile)):
        for j in range(segments):
            a=k*segments+j;b=k*segments+(j+1)%segments;c=((k+1)%len(profile))*segments+(j+1)%segments;d=((k+1)%len(profile))*segments+j
            faces.extend([(a,b,c),(a,c,d)]);u0,u1=band[0]+(band[1]-band[0])*j/segments,band[0]+(band[1]-band[0])*(j+1)/segments;v0,v1=.05+.9*k/len(profile),.05+.9*(k+1)/len(profile)
            uvs.extend([[(u0,v0),(u1,v0),(u1,v1)],[(u0,v0),(u1,v1),(u0,v1)]])
    return mesh(name,verts,faces,uvs,[{bone:1} for _ in verts],[mat])

# Space the returned side sockets apart to restore the concept's third, centre coupling.
components=body.data.attributes['source_component'].data
ports=[];repairs=[]
for component in (93,27):
    ids=sorted({v for f in body.data.polygons if components[f.index].value==component for v in f.vertices})
    co=np.array([body.data.vertices[v].co[:] for v in ids]);delta=math.copysign(.14,float(co[:,0].mean()))
    for v in ids:body.data.vertices[v].co.x+=delta
    co[:,0]+=delta;rim=co[co[:,1]>co[:,1].max()-.07]
    pos=np.array([(rim[:,0].min()+rim[:,0].max())/2,co[:,1].max()-.03,(rim[:,2].min()+rim[:,2].max())/2])
    ports.append(pos);repairs.append({'component':component,'translation_x_m':delta,'port':pos.tolist()})
ports.sort(key=lambda p:p[0]);centre=np.mean(ports,axis=0);centre[0]=0;ports.insert(1,centre)
extra=[]
extra.append(lathe('CentreCoupling',centre,(0,1,0),[(-.10,.17),(-.10,.24),(.04,.24),(.07,.21),(.07,.135),(-.1,.135)],(.71,.96),'B_Barrel'))
# Recessed energy discs, including the two large side cores.
for row in ('Upper','Lower'):
    pos=rig.data.bones['Socket_Muzzle_'+row].head_local.copy();pos.y+=.075
    extra.append(lathe('MuzzleGlow_'+row,pos,(0,-1,0),[(-.012,.012),(-.012,.125),(.0,.125),(.0,.012)],(.1,.9),'B_Recoil_'+row,12,energy))
for side in (-1,1):
    extra.append(lathe('FlankCore',(.98*side,.058,2.484),(side,0,0),[(-.025,.012),(-.025,.20),(.0,.20),(.0,.012)],(.1,.9),'B_Barrel',12,energy))
select([body]+extra);bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
body.name=body.data.name='Bulwark';body.data.update()

# Curved resin hoses. The upper section follows the head; lower bends and plugs stay in root space.
from mathutils.geometry import interpolate_bezier
cable_parts=[];paths=[]
for i,start in enumerate(ports):
    end=Vector((start[0]*1.8,5.6+(.2 if i==1 else 0),.22))
    p0=Vector(start);p1=p0+Vector((0,.9,0));p2=Vector((end.x,3.65,.11));p3=end-Vector((0,.48,0))
    points=[Vector(p) for p in interpolate_bezier(p0,p1,p2,p3,17)]
    paths.append([list(p) for p in points]);verts=[];weights=[];uvs=[];faces=[];r=.10
    frames=[]
    for k,point in enumerate(points):
        tangent=(points[min(k+1,16)]-points[max(k-1,0)]).normalized();x=Vector((1,0,0));x=(x-tangent*x.dot(tangent)).normalized();y=tangent.cross(x);frames.append((x,y))
        w=max(0,min(1,(point.z-.55)/(p0.z-.55)));w=w*w*(3-2*w)
        for j in range(8):
            q=point+r*(x*math.cos(j*math.tau/8)+y*math.sin(j*math.tau/8));verts.append(tuple(q));weights.append({'B_Barrel':w,'B_Root':1-w})
    for k in range(16):
        for j in range(8):
            a=k*8+j;b=k*8+(j+1)%8;c=(k+1)*8+(j+1)%8;d=(k+1)*8+j
            faces.extend([(a,b,c),(a,c,d)]);u0=.035+.24*j/8;u1=.035+.24*(j+1)/8;v0=.035+.93*k/16;v1=.035+.93*(k+1)/16
            uvs.extend([[(u0,v0),(u1,v0),(u1,v1)],[(u0,v0),(u1,v1),(u0,v1)]])
    cable_parts.append(mesh('Hose_'+str(i),verts,faces,uvs,weights,[cablemat]))
    # Two narrow raised filaments, actual emissive geometry rather than an emissive texture.
    for theta in (-math.pi/2-.65,-math.pi/2+.65):
        v=[];w=[];f=[];uv=[]
        for k,point in enumerate(points):
            x,y=frames[k];weight=max(0,min(1,(point.z-.55)/(p0.z-.55)));weight=weight*weight*(3-2*weight)
            for a in (theta-.09,theta+.09):
                v.append(tuple(point+.101*(x*math.cos(a)+y*math.sin(a))));w.append({'B_Barrel':weight,'B_Root':1-weight})
        for k in range(16):
            f.extend([(2*k,2*k+1,2*k+3),(2*k,2*k+3,2*k+2)]);uv.extend([[(0,0),(1,0),(1,1)],[(0,0),(1,1),(0,1)]])
        cable_parts.append(mesh('Filament',v,f,uv,w,[energy]))
    plugcentre=end-Vector((0,.15,0))
    cable_parts.append(lathe('Plug',plugcentre,(0,1,0),[(-.42,.12),(-.34,.20),(-.05,.20),(.02,.15),(.02,.09),(-.42,.09)],(.38,.62),'B_Root',8))
    for yoffset in (-.34,-.05):
        cable_parts.append(lathe('PlugBand',plugcentre+Vector((0,yoffset,0)),(0,1,0),[(-.025,.195),(-.025,.22),(.025,.22),(.025,.195)],(.71,.96),'B_Root',8))
    cable_parts.append(lathe('PortSleeve',p0,(0,1,0),[(-.06,.09),(-.06,.13),(.12,.13),(.12,.09)],(.71,.96),'B_Barrel',8))
select(cable_parts);bpy.context.view_layer.objects.active=cable_parts[0];bpy.ops.object.join();cables=bpy.context.object;cables.name=cables.data.name='Bulwark_Cables'
mod=cables.modifiers.new('Rig','ARMATURE');mod.object=rig;cables.parent=rig
# Root-space static copy is useful to the map integrator; runtime uses this separate skinned mesh in the shared GLB.
select([cables]);bpy.ops.export_scene.gltf(filepath=str(P/'export/hes_bulwark_cables.glb'),use_selection=True,export_format='GLB',export_yup=True,export_skins=False,export_animations=False,export_attributes=False)
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];scene.frame_set(0)
select([body,cables,rig]);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/bulwark_final_rig.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'export/hes_bulwark_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
report={'body_triangles':triangles(body),'cable_triangles':triangles(cables),'ports':list(map(lambda x:list(map(float,x)),ports)),'side_socket_repairs':repairs,'cable_paths':paths,'cable_skin':'head at sockets, root at floor and plugs','raw_geometry_unchanged':True}
(P/'review/geometry/finish_geometry.json').write_text(json.dumps(report,indent=2)+'\n');print('FINISHED',report['body_triangles'],report['cable_triangles'],report['ports'],flush=True)
