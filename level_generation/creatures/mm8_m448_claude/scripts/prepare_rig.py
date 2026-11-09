from pathlib import Path
import bpy, bmesh, json, sys
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/body_head_v1.blend'))
body=bpy.data.objects['Body']
bm=bmesh.new();bm.from_mesh(body.data)
piece=bm.verts.layers.int['piece']
edges=[e for e in bm.edges if e.is_boundary and all(v[piece]==200 for v in e.verts)]
seen=set();loops=[]
for e in edges:
    if e in seen:continue
    stack=[e];group=[]
    while stack:
        x=stack.pop()
        if x in seen:continue
        seen.add(x);group.append(x)
        stack.extend(y for v in x.verts for y in v.link_edges if y in edges and y not in seen)
    vs=set(v for e in group for v in e.verts)
    lo=[min(v.co[i] for v in vs) for i in range(3)];hi=[max(v.co[i] for v in vs) for i in range(3)]
    loops.append({'edges':len(group),'lo':lo,'hi':hi})
print('HEAD_BOUNDARIES',json.dumps(loops))
bm.free()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
# Provisional material/UV satisfies Meshy's rigging input; final UVs follow weighting/reduction.
mat = bpy.data.materials.new('Provisional');mat.use_nodes=True
image = bpy.data.images.new('provisional', width=2, height=2)
image.pixels[:] = [0.5,0.5,0.5,1.0] * 4
node = mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=image
mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
body.data.materials.append(mat)
if not body.data.uv_layers:body.data.uv_layers.new(name='UVMap')
for o in bpy.data.objects:o.select_set(o == body)
(p/'export').mkdir(exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(p/'export/body_for_rig.glb'),use_selection=True,
                         export_format='GLB',export_animations=False,export_skins=False,export_attributes=False)
