"""Step 1 for a batch-B Smart Topology return (work/st_v1_parts.blend, loose parts P00.., 1.7 m, faces -Y):
join every part into 'Body' with the 'piece' point attribute (part index), 'garment' (label below) and 'orig_co';
give it a neutral textured material (Meshy's rigging wants a textured humanoid) and export the PERSON only (no
crescent, back frame, banners or beads: the two banners read as extra limbs to an auto-rig) to work/body_for_rig.glb.
Garments: creature.json (numbering in cfg.py).
Args: none"""
import bpy, os, sys, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import cfg
G, LAB, BACK = cfg.GARMENTS, cfg.LAB, cfg.NOT_IN_RIG
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'st_v1_parts.blend'))
parts = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
assert set(LAB) == set(range(len(parts))), ('unlabelled pieces', sorted(set(range(len(parts))) - set(LAB)))
for o in bpy.data.objects:
    o.select_set(False)
for n, o in parts.items():
    i = int(n[1:])
    o.data.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', [i] * len(o.data.vertices))
    o.data.attributes.new('garment', 'INT', 'POINT').data.foreach_set('value', [LAB[i]] * len(o.data.vertices))
    o.data.materials.clear(); o.select_set(True)
bpy.context.view_layer.objects.active = parts['P00']
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = body.data.name = 'Body'
me = body.data
co = np.array([tuple(v.co) for v in me.vertices])
SP = cfg.C.get('split_piece')
if SP:                                               # a fused shell split by height (warlock: gown + cape below)
    pcv = np.zeros(len(co), np.int32); me.attributes['piece'].data.foreach_get('value', pcv)
    gv0 = np.zeros(len(co), np.int32); me.attributes['garment'].data.foreach_get('value', gv0)
    low = (pcv == SP['piece']) & (co[:, 2] < SP['below_z'])
    if 'reach_z' in SP:                              # necromancer: only the components below the split that reach the
        adj = {}                                     # floor (the cape); the hands below the split stay garment 1
        for e in me.edges:
            i, j = e.vertices
            if low[i] and low[j]:
                adj.setdefault(i, []).append(j); adj.setdefault(j, []).append(i)
        comp = -np.ones(len(co), np.int64); nc = 0
        for v0 in np.where(low)[0]:
            if comp[v0] >= 0:
                continue
            st = [int(v0)]
            while st:
                x = st.pop()
                if comp[x] >= 0:
                    continue
                comp[x] = nc; st += adj.get(x, [])
            nc += 1
        keep = [c for c in range(nc) if co[comp == c, 2].min() >= SP['reach_z']]
        low &= ~np.isin(comp, keep)
        print('PREP split kept above-floor components', [int((comp == c).sum()) for c in keep])
    gv0[low] = SP['garment']
    TH = cfg.C.get('tight_hem')
    if TH:                                           # necromancer: the tunic hem below the split hugs the hips and
        from mathutils.kdtree import KDTree          # thighs (and its front flap hangs over them): it keeps Meshy's
        lg = np.where(pcv == TH['near_piece'])[0]    # hip/thigh weights (garment 17) instead of robe chains, which
        kd = KDTree(len(lg))                         # swung it like a loose skirt through the thighs
        for k_, i_ in enumerate(lg):
            kd.insert(co[i_], k_)
        kd.balance()
        near = np.array([kd.find(co[i_])[2] for i_ in range(len(co))])
        hem = (pcv == SP['piece']) & (gv0 == SP['garment']) & (near < TH['r']) & (co[:, 2] > TH['min_z'])
        hem |= np.isin(pcv, TH.get('whole_pieces', []))
        gv0[hem] = TH['garment']
        print('PREP tight hem verts', int(hem.sum()))
    me.attributes['garment'].data.foreach_set('value', gv0)
me.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', co.ravel())
mat = bpy.data.materials.new('RigNeutral'); mat.use_nodes = True
img = bpy.data.images.new('RigNeutral', width=4, height=4); img.pixels = [.55, .5, .45, 1] * 16; img.pack()
node = mat.node_tree.nodes.new('ShaderNodeTexImage'); node.image = img
mat.node_tree.links.new(node.outputs['Color'], mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
me.materials.append(mat)
if not me.uv_layers:
    me.uv_layers.new(name='UVMap')
for uv in me.uv_layers.active.data:
    uv.uv = (.5, .5)
gv = np.zeros(len(co), np.int32); me.attributes['garment'].data.foreach_get('value', gv)
print('PREP verts', len(co), 'tris', sum(len(p.vertices) - 2 for p in me.polygons), 'height', round(float(co[:, 2].max() - co[:, 2].min()), 3),
      'garments', {g: int((gv == g).sum()) for g in G})
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'step1.blend'))
# person-only copy for the auto-rig
cp = body.copy(); cp.data = body.data.copy(); bpy.context.scene.collection.objects.link(cp)
import bmesh
bm = bmesh.new(); bm.from_mesh(cp.data); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[v for v in bm.verts if gv[v.index] in BACK], context='VERTS')
bm.to_mesh(cp.data); bm.free()
for o in bpy.data.objects:
    o.select_set(o == cp)
bpy.context.view_layer.objects.active = cp
bpy.ops.export_scene.gltf(filepath=os.path.join(common.WORK, 'body_for_rig.glb'), use_selection=True, export_format='GLB',
                          export_animations=False, export_skins=False, export_attributes=False, export_yup=True)
print('PREP rig upload verts', len(cp.data.vertices))
