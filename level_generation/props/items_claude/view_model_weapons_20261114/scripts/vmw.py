"""Mesh helpers for the view-model weapon builders (build.py, README.md "Route"), run inside Blender.

Frame (Blender): Z is the weapon's long axis (glTF +Y: the head), X the edge width (glTF X), Y the flat's normal (glTF
-Z). Units are the arms' (Oblivion units, about 1.43 cm). Every part is a closed shell with flat-shaded bevel facets:
hard edges are marked sharp, curved surfaces stay smooth. Each face carries an integer `region` attribute (REGIONS),
which the paint post-pass uses for metal, roughness and the UV density classes.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

REGIONS = {'blade': 0, 'metal': 1, 'wood': 2, 'leather': 3, 'gem': 4, 'glow': 5, 'string': 6, 'dark': 7, 'brass': 8, 'edge': 9}


class Builder:
    def __init__(self):
        self.bm = bmesh.new()
        self.region = self.bm.faces.layers.int.new('region')

    # -- primitives -------------------------------------------------------------------------------------------------
    def _faces(self, faces, region, sharp_all=False):
        for f in faces:
            f[self.region] = REGIONS[region]
            f.smooth = True
            if sharp_all:
                for e in f.edges:
                    e.smooth = False
        return faces

    def lathe(self, profile, segments, region, cap_start=True, cap_end=True, phase=0.0, scale_xy=(1.0, 1.0),
              center=(0.0, 0.0), facet=False):
        """Surface of revolution about Z. profile: [(z, r, sharp)] bottom to top; `sharp` marks the ring's edges
        hard (a crease between flat sections: band edges, chamfers). r may be 0 at an end (a pole). Regions may be
        given per span as a list (len(profile) - 1)."""
        bm = self.bm
        rings = []
        for z, r, _ in profile:
            if r <= 1e-6:
                rings.append([bm.verts.new((center[0], center[1], z))])
                continue
            ring = []
            for i in range(segments):
                a = 2 * math.pi * (i + phase) / segments
                ring.append(bm.verts.new((center[0] + r * math.cos(a) * scale_xy[0],
                                          center[1] + r * math.sin(a) * scale_xy[1], z)))
            rings.append(ring)
        faces = []
        for k in range(len(rings) - 1):
            lo, hi = rings[k], rings[k + 1]
            span = region[k] if isinstance(region, (list, tuple)) else region
            new = []
            if len(lo) == 1:
                for i in range(segments):
                    new.append(bm.faces.new((lo[0], hi[i], hi[(i + 1) % segments])))
            elif len(hi) == 1:
                for i in range(segments):
                    new.append(bm.faces.new((lo[i], lo[(i + 1) % segments], hi[0])))
            else:
                for i in range(segments):
                    new.append(bm.faces.new((lo[i], lo[(i + 1) % segments], hi[(i + 1) % segments], hi[i])))
            faces += self._faces(new, span)
        bm.edges.ensure_lookup_table()
        if facet:
            # Flat facets: every lengthwise edge hard (a faceted spike).
            for lo, hi in zip(rings[:-1], rings[1:]):
                for i in range(segments):
                    e = bm.edges.get((lo[0] if len(lo) == 1 else lo[i], hi[0] if len(hi) == 1 else hi[i]))
                    if e is not None:
                        e.smooth = False
        for (z, r, sharp), ring in zip(profile, rings):
            if sharp and len(ring) > 1:
                for i in range(segments):
                    e = bm.edges.get((ring[i], ring[(i + 1) % segments]))
                    if e is not None:
                        e.smooth = False
        first = region[0] if isinstance(region, (list, tuple)) else region
        last = region[-1] if isinstance(region, (list, tuple)) else region
        if cap_start and len(rings[0]) > 1:
            faces += self._cap(rings[0], first, flip=True)
        if cap_end and len(rings[-1]) > 1:
            faces += self._cap(rings[-1], last, flip=False)
        return faces

    def _cap(self, ring, region, flip):
        """A flat cap without a high-valence fan: an inner ring at half the radius, quads to it, an n-gon inside
        (triangulated later by beauty)."""
        bm = self.bm
        c = sum((v.co for v in ring), Vector()) / len(ring)
        inner = [bm.verts.new(c + (v.co - c) * 0.5) for v in ring]
        n = len(ring)
        faces = []
        for i in range(n):
            quad = (ring[i], ring[(i + 1) % n], inner[(i + 1) % n], inner[i])
            faces.append(bm.faces.new(quad[::-1] if not flip else quad))
        mid = bm.faces.new(inner[::-1] if flip else inner)
        faces.append(mid)
        for f in faces:
            for e in f.edges:
                if all(v in ring for v in e.verts):
                    e.smooth = False
        return self._faces(faces, region)

    def loft(self, sections, region, cap_start=True, cap_end=True, sharp_columns=(), close=True, sharp_rows=(),
             strip_regions=None):
        """A loft through closed cross-sections (each a list of 3D points with the same count). Columns in
        sharp_columns are hard longitudinal edges (blade facets); rows in sharp_rows hard rings. A section of one
        point is a pole (a tip). strip_regions {i: region}: the strip between columns i and i + 1 (the honed bevels:
        'edge')."""
        bm = self.bm
        rings = [[bm.verts.new(p) for p in s] for s in sections]
        faces = []
        for k in range(len(rings) - 1):
            lo, hi = rings[k], rings[k + 1]
            n = max(len(lo), len(hi))
            new = []
            if len(lo) == 1:
                for i in range(n):
                    new.append(bm.faces.new((lo[0], hi[i], hi[(i + 1) % n])))
            elif len(hi) == 1:
                for i in range(n):
                    new.append(bm.faces.new((lo[i], lo[(i + 1) % n], hi[0])))
            else:
                for i in range(n if close else n - 1):
                    new.append(bm.faces.new((lo[i], lo[(i + 1) % n], hi[(i + 1) % n], hi[i])))
            faces += self._faces(new, region)
            if strip_regions:
                for i, f in enumerate(new):
                    if i in strip_regions:
                        f[self.region] = REGIONS[strip_regions[i]]
        bm.edges.ensure_lookup_table()
        for k in range(len(rings) - 1):
            lo, hi = rings[k], rings[k + 1]
            for i in sharp_columns:
                a = lo[0] if len(lo) == 1 else lo[i]
                b = hi[0] if len(hi) == 1 else hi[i]
                e = bm.edges.get((a, b))
                if e is not None:
                    e.smooth = False
        for k in sharp_rows:
            ring = rings[k]
            for i in range(len(ring)):
                e = bm.edges.get((ring[i], ring[(i + 1) % len(ring)]))
                if e is not None:
                    e.smooth = False
        if cap_start and len(rings[0]) > 2:
            faces += self._cap(rings[0], region, flip=True)
        if cap_end and len(rings[-1]) > 2:
            faces += self._cap(rings[-1], region, flip=False)
        return faces

    def box(self, center, size, region, bevel=0.15, matrix=None):
        """A box with chamfered edges (all edges hard: flat bevel facets)."""
        tmp = bmesh.new()
        bmesh.ops.create_cube(tmp, size=1.0)
        bmesh.ops.scale(tmp, vec=Vector(size), verts=tmp.verts)
        if bevel > 0:
            bmesh.ops.bevel(tmp, geom=list(tmp.edges), offset=bevel, segments=1, affect='EDGES', profile=0.5)
        m = Matrix.Translation(Vector(center)) @ (matrix or Matrix.Identity(4))
        bmesh.ops.transform(tmp, matrix=m, verts=tmp.verts)
        return self.merge(tmp, region, sharp_all=True)

    def merge(self, tmp, region, sharp_all=False):
        """Appends another bmesh's geometry (its faces get `region`)."""
        me = bpy.data.meshes.new('tmp')
        tmp.to_mesh(me)
        tmp.free()
        before = set(self.bm.faces)
        self.bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        new = [f for f in self.bm.faces if f not in before]
        return self._faces(new, region, sharp_all=sharp_all)

    def plate(self, outline, thickness, region, edge=0.12, bevel_in=0.6, z_axis='y', edge_segments=()):
        """A flat bevelled plate from a closed 2D outline (x, z) in the XZ plane: the outline is the thin edge
        (half thickness `edge`), an inset of `bevel_in` units carries the full half thickness: two hard bevel rings.
        Returns faces. The outline must be counter-clockwise seen from -Y and roughly star-shaped about its inset."""
        bm = self.bm
        n = len(outline)
        pts = [Vector((x, 0.0, z)) for x, z in outline]
        inset = _inset(outline, bevel_in)
        honed = set(edge_segments)
        half = thickness * 0.5
        top_o = [bm.verts.new((p.x, -edge, p.z)) for p in pts]
        bot_o = [bm.verts.new((p.x, edge, p.z)) for p in pts]
        top_i = [bm.verts.new((x, -half, z)) for x, z in inset]
        bot_i = [bm.verts.new((x, half, z)) for x, z in inset]
        faces = []
        edges = []
        for i in range(n):
            j = (i + 1) % n
            strip = [bm.faces.new((top_o[i], bot_o[i], bot_o[j], top_o[j])),   # the edge strip
                     bm.faces.new((top_o[j], top_i[j], top_i[i], top_o[i])),   # front bevel
                     bm.faces.new((bot_o[i], bot_i[i], bot_i[j], bot_o[j]))]   # back bevel
            faces += strip
            if i in honed:
                edges += strip
        faces.append(bm.faces.new(top_i[::-1]))
        faces.append(bm.faces.new(bot_i))
        self._faces(faces, region, sharp_all=True)
        for f in edges:
            f[self.region] = REGIONS['edge']
        return faces

    # -- finishing --------------------------------------------------------------------------------------------------
    def finish(self, name, collection=None):
        bm = self.bm
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], quad_method='BEAUTY',
                              ngon_method='BEAUTY')
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        obj = bpy.data.objects.new(name, me)
        (collection or bpy.context.scene.collection).objects.link(obj)
        return obj


