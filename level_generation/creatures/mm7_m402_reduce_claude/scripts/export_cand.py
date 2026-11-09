"""Reduced candidate (work/ladder.blend, REA_CAND, default Cand_55) + rig -> work/cand_export.glb: skinned geometry
only (4 influences, 8 with REA_INFLUENCES=8; no clips), the mesh node named like the installed one so swap_lod0.py can check transforms.
MM7 Spider options:
- REA_FIX_CARDS=1: the fringe cards of work/cards.npz (card_list.py) take, rigidly, the weights of the leg vertex
  nearest to their centroid, as mm7_m402_claude/scripts/rig_spider.py intended (its rig left seven cards on a fang or
  the abdomen, so they stayed behind when their leg moved: up to 0.9 m off in Death).
- REA_FLAT=1: flat shading (every face its own normal, as the original Batch E export); default smooth.
- REA_OUT: output file (default work/cand_export.glb)."""
import os, bpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
rig = bpy.data.objects['Rig']; cand = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_55')]
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
g = cand.vertex_groups.get('ReduceProtect')
if g:
    cand.vertex_groups.remove(g)
if os.environ.get('REA_FIX_CARDS') == '1':
    import numpy as np
    from mathutils.kdtree import KDTree
    cd = np.load(os.path.join(HERE, 'work', 'cards.npz')); me = cand.data
    co = np.array([v.co[:] for v in me.vertices]); kc = KDTree(len(co))
    for i, c in enumerate(co):
        kc.insert(c, i)
    kc.balance()
    names = {g.index: g.name for g in cand.vertex_groups}
    legbone = lambda n: n.split('_')[0] in ('Femur', 'Tibia', 'Tarsus')
    legv = [v.index for v in me.vertices if v.groups and legbone(names[max(v.groups, key=lambda g: g.weight).group])]
    kl = KDTree(len(legv))
    for j, i in enumerate(legv):
        kl.insert(co[i], j)
    kl.balance()
    for card in np.unique(cd['card']):
        pts = cd['pos'][cd['card'] == card]; idx = []
        for q in pts:
            _, i, dist = kc.find(q)
            assert dist < 1e-5, ('card vertex not kept exactly', card)
            idx.append(i)
        leg = legv[kl.find(pts.mean(0))[1]]
        w = [(names[g.group], g.weight) for g in me.vertices[leg].groups]
        for i in idx:
            for g in list(me.vertices[i].groups):
                cand.vertex_groups[g.group].remove([i])
            for n, x in w:
                cand.vertex_groups[n].add([i], x, 'REPLACE')
        print('CARD', int(card), len(idx), 'verts ->', sorted(w, key=lambda t: -t[1])[:2])
for p in cand.data.polygons:
    p.use_smooth = os.environ.get('REA_FLAT') != '1'
bpy.data.objects['Body'].name = 'Source_Body'; cand.name = os.environ.get('REA_NODE', 'Demon_Native_Mesh')
bpy.ops.object.select_all(action='DESELECT'); cand.select_set(True); rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=os.environ.get('REA_OUT', os.path.join(HERE, 'work', 'cand_export.glb')), use_selection=True, export_format='GLB',
                          export_yup=True, export_animations=False, export_skins=True, export_all_influences=os.environ.get('REA_INFLUENCES', '4') == '8',
                          export_attributes=False, export_morph=False, export_image_format='NONE')
print('EXPORTED', sum(len(p.vertices) - 2 for p in cand.data.polygons))
