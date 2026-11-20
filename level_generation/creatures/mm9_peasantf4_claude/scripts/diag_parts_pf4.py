"""Diagnostic renders of a PF4 mesh npz (rest pose, Blender frame): every component its own flat colour, back faces magenta (what a
one-sided viewer culls), optional components hidden. Job 8 (2026-11-04): sleeve holes, hem spikes, chest holes.
Args (after --): <mesh npz> <out prefix> <views: name=cx,cy,cz/tx,ty,tz/ortho;...> [hide comps comma] [size]"""
import bpy, sys, math
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
npz, out, views = a[0], a[1], a[2]
hide = set(a[3].split(',')) if len(a) > 3 and a[3] else set()
size = int(a[4]) if len(a) > 4 else 600
D = np.load(npz, allow_pickle=True); co = D['co']; tri = D['tri']; comp = D['comp']; names = [str(x) for x in D['names']]
inner = D['inner'] if 'inner' in D.files else (D['f4_inner'] if 'f4_inner' in D.files else np.zeros(len(tri), bool))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
for e in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        sc.render.engine = e; break
    except TypeError:
        pass
COL = {'head': (0.9, 0.75, 0.6), 'scarf': (0.2, 0.6, 0.9), 'dress': (0.75, 0.3, 0.2), 'skirt': (0.3, 0.3, 0.3), 'legs': (0.6, 0.6, 0.2),
       'hands': (0.95, 0.85, 0.3), 'lining': (0.1, 0.8, 0.8), 'hood4': (0.4, 0.8, 0.3), 'sleeve4': (0.35, 0.45, 0.95)}
def mat(nm, rgb):
    m = bpy.data.materials.new(nm); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial'); geo = nt.nodes.new('ShaderNodeNewGeometry'); mix = nt.nodes.new('ShaderNodeMixShader')
    d = nt.nodes.new('ShaderNodeBsdfDiffuse'); d.inputs['Color'].default_value = (*rgb, 1)
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (1, 0, 1, 1); e.inputs['Strength'].default_value = 1.0
    nt.links.new(geo.outputs['Backfacing'], mix.inputs['Fac']); nt.links.new(d.outputs[0], mix.inputs[1]); nt.links.new(e.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], o.inputs['Surface']); return m
ct = comp[tri[:, 0]]
for k, nm in enumerate(names):
    if nm in hide: continue
    for inn in (False, True):
        sel = (ct == k) & (inner == inn)
        if not sel.any(): continue
        t = tri[sel]; u, iv = np.unique(t.ravel(), return_inverse=True)
        me = bpy.data.meshes.new(nm); me.from_pydata(co[u].tolist(), [], iv.reshape(-1, 3).tolist()); me.update()
        c = COL.get(nm, (0.7, 0.7, 0.7))
        if inn: c = tuple(x * 0.45 for x in c)
        me.materials.append(mat(nm + ('_in' if inn else ''), c))
        ob = bpy.data.objects.new(nm, me); sc.collection.objects.link(ob)
sc.world = bpy.data.worlds.new('W'); sc.world.use_nodes = True
bg = sc.world.node_tree.nodes['Background']; bg.inputs['Color'].default_value = (0.08, 0.09, 0.1, 1); bg.inputs['Strength'].default_value = 1.0
for i, (rot, en) in enumerate((((50, 0, 30), 3.0), ((60, 0, 200), 1.5), ((-40, 0, 100), 1.0))):
    ld = bpy.data.lights.new(f'L{i}', 'SUN'); ld.energy = en; lo = bpy.data.objects.new(f'L{i}', ld)
    lo.rotation_euler = [math.radians(x) for x in rot]; sc.collection.objects.link(lo)
sc.render.resolution_x = sc.render.resolution_y = size
cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.type = 'ORTHO'; cd.clip_start = 0.001; cd.clip_end = 30
for v in views.split(';'):
    nm, spec = v.split('=')
    c_, t_, o_ = spec.split('/')
    cam.location = Vector([float(x) for x in c_.split(',')]); tgt = Vector([float(x) for x in t_.split(',')])
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler(); cd.ortho_scale = float(o_)
    sc.render.filepath = f'{out}_{nm}.png'; bpy.ops.render.render(write_still=True)
print('DIAG', out)
