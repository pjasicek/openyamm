"""Numbers for joint placement (Meshy frame, z not grounded): midline z-range per y, leg centroids per z,
wing-sheet y per x."""
import bpy, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/smart_topology_v1/model_urls_glb.glb'))
m = next(o for o in bpy.data.objects if o.type == 'MESH')
co = np.array([tuple(m.matrix_world @ v.co) for v in m.data.vertices])
lab = np.load(os.path.join(HERE, 'work', 'component_labels.npy'))
main = lab == 0
c = co[main]
print('MIDLINE (y: zmin zmax) |x|<0.03')
for y in np.arange(-0.50, 0.51, 0.025):
    s = c[(np.abs(c[:, 0]) < 0.03) & (np.abs(c[:, 1] - y) < 0.0125)]
    if len(s):
        print(f'  y {y:+.3f}: z {s[:,2].min():+.3f} {s[:,2].max():+.3f}  n {len(s)}')
print('LEG +x (z: x y) for x>0.02, z<-0.03, y<-0.1')
for z in np.arange(-0.22, -0.0, 0.01):
    s = c[(c[:, 0] > 0.02) & (np.abs(c[:, 2] - z) < 0.005) & (c[:, 1] < -0.1) & (c[:, 1] > -0.32)]
    if len(s):
        print(f'  z {z:+.3f}: x {s[:,0].mean():+.3f} [{s[:,0].min():+.3f},{s[:,0].max():+.3f}] y {s[:,1].mean():+.3f} [{s[:,1].min():+.3f},{s[:,1].max():+.3f}] n {len(s)}')
print('WING +x (x: y z-range)')
for x in np.arange(0.06, 0.52, 0.02):
    s = c[(np.abs(c[:, 0] - x) < 0.01) & (c[:, 2] > -0.02)]
    if len(s):
        print(f'  x {x:+.3f}: y {np.median(s[:,1]):+.3f} [{s[:,1].min():+.3f},{s[:,1].max():+.3f}] z [{s[:,2].min():+.3f},{s[:,2].max():+.3f}] n {len(s)}')
