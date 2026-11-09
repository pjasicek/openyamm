#!/usr/bin/env python3
"""Close-ups of the faces reduction_uv_audit.py flags: where the reduced LOD0's escaping faces are and whether they show.

Driver (plain Python): clusters the LOD0 escaping faces of an audit JSON by position (radius R), keeps the CLUSTERS
largest by colour error x area, writes a render plan, runs Blender once (rest pose, Workbench studio light, base colour
textures only: region-mask ramps are not applied) and composes one sheet per model. Each row is one cluster: a context
shot and a close-up of the reduced model with the escaping faces outlined in red, then source | reduced close-ups for
every tier whose base colour image differs (KHR_materials_variants).
Usage: reduction_uv_closeups.py <audit.json> <out_dir> [--clusters N] [--blender /snap/bin/blender]
Writes <out_dir>/closeups.png (+ cells/). Run it under the memory scope, one Blender at a time.
Blender side (internal): blender -b --threads 4 -P reduction_uv_closeups.py -- <plan.json>"""
import json
import os
import subprocess
import sys

R = 0.07          # cluster radius (m)
CELL = 360        # rendered cell size (px)


def to_blender(p):
    return (p[0], -p[2], p[1])


# ---------------------------------------------------------------- Blender side
def blender_main(plan_path):
    import bpy
    from mathutils import Vector
    plan = json.load(open(plan_path))
    os.makedirs(plan['cells'], exist_ok=True)
    for label, glb in (('src', plan['source']), ('red', plan['reduced'])):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=glb)
        for arm in (o for o in bpy.data.objects if o.type == 'ARMATURE'):
            if arm.animation_data:
                arm.animation_data.action = None
            for b in arm.pose.bones:
                b.matrix_basis.identity()
        body = bpy.data.objects[plan['node']]
        for o in bpy.data.objects:
            if o.type == 'MESH':
                o.hide_render = o is not body
        defaults = [s.material for s in body.material_slots]
        sc = bpy.context.scene
        sc.render.engine = 'BLENDER_WORKBENCH'
        sh = sc.display.shading
        sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_cavity = False; sh.show_shadows = False
        sh.background_type = 'VIEWPORT'; sh.background_color = (0.16, 0.17, 0.18)
        sc.view_settings.view_transform = 'Standard'
        sc.render.resolution_x = sc.render.resolution_y = CELL
        cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
        cam.data.type = 'ORTHO'
        # red outlines of the escaping faces (reduced pass only)
        ov = None
        if label == 'red':
            verts, faces = [], []
            for c in plan['clusters']:
                for t in c['tris']:
                    n = len(verts)
                    verts += [Vector(to_blender(p)) + Vector(to_blender(c['normal'])) * 0.0015 for p in t]
                    faces.append((n, n + 1, n + 2))
            me = bpy.data.meshes.new('esc'); me.from_pydata(verts, [], faces)
            ov = bpy.data.objects.new('esc', me); sc.collection.objects.link(ov)
            wf = ov.modifiers.new('wf', 'WIREFRAME'); wf.thickness = 0.0012; wf.use_replace = True
            m = bpy.data.materials.new('esc'); m.diffuse_color = (1, 0.05, 0.05, 1); me.materials.append(m)
        for ti, tier in enumerate(plan['tiers']):
            for s, d in zip(body.material_slots, defaults):
                name = tier['map'].get(d.name, d.name)
                s.material = bpy.data.materials.get(name, d)
            for ci, c in enumerate(plan['clusters']):
                ctr, nrm = Vector(to_blender(c['center'])), Vector(to_blender(c['normal'])).normalized()
                shots = [('close', c['size'])]
                if label == 'red' and ti == 0:
                    shots = [('context', c['size'] * 4), ('mark', c['size']), ('close', c['size'])]
                for kind, size in shots:
                    cam.location = ctr + nrm * 3
                    cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
                    cam.data.ortho_scale = size
                    cam.data.clip_start = 3 - max(size * 0.6, 0.05) if kind != 'context' else 0.1
                    cam.data.clip_end = 6
                    if ov:
                        ov.hide_render = kind == 'close'
                    sc.render.filepath = os.path.join(plan['cells'], f'{ci}_{label}_{tier["name"]}_{kind}.png')
                    bpy.ops.render.render(write_still=True)
    print('CLOSEUPS RENDERED')


# ---------------------------------------------------------------- driver side
def glb_json(path):
    import struct
    raw = open(path, 'rb').read(1 << 24)
    size = struct.unpack_from('<I', raw, 12)[0]
    if len(raw) < 20 + size:
        raw = open(path, 'rb').read()
    return json.loads(raw[20:20 + size])


