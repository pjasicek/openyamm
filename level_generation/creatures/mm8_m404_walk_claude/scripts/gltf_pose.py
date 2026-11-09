"""Blender pose <-> glTF node TRS for an imported GLB rig (runs inside Blender).

The importer gives each bone a corrected axis frame: bone.matrix_local = G_rest @ C, where G_rest is the joint
node's rest transform in armature space (glTF Y-up converted to Blender Z-up) and C a constant per bone. A posed
node is therefore G(t) = pb.matrix @ C^-1, its glTF local is G(parent)^-1 @ G(node), converted back to Y-up."""
import numpy as np
from mathutils import Matrix, Quaternion, Vector

K = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))     # glTF (x, y, z) -> Blender (x, -z, y)
KI = K.inverted()


def node_matrix(node):
    if 'matrix' in node:
        return Matrix(np.array(node['matrix']).reshape(4, 4).T.tolist())
    t = Vector(node.get('translation', (0, 0, 0)))
    r = node.get('rotation', (0, 0, 0, 1)); q = Quaternion((r[3], r[0], r[1], r[2]))
    s = node.get('scale', (1, 1, 1))
    S = Matrix.Diagonal(Vector((s[0], s[1], s[2], 1)))
    return Matrix.Translation(t) @ q.to_matrix().to_4x4() @ S


class GltfPose:
    def __init__(self, gjson, rig):
        nodes = gjson['nodes']
        self.parent = {}
        for i, n in enumerate(nodes):
            for c in n.get('children', []):
                self.parent[c] = i
        self.index = {n.get('name'): i for i, n in enumerate(nodes)}
        rig_index = self.index[rig.name] if rig.name in self.index else self.index['Rig']
        self.rig_index = rig_index
        self.bones = [b.name for b in rig.data.bones]
        world = {}

        def rest_world(i):
            if i == rig_index:
                return Matrix.Identity(4)
            if i not in world:
                world[i] = rest_world(self.parent[i]) @ node_matrix(nodes[i])
            return world[i]
        self.C = {}
        for b in rig.data.bones:
            G = K @ rest_world(self.index[b.name]) @ KI
            self.C[b.name] = G.inverted() @ b.matrix_local
        self.rig = rig

    def node_locals(self):
        """{bone: (translation xyz, rotation xyzw, scale xyz)} in glTF space for the current pose."""
        G = {n: self.rig.pose.bones[n].matrix @ self.C[n].inverted() for n in self.bones}
        out = {}
        for n in self.bones:
            p = self.parent.get(self.index[n])
            pname = None if p is None or p == self.rig_index else next(b for b in self.bones if self.index[b] == p)
            L = G[n] if pname is None else G[pname].inverted() @ G[n]
            Lg = KI @ L @ K
            t, q, s = Lg.decompose()
            out[n] = (np.array(t[:]), np.array((q.x, q.y, q.z, q.w)), np.array(s[:]))
        return out
