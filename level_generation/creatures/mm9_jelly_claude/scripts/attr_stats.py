"""Counts and z ranges of the fit's 'chain'/'piece' attributes, and dominant bones per chain if weighted.
Args: blend"""
import bpy, sys, collections
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
b = bpy.data.objects['Body']; me = b.data
ch = me.attributes.get('chain'); pc = me.attributes.get('piece')
st = collections.defaultdict(list)
dom = collections.defaultdict(collections.Counter)
for v in me.vertices:
    key = (ch.data[v.index].value if ch else None, pc.data[v.index].value if pc else None)
    st[key].append(v.co.z)
    if v.groups:
        g = max(v.groups, key=lambda g: g.weight)
        dom[key][b.vertex_groups[g.group].name] += 1
for k, zs in sorted(st.items(), key=lambda kv: str(kv[0])):
    print('ATTR', k, len(zs), round(min(zs), 3), round(max(zs), 3), dom[k].most_common(4))
