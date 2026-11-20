"""Copy the staff UVs from a fresh work/staff.blend (make_staff.py, same topology) onto the seated Staff object of a
textured master (the band/wood swatch parity was fixed after the texture chain; geometry, weights and clips unchanged).
Args: -- <blend>"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
st = bpy.data.objects['Staff']
with bpy.data.libraries.load(os.path.join(common.WORK, 'staff.blend'), link=False) as (s_, d_):
    d_.meshes = ['Staff']
new = d_.meshes[0]
assert len(new.loops) == len(st.data.loops), (len(new.loops), len(st.data.loops))
src = new.uv_layers['UVMap'].data; dst = st.data.uv_layers['UVMap'].data
for i in range(len(src)):
    dst[i].uv = src[i].uv
print('STAFFUV copied', len(src), 'loops')
bpy.ops.wm.save_mainfile()
