"""Posed GLB render with backfaces in red (EEVEE, Geometry Backfacing). Args: <glb> <out prefix> <clip> <seconds> <spec>... spec name:dx,dy,dz:cx,cy,cz:ortho (Blender axes)"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
sc = bpy.context.scene
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
act = bpy.data.actions[a[2]] if a[2] in bpy.data.actions else next(x for x in bpy.data.actions if x.name.startswith(a[2]))
rig.animation_data_create(); rig.animation_data.action = act
if getattr(act, 'slots', None) is not None and len(act.slots): rig.animation_data.action_slot = act.slots[0]
sc.frame_set(int(float(a[3]) * 24))
m = bpy.data.materials.new('bf'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
out = nt.nodes.new('ShaderNodeOutputMaterial'); mix = nt.nodes.new('ShaderNodeMixShader'); geo = nt.nodes.new('ShaderNodeNewGeometry')
d = nt.nodes.new('ShaderNodeBsdfDiffuse'); d.inputs['Color'].default_value = (0.7, 0.7, 0.7, 1); e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (1, 0, 0, 1)
nt.links.new(geo.outputs['Backfacing'], mix.inputs['Fac']); nt.links.new(d.outputs[0], mix.inputs[1]); nt.links.new(e.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], out.inputs['Surface'])
for o in bpy.data.objects:
    if o.type == 'MESH':
        if 'LOD' in o.name and 'LOD0' not in o.name: o.hide_render = True
        for i in range(len(o.data.materials)): o.data.materials[i] = m
sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [x.identifier for x in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
sc.render.resolution_x = sc.render.resolution_y = 600
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.3, 0.3, 0.35, 1)
ld = bpy.data.lights.new('L', 'SUN'); ld.energy = 3; lo = bpy.data.objects.new('L', ld); sc.collection.objects.link(lo); lo.rotation_euler = (0.6, 0.2, 0.3)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
for s in a[4:]:
    n, dd, c, o = s.split(':'); dd = Vector([float(x) for x in dd.split(',')]).normalized(); c = Vector([float(x) for x in c.split(',')])
    cd.ortho_scale = float(o); cam.location = c + dd * 6; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{n}.png'; bpy.ops.render.render(write_still=True)
print('BF done')
