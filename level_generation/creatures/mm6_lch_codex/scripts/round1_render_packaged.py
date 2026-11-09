"""Measure the actual packaged meshes against accepted LOD0 at identical eight-view cameras."""
import bpy,json,sys,math,copy,subprocess,os
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];R=P/'review/triangle_reduction';sys.dont_write_bytecode=True
sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb
camera=json.loads((R/'camera.json').read_text());report=[]
for level in range(4):
    for label,path in [('baseline',R/'baseline/export/mm6_lch.glb'),('final',P/'export/mm6_lch.glb')]:
        d,b=read_glb(path);node=next(n for n in d['nodes']if n.get('name')=='Lich')
        mi=node['mesh'] if label=='baseline' or level==0 else d['meshes'][node['mesh']]['extras']['openyamm_lods'][level-1]
        d['meshes']=[copy.deepcopy(d['meshes'][mi])];d['meshes'][0].pop('extras',None);node['mesh']=0
        tmp=P/'work/round1/metric_import.glb';write_glb(tmp,d,b)
        bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(tmp))
        body=bpy.data.objects['Lich'];rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');sc=bpy.context.scene
        act=bpy.data.actions['Standing'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
        sc.render.fps=30;sc.frame_set(0)
        for ob in bpy.data.objects:ob.hide_render=ob not in (body,rig)
        for mat in body.data.materials:
            bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
            tex=bs.inputs['Base Color'].links[0].from_node;mat.node_tree.nodes.active=tex
        sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='TEXTURE'
        sc.display.shading.show_cavity=False;sc.display.shading.show_shadows=False;sc.render.film_transparent=True
        sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
        sc.render.resolution_x=sc.render.resolution_y=960;sc.render.resolution_percentage=100;sc.display.render_aa='32';sc.view_settings.view_transform='Standard'
        cd=bpy.data.cameras.new('ComparisonCamera');cd.type='PERSP';cd.lens_unit='FOV';cd.angle=math.radians(35)
        cam=bpy.data.objects.new('ComparisonCamera',cd);sc.collection.objects.link(cam);sc.camera=cam
        dest=R/f'packaged/{label}/lod{level}';dest.mkdir(parents=True,exist_ok=True)
        for k in range(8):
            ang=k*math.pi/4;target=Vector((0,.15,.9));cam.location=target+Vector((math.sin(ang),-math.cos(ang),0))*camera['distance_m'][level]
            cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(dest/f'{k}.png');bpy.ops.render.render(write_still=True)
    dest=R/f'packaged/final/lod{level}'
    subprocess.run(['/usr/bin/python3',str(P/'scripts/round1_metrics.py'),str(dest),str(R/f'packaged/baseline/lod{level}')],check=True,env=dict(os.environ,LCH_IOU_AGGREGATION='pooled'))
    metrics=json.loads((dest/'metrics.json').read_text());report.append(metrics);print('PACKAGED_METRIC',level,metrics['pass'],metrics['min_iou'],metrics['pooled_iou'],metrics['min_ssim'],flush=True)
(R/'packaged_metrics.json').write_text(json.dumps(report,indent=2)+'\n')
assert all(r['pass']for r in report),[(i,r['pooled_iou'],r['min_ssim'])for i,r in enumerate(report)if not r['pass']]
