import bpy,sys,json,collections
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_textured.blend'))
o=bpy.data.objects['Body'];print('OBJECT',o.name,len(o.data.vertices),len(o.data.polygons),'UV',[x.name for x in o.data.uv_layers],'MATS',[x.name for x in o.data.materials],'MODS',[(x.name,x.type)for x in o.modifiers]);print('ATTR',[(a.name,a.domain,a.data_type)for a in o.data.attributes]);c=collections.Counter()
for f in o.data.polygons:c[o.data.attributes['piece'].data[f.vertices[0]].value]+=len(f.vertices)-2
print('PIECES',sorted(c.items()))
m=o.modifiers.new('test','DECIMATE');print('DECIMATE',[(p.identifier,p.description,p.default if hasattr(p,'default')else None)for p in m.bl_rna.properties if 'vertex' in p.identifier or 'delimit' in p.identifier]);print('PYTHON',sys.path)
