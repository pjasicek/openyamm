import bpy, sys, os, json
from mathutils import Vector
argv = sys.argv[sys.argv.index('--')+1:]
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
bpy.ops.import_scene.gltf(filepath=argv[0])
arm = [o for o in bpy.data.objects if o.type=='ARMATURE'][0]
print('ARM', arm.name, len(arm.data.bones))
for b in arm.data.bones:
    print('BONE', b.name, 'parent', b.parent.name if b.parent else None, 'head', tuple(round(x,3) for x in (arm.matrix_world@b.head_local)), 'len', round(b.length,3))
for o in bpy.data.objects:
    if o.type=='MESH':
        me=o.data
        zs=[(o.matrix_world@v.co).z for v in me.vertices]
        print('MESH', o.name, len(me.vertices), len(me.polygons), 'z', round(min(zs),3), round(max(zs),3), 'mats', [m.name for m in me.materials])
        if o.name.endswith('Mesh') or 'LOD' not in o.name and 'Shadow' not in o.name:
            cnt={}
            for v in me.vertices:
                for g in v.groups:
                    if g.weight>0.3: cnt[o.vertex_groups[g.group].name]=cnt.get(o.vertex_groups[g.group].name,0)+1
            print('GROUPS', o.name, sorted(cnt.items(), key=lambda x:-x[1]))
print('ACTIONS', [(a.name, a.frame_range[:]) for a in bpy.data.actions])
print('FPS', bpy.context.scene.render.fps)
