"""Insert a 'Bip01 L Hand' joint into an MM9 child-boy GLB (PEASANTBOY*/PEASANTCHILDBOY have no left hand joint: the
left fingers hang off 'Bip01 L Forearm', so MM9's left wrist never bends).

The new joint is a child of the left forearm with the forearm's own rotation (local rotation identity) at the mirror
image of the right hand joint; the left fingers are re-parented to it with their translations moved into its frame.
No clip animates it, so the left hand stays rigid on the forearm exactly as in MM9, while our shared hand scripts
(graft, rest, gates) find a hand joint on both sides. clips_mm9.py copies local finger rotations unchanged: with an
identity hand rotation the forearm frame and the hand frame are the same, so MM9's finger keys mean the same thing.

Usage: python3 add_left_hand.py <in.glb> <out.glb>
"""
import sys
import numpy as np
from pygltflib import GLTF2, Node


def qmat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def local(n):
    M = np.eye(4)
    M[:3, :3] = qmat(n.rotation or [0, 0, 0, 1]) * np.array(n.scale or [1, 1, 1], float)
    M[:3, 3] = n.translation or [0, 0, 0]
    return M


src, dst = sys.argv[1:3]
g = GLTF2().load(src)
byname = {n.name: i for i, n in enumerate(g.nodes)}
assert 'Bip01 L Hand' not in byname
parent = {}
for i, n in enumerate(g.nodes):
    for c in n.children or []:
        parent[c] = i


def world(i):
    M = np.eye(4)
    while i is not None:
        M = local(g.nodes[i]) @ M
        i = parent.get(i)
    return M


fa = byname['Bip01 L Forearm']
rh = world(byname['Bip01 R Hand'])
# mirror plane: the model's x = 0 (LithTech local axes: x is left/right)
p = rh[:3, 3] * np.array([-1, 1, 1])
Wf = world(fa)
t_local = np.linalg.inv(Wf) @ np.append(p, 1.0)
hand = Node(name='Bip01 L Hand', translation=[float(x) for x in t_local[:3]], rotation=[0.0, 0.0, 0.0, 1.0],
            children=[])
g.nodes.append(hand)
hi = len(g.nodes) - 1
for fname in ('Bip01 L Finger0', 'Bip01 L Finger1'):
    fi = byname[fname]
    g.nodes[fa].children.remove(fi)
    hand.children.append(fi)
    t = np.array(g.nodes[fi].translation or [0, 0, 0], float) - t_local[:3]
    g.nodes[fi].translation = [float(x) for x in t]
g.nodes[fa].children.append(hi)
parent[hi] = fa
# the file's own animation keys translate the re-parented fingers in the forearm frame: move them into the hand frame
# too (Blender's importer poses the rig with the first key, which otherwise shifted the left fingers 18 cm)
blob = bytearray(g.binary_blob())
moved = set()
for an in g.animations:
    for ch in an.channels:
        if ch.target.path != 'translation' or g.nodes[ch.target.node].name not in ('Bip01 L Finger0', 'Bip01 L Finger1'):
            continue
        acc = g.accessors[an.samplers[ch.sampler].output]
        if acc.bufferView in moved:
            continue
        moved.add(acc.bufferView)
        bv = g.bufferViews[acc.bufferView]
        off = (bv.byteOffset or 0) + (acc.byteOffset or 0)
        assert not bv.byteStride or bv.byteStride == 12
        v = np.frombuffer(bytes(blob[off:off + 12 * acc.count]), dtype=np.float32).reshape(-1, 3) - t_local[:3]
        blob[off:off + 12 * acc.count] = v.astype(np.float32).tobytes()
        if acc.min is not None:
            acc.min = [float(x) for x in v.min(0)]
            acc.max = [float(x) for x in v.max(0)]
        print('ANIM keys moved', g.nodes[ch.target.node].name, acc.count)
g.set_binary_blob(bytes(blob))
# skin: add the joint with its inverse bind matrix (column-major MAT4)
blob = bytearray(g.binary_blob())
for skin in g.skins:
    ibm_acc = g.accessors[skin.inverseBindMatrices]
    bv = g.bufferViews[ibm_acc.bufferView]
    off = (bv.byteOffset or 0) + (ibm_acc.byteOffset or 0)
    old = np.frombuffer(bytes(blob[off:off + 64 * ibm_acc.count]), dtype=np.float32).reshape(-1, 16)
    # world of the new joint in the skin's frame = world(hi); the other joints' IBMs are world^-1 too
    Wh = world(hi)
    new = np.vstack([old, np.linalg.inv(Wh).T.reshape(1, 16).astype(np.float32)])
    while len(blob) % 4:
        blob.append(0)
    noff = len(blob)
    blob += new.astype(np.float32).tobytes()
    from pygltflib import BufferView, Accessor
    g.bufferViews.append(BufferView(buffer=0, byteOffset=noff, byteLength=new.nbytes))
    g.accessors.append(Accessor(bufferView=len(g.bufferViews) - 1, componentType=5126, count=len(new), type='MAT4'))
    skin.inverseBindMatrices = len(g.accessors) - 1
    skin.joints.append(hi)
g.buffers[0].byteLength = len(blob)
g.set_binary_blob(bytes(blob))
g.save(dst)
print('L HAND at', [round(float(x), 4) for x in p], 'local', [round(float(x), 4) for x in t_local[:3]])
