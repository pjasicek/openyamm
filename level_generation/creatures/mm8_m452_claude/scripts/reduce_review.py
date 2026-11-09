"""Progressive 10% reduction candidates, preserving the head, paws, tail, UVs and skin weights."""
import bpy,bmesh,os,sys,json
import numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
HERE=str(Path(__file__).resolve().parents[1]);P=Path(HERE);T=str(P/'textures')
sys.path.insert(0,str(P/'scripts'))
from common_rat import render_ortho
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'))
mesh=bpy.data.objects['Rat'];rig=bpy.data.objects['Rat_Rig'];sc=bpy.context.scene
mat = bpy.data.materials.new('Rat_Palette452'); mat.use_nodes = True; nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
def tex(name, cs):
    img = bpy.data.images.load(os.path.join(T, name)); img.colorspace_settings.name = cs
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; return n
bc = tex('rat_basecolor_graded.png', 'sRGB'); nt.links.new(bc.outputs['Color'], bsdf.inputs['Base Color'])
nm = tex('rat_normal.png', 'Non-Color'); nmap = nt.nodes.new('ShaderNodeNormalMap')
nt.links.new(nm.outputs['Color'], nmap.inputs['Color']); nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
mr = tex('rat_metal_rough.png', 'Non-Color'); sep = nt.nodes.new('ShaderNodeSeparateColor')
nt.links.new(mr.outputs['Color'], sep.inputs['Color'])
nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
mesh.data.materials.clear(); mesh.data.materials.append(mat)
nt.nodes.active=bc

rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_hi.blend'))
source=mesh;source.name='Rat_High'
def evaluated(obj):
    bm=bmesh.new();bm.from_object(obj,bpy.context.evaluated_depsgraph_get());bm.transform(obj.matrix_world)
    return bm
def triangles(obj):return sum(len(f.vertices)-2 for f in obj.data.polygons)
def boundary(obj):
    bm=bmesh.new();bm.from_mesh(obj.data);n=sum(e.is_boundary for e in bm.edges);bm.free();return n
poses=[('Standing',0),('Walking',.25),('Walking',.75),('Running',.3),('Attack',.30),('Attack',.50),('Attack',.65),('Hit',.125),('Death',.40),('Death',.75)]
report={'source_triangles':triangles(source),'source_boundary_edges':boundary(source),'candidates':{}}
objects={'high':source}
for step in range(1,9):
    ratio=.9**step;tag=f'r{round(ratio*100):02d}'
    rig.animation_data.action=None
    for b in rig.pose.bones:b.matrix_basis.identity()
    bpy.context.view_layer.update()
    c=source.copy();c.data=source.data.copy();c.name='Rat_'+tag;sc.collection.objects.link(c)
    for m in list(c.modifiers):c.modifiers.remove(m)
    for o in bpy.data.objects:o.select_set(o==c)
    bpy.context.view_layer.objects.active=c
    d=c.modifiers.new('Reduce','DECIMATE');d.ratio=ratio;d.use_collapse_triangulate=True
    # Unbiased collapse retains the curved torso better than forcing triangles into dense paws.
    d.vertex_group=''
    bpy.ops.object.modifier_apply(modifier=d.name)
    bpy.ops.object.vertex_group_limit_total(limit=4);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    arm=c.modifiers.new('Skin','ARMATURE');arm.object=rig
    distances=[];min_z=1.0
    for clip,t in poses:
        rig.animation_data.action=bpy.data.actions[clip];sc.frame_set(1+round(t*24))
        a,b=evaluated(source),evaluated(c);ta,tb=BVHTree.FromBMesh(a),BVHTree.FromBMesh(b)
        distances.extend(tb.find_nearest(v.co)[3] for v in a.verts)
        distances.extend(ta.find_nearest(v.co)[3] for v in b.verts)
        min_z=min(min_z,min(v.co.z for v in b.verts));a.free();b.free()
    report['candidates'][tag]={'ratio':ratio,'triangles':triangles(c),'boundary_edges':boundary(c),
        'max_surface_error_m':max(distances),'p99_surface_error_m':float(np.quantile(distances,.99)),'min_z_m':min_z}
    objects[tag]=c;c.hide_render=True
    print(tag,report['candidates'][tag],flush=True)
for tag in ['high','r53','r43']:
    obj=objects[tag];original=obj.name;obj.name='Rat'
    for clip,t in [('Standing',0),('Attack',.3),('Death',.75)]:
        rig.animation_data.action=bpy.data.actions[clip];sc.frame_set(1+round(t*24))
        for view,loc in [('side',(3,0,.18)),('quarter',(2,-3,1.2))]:
            render_ortho(loc,(0,-.05,.20),1.22,str(P/f'review/reduce_{tag}_{clip}_{view}.png'),res=(1000,720),textured=True)
    obj.name=original
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1)
source.name='Rat_High'
(P/'work/reduction.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/reduction.blend'))
