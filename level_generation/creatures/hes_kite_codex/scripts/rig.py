"""Anatomical skin domains keep the four membrane pairs, neck and tail independent."""
import bpy, bmesh, math, json, os, sys, traceback
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'claude_shared'))
from uv_head_density import scale_head_islands


def main():
    bpy.ops.wm.open_mainfile(filepath=str(P/'work/geometry_v3.blend'))
    mesh=bpy.data.objects['Ashkite']
    info=json.loads((P/'review/geometry_v3.json').read_text())
    lift=info['ground_translation']; scale=info['scale_provisional']
    def body_point(p):
        return Vector(p)*scale+Vector((0,0,lift))
    def wing_point(raw,part):
        v=Vector(raw); sign=1 if part.endswith('L') else -1
        root=Vector((sign*.07,-.205,-.07))
        weight=min(1,max(0,(abs(v.x)-.06)/.08))
        v=v.lerp(root+Matrix.Rotation(math.radians(sign*34),3,'Y')@(v-root),weight)
        if part.startswith('Rear'):
            d=v-root;d.x*=.83;d.y*=.72;d.z*=.83
            v=Vector((sign*.065,-.045,-.105))+Matrix.Rotation(math.radians(sign*20),3,'Z')@d
        return body_point(v)
    bones={}
    def add(name,parent,a,b): bones[name]=(parent,Vector(a),Vector(b))
    add('Spine1',None,body_point((0,-.05,-.135)),body_point((0,-.22,-.10)))
    add('Neck1','Spine1',body_point((0,-.22,-.10)),body_point((0,-.38,-.075)))
    add('Neck2','Neck1',body_point((0,-.38,-.075)),body_point((0,-.53,.055)))
    add('Head','Neck2',body_point((0,-.53,.055)),body_point((0,-.705,.055)))
    tail=[(0,-.05,-.135),(0,.06,-.14),(0,.17,-.14),(0,.28,-.135),
          (0,.39,-.13),(0,.5,-.12),(0,.6,-.12),(0,.69,-.15)]
    for i in range(7):add('Tail'+str(i+1),'Spine1' if i==0 else 'Tail'+str(i),body_point(tail[i]),body_point(tail[i+1]))
    wing_names={}
    for side,sign in [('L',1),('R',-1)]:
        leg=[(sign*.055,-.11,-.175),(sign*.105,-.045,-.26),
             (sign*.075,-.15,-.38),(sign*.075,-.235,-.43)]
        for i,n in enumerate(['Thigh','Shin','Foot']):
            add(n+'_'+side,'Spine1' if i==0 else ['Thigh','Shin'][i-1]+'_'+side,
                body_point(leg[i]),body_point(leg[i+1]))
        for pair in ['Front','Rear']:
            part=pair+'_'+side
            wp=lambda p:wing_point((sign*p[0],p[1],p[2]),part)
            root=wp((.07,-.205,-.07)); elbow=wp((.35,-.31,.18)); wrist=wp((.60,-.24,.35))
            names=[part+'_'+n for n in ['Upper','Fore','Finger1','Finger2','Finger3']]
            add(names[0],'Spine1',root,elbow);add(names[1],names[0],elbow,wrist)
            add(names[2],names[1],wrist,wp((.95,-.06,.45)))
            add(names[3],names[1],wrist,wp((.65,.025,.37)))
            add(names[4],names[0],elbow,wp((.35,-.03,.15)))
            wing_names[part]=names
    arm=bpy.data.armatures.new('Ashkite_Rig');rig=bpy.data.objects.new('Ashkite_Rig',arm)
    bpy.context.collection.objects.link(rig)
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
    bpy.ops.object.mode_set(mode='EDIT')
    for name,(parent,a,b) in bones.items():
        bone=arm.edit_bones.new(name);bone.head=a;bone.tail=b;bone.align_roll(Vector((0,0,1)))
        if parent:bone.parent=arm.edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT')
    # Keep source domains for attachments and audits; they are not deforming bones.
    parts={g.index:g.name.removeprefix('part_') for g in mesh.vertex_groups}
    domains=[parts[max(v.groups,key=lambda g:g.weight).group] for v in mesh.data.vertices]
    groups={n:mesh.vertex_groups.new(name=n) for n in bones}
    for v,part in zip(mesh.data.vertices,domains):
        raw=(v.co-Vector((0,0,lift)))/scale
        if part!='Body':
            candidates=list(wing_names[part])
            if abs(raw.x)<.20:
                candidates+=['Spine1','Neck1','Neck2'] if part.startswith('Front') else ['Spine1','Tail1']
        elif raw.y < -.48:
            candidates=['Head','Neck2']
        elif raw.y < -.30:
            candidates=['Neck1','Neck2','Head']
        elif raw.y > -.015:
            candidates=['Spine1']+['Tail'+str(i) for i in range(1,8)]
        elif raw.z < -.20 and abs(raw.x)>.025:
            side='L' if raw.x>0 else 'R'
            candidates=['Spine1','Thigh_'+side,'Shin_'+side,'Foot_'+side]
        else:candidates=['Spine1','Neck1','Tail1']
        ds=[]
        for n in candidates:
            a,b=bones[n][1:];d=b-a;t=max(0,min(1,(v.co-a).dot(d)/d.length_squared))
            ds.append(((v.co-(a+d*t)).length,n))
        ds=sorted(ds)[:4]
        ws=np.array([(d+.025)**-4 for d,n in ds]);ws/=ws.sum()
        for (_,n),w in zip(ds,ws):groups[n].add([v.index],float(w),'REPLACE')
    # Identical cut-edge positions must share deformation weights to keep the shoulder watertight.
    coincident={}
    for v in mesh.data.vertices:coincident.setdefault(tuple(round(c,5) for c in v.co),[]).append(v)
    for vs in coincident.values():
        if len(vs)<2:continue
        weights={}
        for v in vs:
            for g in v.groups:
                name=mesh.vertex_groups[g.group].name
                if name in bones:weights[name]=weights.get(name,0)+g.weight/len(vs)
        selected=sorted(weights.items(),key=lambda x:-x[1])[:4];total=sum(w for _,w in selected)
        for v in vs:
            for g in groups.values():g.remove([v.index])
            for n,w in selected:groups[n].add([v.index],w/total,'REPLACE')
    mod=mesh.modifiers.new('Armature','ARMATURE');mod.object=rig;mesh.parent=rig
    assert all(abs(sum(g.weight for g in v.groups if mesh.vertex_groups[g.group].name in bones)-1)<1e-5 for v in mesh.data.vertices)
    bpy.ops.object.select_all(action='DESELECT');mesh.select_set(True);bpy.context.view_layer.objects.active=mesh
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.004,area_weight=0,scale_to_bounds=False)
    scale_head_islands(mesh,('Head',),factor=2.5)
    bpy.ops.uv.select_all(action='SELECT');bpy.ops.uv.pack_islands(rotate=True,margin=.003,margin_method='FRACTION',shape_method='CONCAVE')
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v3.blend'))
    # The same UV layout is used by the static texture upload and the animated master.
    dup=mesh.copy();dup.data=mesh.data.copy();dup.parent=None;dup.modifiers.clear();dup.vertex_groups.clear()
    bpy.context.collection.objects.link(dup)
    bpy.ops.object.select_all(action='DESELECT');dup.select_set(True);bpy.context.view_layer.objects.active=dup
    bpy.ops.export_scene.gltf(filepath=str(P/'work/texture_upload_v3.glb'),use_selection=True,export_format='GLB',
                              export_animations=False,export_skins=False,export_attributes=False)
    mesh.data.calc_loop_triangles();uv=mesh.data.uv_layers.active.data
    np.savez_compressed(P/'work/surface_v3.npz',positions=np.array([tuple(v.co) for v in mesh.data.vertices]),
        triangles=np.array([tuple(t.vertices) for t in mesh.data.loop_triangles]),
        uv=np.array([[tuple(uv[l].uv) for l in t.loops] for t in mesh.data.loop_triangles]),
        domains=np.array(domains))
    report={'bones':{n:{'parent':p,'head':list(a),'tail':list(b)} for n,(p,a,b) in bones.items()},
            'vertices':len(mesh.data.vertices),'unweighted':0,'max_influences':4,'head_uv_density_multiplier':2.5,
            'library_selection':'Stored fly clips are biped Floating/Flying. Four-wing membrane/neck/tail anatomy requires local flyer clips.'}
    (P/'review/rig_v3.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RIG',len(bones),'bones, zero unweighted vertices; upload ready',flush=True)

try:main()
except BaseException:traceback.print_exc();sys.stderr.flush();os._exit(1)
sys.stdout.flush();os._exit(0)