def tiers_of(path, node):
    """[{name, map: default material name -> tier material name}] from KHR_materials_variants (one entry without)."""
    doc = glb_json(path)
    variants = doc.get('extensions', {}).get('KHR_materials_variants', {}).get('variants', [])
    mesh = doc['meshes'][next(n['mesh'] for n in doc['nodes'] if n.get('name') == node and 'mesh' in n)]
    out = [{'name': v.get('name', f'v{i}'), 'map': {}, 'images': []} for i, v in enumerate(variants)] or \
        [{'name': 'default', 'map': {}, 'images': []}]

    def image(mi):
        t = doc['materials'][mi].get('pbrMetallicRoughness', {}).get('baseColorTexture')
        return doc['textures'][t['index']]['source'] if t else None

    for p in mesh['primitives']:
        d = doc['materials'][p['material']]['name']
        for mp in p.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
            for v in mp['variants']:
                out[v]['map'][d] = doc['materials'][mp['material']]['name']
                out[v]['images'].append(image(mp['material']))
        for t in out:
            if d not in t['map']:
                t['map'][d] = d
                t['images'].append(image(p['material']))
    seen, keep = set(), []
    for t in out:  # tiers whose base colour images are all the same draw the same: keep the first
        k = tuple(t['images'])
        if k not in seen:
            seen.add(k); keep.append(t)
    return keep


def clusters(faces, n_max):
    import numpy as np
    left = sorted(faces, key=lambda f: -(f['colour_err'] + 1) * f['area_mm2'])
    out = []
    while left and len(out) < n_max:
        seed = np.array(left[0]['centroid'])
        member = [f for f in left if np.linalg.norm(np.array(f['centroid']) - seed) < R]
        left = [f for f in left if f not in member]
        C = np.array([f['centroid'] for f in member])
        w = np.array([f['area_mm2'] for f in member]) + 1e-6
        nrm = (np.array([f['normal'] for f in member]) * w[:, None]).sum(0)
        nrm = nrm / np.linalg.norm(nrm) if np.linalg.norm(nrm) > 1e-6 else np.array(member[0]['normal'])
        ext = float(np.ptp(C, 0).max()) if len(C) > 1 else 0.0
        out.append(dict(center=C.mean(0).tolist(), normal=nrm.tolist(), size=max(0.12, ext * 2.2),
                        faces=len(member), materials=sorted({f['material'] for f in member}),
                        colour_err=max(f['colour_err'] for f in member), tris=[f['tri'] for f in member]))
    return out, len(left)


def compose(plan, out_png):
    from PIL import Image, ImageDraw
    cols = [('context', 'red', 0, 'context'), ('mark', 'red', 0, 'escaping faces')]
    for ti, t in enumerate(plan['tiers']):
        cols += [('close', 'src', ti, f'{t["name"]} source'), ('close', 'red', ti, f'{t["name"]} reduced')]
    H = CELL + 18
    sheet = Image.new('RGB', (CELL * len(cols), H * len(plan['clusters']) + 22), (22, 22, 22))
    d = ImageDraw.Draw(sheet)
    d.text((4, 4), plan['title'], fill=(255, 255, 255))
    for ci, c in enumerate(plan['clusters']):
        y = 22 + ci * H
        d.text((4, y + 2), f'cluster {ci}: {c["faces"]} faces ({", ".join(c["materials"])}), colour err max '
                           f'{c["colour_err"]:.0f}, view {c["size"] * 100:.0f} cm', fill=(255, 220, 120))
        for j, (kind, label, ti, cap) in enumerate(cols):
            p = os.path.join(plan['cells'], f'{ci}_{label}_{plan["tiers"][ti]["name"]}_{kind}.png')
            if os.path.exists(p):
                sheet.paste(Image.open(p).convert('RGB'), (j * CELL, y + 18))
            d.text((j * CELL + 4, y + 20), cap, fill=(200, 230, 255))
    sheet.save(out_png)


def driver():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('audit')
    ap.add_argument('out_dir')
    ap.add_argument('--clusters', type=int, default=6)
    ap.add_argument('--blender', default='/snap/bin/blender')
    ap.add_argument('--node')
    a = ap.parse_args()
    rep = json.load(open(a.audit))
    nodes = [a.node] if a.node else list(rep['nodes'])
    os.makedirs(a.out_dir, exist_ok=True)
    for node in nodes:
        faces = [dict(f, material=r['material']) for r in rep['nodes'][node][0] for f in r['faces_list']]
        if not faces:
            continue
        cl, rest = clusters(faces, a.clusters)
        tag = '' if len(nodes) == 1 else f'_{node}'
        plan = dict(source=os.path.abspath(rep['source']), reduced=os.path.abspath(rep['reduced']), node=node,
                    tiers=tiers_of(rep['reduced'], node), clusters=cl,
                    cells=os.path.abspath(os.path.join(a.out_dir, f'cells{tag}')),
                    title=f'{os.path.basename(rep["reduced"])} {node}: {len(faces)} LOD0 faces leave the source UV charts'
                          f' ({len(cl)} clusters shown, {rest} faces in further clusters); rest pose, base colour only')
        pp = os.path.join(a.out_dir, f'plan{tag}.json')
        json.dump(plan, open(pp, 'w'), indent=1)
        subprocess.run([a.blender, '-b', '--threads', '4', '-P', os.path.abspath(__file__), '--', pp], check=True,
                       stdout=subprocess.DEVNULL)
        compose(plan, os.path.join(a.out_dir, f'closeups{tag}.png'))
        print('SHEET', os.path.join(a.out_dir, f'closeups{tag}.png'))


if __name__ == '__main__':
    try:
        import bpy  # noqa: F401
        blender_main(sys.argv[sys.argv.index('--') + 1])
    except ImportError:
        driver()
