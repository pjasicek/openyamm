import bpy,bmesh,sys,colorsys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/draw_hook_trial.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];scene=bpy.context.scene
bm=bmesh.new();bm.from_mesh(body.data);pl=bm.verts.layers.int['piece']
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[pl]!=5],context='VERTS');bm.to_mesh(body.data);bm.free()
common.workbench_clay(scene)
body.data.materials.clear()
for i in range(16):
    mat=bpy.data.materials.new('Bone'+str(i));mat.diffuse_color=(*colorsys.hsv_to_rgb((i//3)/5,.45,.7+(.1*(i%3))),1);body.data.materials.append(mat)
names=['B_R_Finger0','B_R_Finger0.001','B_R_Finger0.002']+[f'B_R_Finger{i}{s}' for i in range(1,5)for s in ['','1','2']]+['B_R_Hand']
for f in body.data.polygons:
    weights={n:0 for n in names}
    for i in f.vertices:
        for g in body.data.vertices[i].groups:
            n=body.vertex_groups[g.group].name
            if n in weights:weights[n]+=g.weight
    f.material_index=names.index(max(weights,key=weights.get))
for name,f in [('rest',None),('hook',25)]:
    rig.animation_data.action=bpy.data.actions['Attack'] if f else None
    if f:
        rig.animation_data.action_slot=rig.animation_data.action.slots[0];scene.frame_set(f)
    else:
        for b in rig.pose.bones:b.matrix_basis.identity()
    bpy.context.view_layer.update();lo,hi=common.world_bounds([body]);c=(lo+hi)*.5
    common.render_views(str(P/f'review/isolated_hand_{name}'),c.z,.34,
        views=('front','left','back','right','three_quarter'),resolution=(650,650),target=(c.x,c.y))
