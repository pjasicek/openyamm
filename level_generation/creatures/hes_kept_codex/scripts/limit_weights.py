"""Normalize the largest eight influences after collapse interpolation."""
import bpy,sys,os
src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src));b=bpy.data.objects['Body']
for v in b.data.vertices:
 weights=sorted([(g.group,g.weight) for g in v.groups if g.weight>1e-5],key=lambda x:-x[1])[:8];total=sum(w for g,w in weights);assert total>.99
 for g in list(v.groups):b.vertex_groups[g.group].remove([v.index])
 for g,w in weights:b.vertex_groups[g].add([v.index],w/total,'REPLACE')
assert max(len(v.groups) for v in b.data.vertices)<=8
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))

sys.stdout.flush();sys.stderr.flush();os._exit(0)
