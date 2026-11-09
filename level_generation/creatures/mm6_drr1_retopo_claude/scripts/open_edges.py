"""Open (boundary) edges of the source body and of retopology REA_TAG: new holes show as extra boundary edges."""
import os, bmesh, bpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = os.environ['REA_TAG']
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', f'retopo_{TAG}.blend'))
for name in ('Wyrm', f'Wyrm_{TAG}'):
    b = bmesh.new(); b.from_mesh(bpy.data.objects[name].data)
    print('OPEN', name, 'boundary edges', sum(1 for e in b.edges if len(e.link_faces) == 1),
          'tris', sum(len(f.verts) - 2 for f in b.faces))
    b.free()
