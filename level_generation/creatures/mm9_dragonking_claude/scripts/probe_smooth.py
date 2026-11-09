"""Report smooth/flat face state and sharp edges of 'Body' in each blend (shading-fix probe, 2026-10-30).
Args: -- <blend> [<blend> ...]"""
import bpy, sys
for path in sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.open_mainfile(filepath=path)
    ob = bpy.data.objects.get('Body')
    me = ob.data
    smooth = sum(p.use_smooth for p in me.polygons)
    sharp = sum(e.use_edge_sharp for e in me.edges)
    mods = [m.type for m in ob.modifiers]
    print('PROBE', path.split('/')[-1], 'faces', len(me.polygons), 'smooth', smooth, 'sharp_edges', sharp,
          'custom_normals', me.has_custom_normals, 'uv', [l.name for l in me.uv_layers], 'mods', mods)