def _inset(outline, d):
    """Inset of a closed polygon by d along the averaged edge normals (CCW in x, z)."""
    n = len(outline)
    out = []
    dist = d if isinstance(d, (list, tuple)) else [d] * n
    for i in range(n):
        d = dist[i]
        p0, p1, p2 = Vector(outline[i - 1]), Vector(outline[i]), Vector(outline[(i + 1) % n])
        e0, e1 = (p1 - p0).normalized(), (p2 - p1).normalized()
        n0, n1 = Vector((-e0.y, e0.x)), Vector((-e1.y, e1.x))
        m = (n0 + n1)
        if m.length < 1e-6:
            m = n1
        m.normalize()
        cos = max(m.dot(n1), 0.35)
        q = p1 + m * (d / cos)
        out.append((q.x, q.y))
    return out


def blade_sections(z0, length, half_width, ridge, edge=0.06, bevel=0.8, rows=14, base=None, curve=None,
                   tip_rows=1):
    """Cross-sections of a diamond-section blade along +Z from z0: half_width(t) and ridge(t) (half thickness at the
    ridge) for t in 0..1; the honed edge bevel starts at `bevel` of the half width. Ten points per section:
    edge+, bevel, ridge, bevel, edge-, then the back. The last section is a pole (the point). curve(t) shifts x."""
    out = []
    for k in range(rows):
        t = k / (rows - 1) if rows > 1 else 0.0
        if k == rows - 1:
            out.append([(curve(t) if curve else 0.0, 0.0, z0 + length)])
            break
        w, T = half_width(t), ridge(t)
        e = min(edge, T * 0.5)
        b = max(e, T * 0.28)
        x0 = curve(t) if curve else 0.0
        z = z0 + length * t
        pts = [(w, -e), (bevel * w, -b), (0.0, -T), (-bevel * w, -b), (-w, -e),
               (-w, e), (-bevel * w, b), (0.0, T), (bevel * w, b), (w, e)]
        out.append([(x0 + x, y, z) for x, y in pts])
    return out


BLADE_SHARP = tuple(range(10))
