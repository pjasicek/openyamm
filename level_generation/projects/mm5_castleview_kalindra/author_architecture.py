"""Run in Blender: author original MM5 facade/roof prototypes and export native sources.

Only the explicitly selected sites are built until the prototype review is accepted.
The saved library contains this project's scene; unrelated Blender work is preserved.
"""
import json
import importlib
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
SOURCE = PROJECT / 'implementation/source'
MODELS = SOURCE / 'models'
SCALE = 128
SCENE_NAME = 'MM5 Castleview architecture'
SELECTED = globals().get('SELECTED', [
    'guild', 'forge', 'training', 'monks_n', 'bank', 'workers',
    'monks_s', 'tavern', 'lodging', 'maps', 'mayor', 'workyard',
    'ranger', 'herbalist', 'nadia', 'diviners', 'crafts', 'keeper',
    'jail', 'joe', 'king', 'puzzle', 'tower', 'temple',
    'ruby', 'emerald', 'sapphire', 'diamond', 'reger', 'luna', 'vespar', 'western', 'kalindra',
    'dreyfus','justine','yog','kramer','mine','troll_a','troll_b','troll_c','sewer_out','falista','nibbler','skyrope'])
SPEC = json.loads((PROJECT / 'implementation/architecture.json').read_text())
sys.path.insert(0, str(PROJECT))
import author_fortifications
importlib.reload(author_fortifications)
import author_props
importlib.reload(author_props)
import author_chapter_court
importlib.reload(author_chapter_court)
import author_ranger_yard
importlib.reload(author_ranger_yard)
import author_training_yard
importlib.reload(author_training_yard)
import author_town_working_details
importlib.reload(author_town_working_details)
import author_frontage_signs
importlib.reload(author_frontage_signs)
import author_public_notices
importlib.reload(author_public_notices)
import author_landmarks
importlib.reload(author_landmarks)
import author_watchtower
importlib.reload(author_watchtower)
import author_castle
importlib.reload(author_castle)
import author_camps
importlib.reload(author_camps)
import author_natural_entrances
importlib.reload(author_natural_entrances)
import author_sewer
importlib.reload(author_sewer)
import author_skyrope
importlib.reload(author_skyrope)
import author_town_sewers
importlib.reload(author_town_sewers)
import prepare_town_sewers
importlib.reload(prepare_town_sewers)
import author_town_chests
importlib.reload(author_town_chests)
import prepare_town_chests
importlib.reload(prepare_town_chests)
import author_source_wells
importlib.reload(author_source_wells)
import prepare_source_wells
importlib.reload(prepare_source_wells)
import author_source_signs
importlib.reload(author_source_signs)
import author_source_shrine
importlib.reload(author_source_shrine)
import author_message_bottles
importlib.reload(author_message_bottles)
import author_melon_patches
importlib.reload(author_melon_patches)
import author_wreck
importlib.reload(author_wreck)
import author_barbarian_camp
importlib.reload(author_barbarian_camp)
import author_pyramid
importlib.reload(author_pyramid)
import author_workshops
importlib.reload(author_workshops)
import author_retreats
importlib.reload(author_retreats)
import author_bridges
importlib.reload(author_bridges)
import prepare_bridges
importlib.reload(prepare_bridges)
import world_rim
importlib.reload(world_rim)
import author_route_placeholders
importlib.reload(author_route_placeholders)


class Author:
    def __init__(self):
        MODELS.mkdir(parents=True, exist_ok=True)
        old = bpy.data.scenes.get(SCENE_NAME)
        self.scene = bpy.data.scenes.new(SCENE_NAME)
        bpy.context.window.scene = self.scene
        if old:
            assert old.get('levelgen_project') == 'mm5_castleview_kalindra'
            for obj in list(old.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.scenes.remove(old)
        self.scene.name = SCENE_NAME
        self.scene['levelgen_project'] = 'mm5_castleview_kalindra'
        self.scene['native_units_per_blender_unit'] = SCALE
        self.materials = {}
        self.sizes = {}
        self.metadata = {'version': 1, 'map_file': 'mm5_sw.odm', 'bmodels': []}
        self.semantic = {'status': 'partial prototype geometry; native and visual acceptance pending',
                         'buildings': [], 'props': [], 'fortifications': [], 'bmodels': [], 'events': [],
                         'scenery_groups': SPEC['sceneryGroups'],
                         'texture_provenance': SPEC['materials']}

    def material(self, key):
        if key not in self.materials:
            image = bpy.data.images.load(str(ROOT / SPEC['materials'][key]['path']), check_existing=True)
            image.pack()
            mat = bpy.data.materials.new('MM5 ' + key)
            mat.use_nodes = True
            tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
            tex.image = image
            tex.interpolation = 'Closest'
            shader = mat.node_tree.nodes.get('Principled BSDF')
            shader.inputs['Roughness'].default_value = 1
            mat.node_tree.links.new(tex.outputs['Color'], shader.inputs['Base Color'])
            self.materials[key] = mat
            self.sizes[key] = tuple(image.size)
        return self.materials[key]

    def panel(self, panels, points, key, uv=None):
        self.material(key)
        if uv is None:
            origin = Vector(points[0])
            u = (Vector(points[1]) - origin).normalized()
            normal = (Vector(points[1]) - origin).cross(Vector(points[-1]) - origin).normalized()
            v = normal.cross(u)
            w, h = self.sizes[key]
            uv = [((Vector(p) - origin).dot(u) / w, (Vector(p) - origin).dot(v) / h) for p in points]
        panels.append((points, key, uv))

    def model(self, name, panels, building, event=None):
        if not panels:
            return
        origin, tangent, outward = building['frontOrigin'], building['frontTangent'], building['frontOutward']
        def transform(p):
            return ((origin[0] + tangent[0] * p[0] - outward[0] * p[1]) / SCALE,
                    (origin[1] + tangent[1] * p[0] - outward[1] * p[1]) / SCALE,
                    (building['padHeight'] + p[2]) / SCALE)

        vertices, faces, keys, uvs = [], [], [], []
        for points, key, uv in panels:
            faces.append(tuple(range(len(vertices), len(vertices) + len(points))))
            vertices.extend(transform(p) for p in points)
            keys.append(key)
            uvs.extend(uv)
        mesh = bpy.data.meshes.new('MM5 ' + name)
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        unique = list(dict.fromkeys(keys))
        for key in unique:
            mesh.materials.append(self.material(key))
        for poly, key in zip(mesh.polygons, keys):
            poly.material_index = unique.index(key)
        layer = mesh.uv_layers.new(name='Native texels')
        for datum, uv in zip(layer.data, uvs):
            datum.uv = uv
        obj = bpy.data.objects.new('BMODEL_' + name, mesh)
        self.scene.collection.objects.link(obj)
        obj['levelgen_kind'] = 'bmodel'
        obj['semantic_id'] = building['semanticId'] + '/' + name
        obj['assembly_id'] = building['id']
        path = MODELS / (name + '.obj')
        # Blender adds scene-global suffixes when an isolated study contains the same object.
        # The exported identity must depend only on this semantic model, not open review scenes.
        lines = ['o BMODEL_' + name]
        lines += ['v ' + ' '.join(f'{x:.7f}' for x in v.co) for v in mesh.vertices]
        lines += ['vt ' + ' '.join(f'{x:.7f}' for x in uv.uv) for uv in layer.data]
        for poly in mesh.polygons:
            lines.append('usemtl ' + unique[poly.material_index])
            lines.append('f ' + ' '.join(f'{mesh.loops[i].vertex_index + 1}/{i + 1}' for i in poly.loop_indices))
        path.write_text('\n'.join(lines) + '\n')
        index = len(self.metadata['bmodels'])
        self.metadata['bmodels'].append({
            'geometry_id': obj['semantic_id'], 'runtime_bmodel_index': index,
            'source': {'asset_path': str(path), 'scale': SCALE, 'merge_coplanar_faces': False,
                       'preserve_source_winding': True},
            'materials': {'default_texture': unique[0], 'remaps': {k: k for k in unique}}})
        self.semantic['bmodels'].append({'id': obj['semantic_id'], 'index': index,
                                        'assembly': building['id'], 'faces': len(faces)})
        if event:
            self.semantic['events'].append({**event, 'bmodel_index': index, 'faces': list(range(len(faces)))})

    def wall(self, panels, a, b, lower, upper, palette, door_offsets=(), front=False, windows=True,
             window_levels=None):
        length = math.dist(a, b)
        door_ranges = [(offset - 64 - a[0], offset + 64 - a[0]) for offset in door_offsets] if front else []
        cuts = {0., length}
        if length >= 384:
            cuts.update([128., length - 128])
        for value in range(128, math.ceil(length), 128):
            if length >= 384 and value > length - 128:
                continue
            if not any(lo < value < hi for lo, hi in door_ranges):
                cuts.add(float(value))
        for lo, hi in door_ranges:
            cuts.update([lo, hi])
        cuts = sorted(x for x in cuts if 0 <= x <= length
                      and not any(lo < x < hi for lo, hi in door_ranges))
        assert all(lo in cuts and hi in cuts for lo, hi in door_ranges), door_ranges
        for bottom in range(lower, upper, 256):
            top = min(bottom + 256, upper)
            for i, (left, right) in enumerate(zip(cuts, cuts[1:])):
                if bottom == 0 and any(abs(left - lo) < .01 and abs(right - hi) < .01 for lo, hi in door_ranges):
                    continue
                p = [a[j] + (b[j] - a[j]) * left / length for j in range(2)]
                q = [a[j] + (b[j] - a[j]) * right / length for j in range(2)]
                key = 't05a01' if palette['wall'] == 't05c01' and top - bottom < 256 else palette['wall']
                if bottom >= 0 and right - left == 128:
                    if i == 0:
                        key = palette['corner']
                    elif i == len(cuts) - 2:
                        key = palette['corner_other']
                    elif (windows and i % 3 == 1 and top - bottom == 256
                          and (window_levels is None or bottom in window_levels)):
                        key = palette['window']
                if bottom < 0:
                    key = palette['stone']
                self.panel(panels, [(p[0], p[1], bottom), (q[0], q[1], bottom),
                                    (q[0], q[1], top), (p[0], p[1], top)], key,
                           [(0, 0), ((right-left)/128, 0), ((right-left)/128, (top-bottom)/256),
                            (0, (top-bottom)/256)])

    def roof(self, panels, bounds, eave, peak, kind, palette, ridge_axis='x'):
        if ridge_axis=='y':
            rotated=[]
            x0,y0,x1,y1=bounds
            self.roof(rotated,[-y1,x0,-y0,x1],eave,peak,kind,palette)
            panels.extend(([(y,-x,z) for x,y,z in points],key,uv) for points,key,uv in rotated)
            return
        assert kind in ['hip', 'gable', 'parapet'], ('Specialist roof still needs its own builder', kind)
        x0, y0, x1, y1 = bounds
        if kind == 'parapet':
            # A recessed flat terrace and four independently modeled parapet walls.
            self.panel(panels, [(x0, y0, eave), (x1, y0, eave), (x1, y1, eave), (x0, y1, eave)], palette['stone'])
            ring = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
            inner = [(x0+32,y0+32), (x1-32,y0+32), (x1-32,y1-32), (x0+32,y1-32)]
            for i, a in enumerate(ring):
                b = ring[(i + 1) % 4]
                c, d = inner[(i+1)%4], inner[i]
                self.wall(panels, a, b, eave, peak, palette, windows=False)
                self.panel(panels, [(*c, eave), (*d, eave), (*d, peak), (*c, peak)], palette['stone'])
                self.panel(panels, [(*a, peak), (*b, peak), (*c, peak), (*d, peak)], palette['stone'])
            return
        # Roof overhang fits inside the reserved planning envelope.
        x0 -= 24; x1 += 24; y0 -= 24; y1 += 24
        edge = [(x0,y0), (x1,y0), (x1,y1), (x0,y1)]
        inner = [(x0+24,y0+24), (x1-24,y0+24), (x1-24,y1-24), (x0+24,y1-24)]
        for i, p in enumerate(edge):
            q = edge[(i+1)%4]
            self.panel(panels, [(*p,eave-16),(*q,eave-16),(*q,eave),(*p,eave)],palette['trim'])
            # Close the overhang underside so roofs have visible thickness.
            self.panel(panels, [(*q,eave-16),(*p,eave-16),(*inner[i],eave-16),
                               (*inner[(i+1)%4],eave-16)],palette['trim'])
        middle = (y0+y1)/2
        inset = min((x1-x0)*.23, (y1-y0)*.4) if kind == 'hip' else 0
        a, b = (x0+inset, middle, peak), (x1-inset, middle, peak)
        for points in [[(x0,y0,eave),(x1,y0,eave),b,a],
                       [a,b,(x1,y1,eave),(x0,y1,eave)],
                       [(x0,y1,eave),(x0,y0,eave),a],
                       [(x1,y0,eave),(x1,y1,eave),b]]:
            # Gable end walls use masonry, pitched slopes use roof tiles.
            key = palette.get('gable',palette['wall']) if kind == 'gable' and len(points) == 3 else palette['roof']
            self.panel(panels, points, key)

    def box(self, panels, bounds, key, omit_faces=()):
        x0, y0, z0, x1, y1, z1 = bounds
        ring = [(x0,y0), (x1,y0), (x1,y1), (x0,y1)]
        for i, p in enumerate(ring):
            if i in omit_faces:
                continue
            q = ring[(i+1)%4]
            self.panel(panels, [(*p,z0),(*q,z0),(*q,z1),(*p,z1)], key)
        if 4 not in omit_faces:
            self.panel(panels, [(*p,z0) for p in reversed(ring)], key)
        if 5 not in omit_faces:
            self.panel(panels, [(*p,z1) for p in ring], key)

    def stock_shelter(self, panels, component, palette):
        x0, y0, x1, y1 = component['bounds']
        high, low = component['top'], component['eave']
        # Posts and rafters meet the underside of the actual sloping roof.
        for x in [x0+16, x1-16]:
            for y in [y0+16, y1-16]:
                ring=[(x-16,y-16),(x+16,y-16),(x+16,y+16),(x-16,y+16)]
                top=[(px,py,high+(low-high)*(py-y0)/(y1-y0)-32) for px,py in ring]
                # Match the sloping rafter underside. Box tops previously overlapped its side faces.
                for i,p in enumerate(ring):
                    q=ring[(i+1)%4]
                    self.panel(panels,[(*p,-32),(*q,-32),top[(i+1)%4],top[i]],palette['trim'])
                self.panel(panels,top,palette['trim'])
                self.panel(panels,[(*p,-32) for p in reversed(ring)],palette['trim'])
            side = [(x-16,y0,high-32),(x-16,y1,low-32),
                    (x-16,y1,low-16),(x-16,y0,high-16)]
            other = [(p[0]+32,p[1],p[2]) for p in side]
            self.panel(panels, list(reversed(side)), palette['trim'])
            self.panel(panels, other, palette['trim'])
            for i in range(4):
                self.panel(panels, [side[(i+1)%4],other[(i+1)%4],other[i],side[i]], palette['trim'])
        roof = [(x0,y0,high),(x1,y0,high),(x1,y1,low),(x0,y1,low)]
        self.panel(panels, roof, palette['roof'])
        underside = [(x,y,z-16) for x,y,z in roof]
        self.panel(panels, list(reversed(underside)), palette['trim'])
        for i in range(4):
            self.panel(panels, [underside[i],underside[(i+1)%4],roof[(i+1)%4],roof[i]], palette['trim'])
        # A low stock bench leaves the shelter's open side accessible.
        if not component.get('stockBench',True):
            return
        self.box(panels, [x0+64,y1-120,64,x1-64,y1-48,80], palette['trim'])
        for x in [x0+80,x1-80]:
            for y in [y1-104,y1-64]:
                self.box(panels, [x-12,y-12,-16,x+12,y+12,64], palette['trim'])

    def service_details(self, building, palette):
        panels = []
        if building.get('entranceGeometry'):
            author_natural_entrances.details(self,panels,building,palette,
                                             (PROJECT/'landscape/heightmap.raw').read_bytes())
        if building['id'] in ['dreyfus','justine','yog','kramer']:
            author_camps.supplies(self,panels,building,palette)
        if building['id']=='kalindra':
            author_castle.fittings(self,panels,building,palette)
        if building['id'] in ['reger','luna','vespar']:
            author_retreats.details(self,panels,building,palette,SPEC['palettes']['working_props'])
        if building['id'] in SPEC['palettes']['gemsmith_signs']:
            author_workshops.gemsmith_details(self,panels,building,palette,SPEC['palettes']['working_props'],
                                             SPEC['palettes']['gemsmith_signs'][building['id']])
        if building['id']=='temple':
            author_landmarks.mok_inscription(self,panels,SPEC['palettes']['courtyard_stone']['rim'])
        if building['id'] == 'forge':
            # Independent masonry flue, embedded through the hall roof, open at its cap.
            x, y, top = 220, 700, 848
            self.box(panels, [x-64,y-64,320,x+64,y+64,top-32], palette['stone'])
            for bounds in [[x-80,y-80,top-32,x+80,y-48,top],
                           [x-80,y+48,top-32,x+80,y+80,top],
                           [x-80,y-48,top-32,x-48,y+48,top],
                           [x+48,y-48,top-32,x+80,y+48,top]]:
                self.box(panels, bounds, palette['stone'])
        if building['id'] == 'training':
            for detail in building['details']:
                self.box(panels,detail['bounds'],palette['pier'])
        for detail in building['details']:
            x0,y0,z0,x1,y1,z1=detail['bounds']
            if detail['id'] in ['guard_pier','gutter_spine','entrance_step']:
                self.box(panels,detail['bounds'],palette['stone'])
            elif detail['id']=='drying_rack':
                for x in [x0,x1-16]:
                    for y in [y0,y1-16]:
                        self.box(panels,[x,y,-32,x+16,y+16,z1],palette['trim'])
                for z in [80,128,176]:
                    self.box(panels,[x0+16,y0,z,x1-16,y1,z+8],palette['trim'])
            elif detail['id']=='kennel':
                # Small timber shelter under the lower canopy. Its opening faces the open side yard.
                for bounds in [[x0,y0,-32,x0+16,y1,96],
                               [x0+16,y0,-32,x1,y0+16,96],
                               [x0+16,y1-16,-32,x1,y1,96],
                               [x1-16,y0+16,-32,x1,y0+40,96],
                               [x1-16,y1-40,-32,x1,y1-16,96],
                               [x1-16,y0+40,80,x1,y1-40,96]]:
                    self.box(panels,bounds,palette['trim'])
                self.roof(panels,[x0,y0,x1,y1],96,144,'hip',palette)
            elif detail['id']=='anvil':
                work=SPEC['palettes']['working_props']
                cx,cy=-220,1184
                self.box(panels,[cx-64,cy-40,-32,cx+64,cy+40,48],work['wood'])
                rings=[[(cx-x,cy-y,z),(cx+x,cy-y,z),(cx+x,cy+y,z),(cx-x,cy+y,z)]
                       for x,y,z in [(64,40,48),(40,24,72),(24,20,96),(48,32,120),
                                     (64,36,128),(64,36,144)]]
                for band,(a,b) in enumerate(zip(rings,rings[1:])):
                    for i in range(4):
                        if band==4 and i==1:continue  # Horn grows out of this opening.
                        j=(i+1)%4
                        self.panel(panels,[a[i],a[j],b[j],b[i]],work['metal'])
                self.panel(panels,rings[-1],work['metal'])
                for lo,hi in [(-36,-24),(24,36)]:
                    self.panel(panels,[(cx+64,cy+lo,128),(cx+64,cy+hi,128),
                                       (cx+64,cy+hi,144),(cx+64,cy+lo,144)],work['metal'])
                opening=[(cx+64,cy-24,128),(cx+64,cy+24,128),
                         (cx+64,cy+24,144),(cx+64,cy-24,144)]
                for i in range(4):
                    self.panel(panels,[opening[i],opening[(i+1)%4],(cx+112,cy,136)],work['metal'])
            elif detail['id']=='ore_bin':
                work=SPEC['palettes']['working_props']
                for bounds in [[x0,y0,-32,x1,y0+12,64],[x0,y1-12,-32,x1,y1,64],
                               [x0,y0+12,-32,x0+12,y1-12,64],[x1-12,y0+12,-32,x1,y1-12,64],
                               [x0+12,y0+12,16,x1-12,y1-12,24]]:
                    self.box(panels,bounds,work['wood'])
                for cx,cy,z,r in [(x0+32,y0+36,28,18),(x0+68,y0+34,32,20),
                                   (x0+50,y0+66,40,22),(x0+50,y0+46,58,18)]:
                    ring=[(cx+r*math.cos(i*math.tau/5),cy+r*math.sin(i*math.tau/5),z) for i in range(5)]
                    for i in range(5):
                        j=(i+1)%5
                        self.panel(panels,[ring[i],ring[j],(cx+3,cy-2,z+r)],work['ore'])
                        self.panel(panels,[ring[j],ring[i],(cx-2,cy+2,z-r)],work['ore'])
        author_frontage_signs.author_signs(self,panels,building,SPEC['palettes']['working_props'])
        self.model(building['id']+'_service_details', panels, building)

    def fountain(self, prop):
        palette = SPEC['palettes'][prop['palette']]
        panels = []
        # Twelve-sided original basin with a low step and thick, usable stone rim.
        def ring(radius, z):
            return [(round(radius*math.cos(i*math.tau/12), 3),
                     round(radius*math.sin(i*math.tau/12), 3), z) for i in range(12)]

        def band(r0, z0, r1, z1, key):
            a, b = ring(r0,z0), ring(r1,z1)
            for i in range(12):
                j = (i+1)%12
                self.panel(panels, [a[i],a[j],b[j],b[i]], palette[key])

        skirt = prop['foundation']['skirtBottomZ']-prop['padHeight']
        band(256,skirt,256,16,'stone')
        band(256,16,208,16,'rim')
        band(208,16,208,112,'stone')
        band(208,112,168,112,'rim')
        band(168,112,168,48,'stone')
        # Water is an ordinary native artwork face; the local handler grants no HP.
        water = ring(168,88)
        for i in range(12):
            points = [(0,0,88),water[i],water[(i+1)%12]]
            self.panel(panels, points, palette['water'], [(x/128,y/128) for x,y,z in points])
        band(40,48,32,192,'column')
        band(32,192,80,224,'stone')
        band(80,224,80,248,'stone')
        band(80,248,60,248,'rim')
        band(60,248,60,224,'stone')
        water = ring(60,236)
        for i in range(12):
            points = [(0,0,236),water[i],water[(i+1)%12]]
            self.panel(panels, points, palette['water'], [(x/128,y/128) for x,y,z in points])
        self.model(prop['id'], panels, prop, {'semantic_id':prop['semanticId'], 'label':prop['title'],
                   'id':prop['eventId'], 'behavior':prop['behavior']})
        self.semantic['props'].append(prop)

    def building(self, building):
        if building.get('environmentKind') == 'native scenery clearing':
            assert building['nativeScenery'] and building['venues']
            self.semantic['buildings'].append(building)
            return
        palette = SPEC['palettes'][building['palette']]
        for component in building['components']:
            x0, y0, x1, y1 = component['bounds']
            roof_kind = component['roof']
            panels = []
            ring = [(x0,y0), (x1,y0), (x1,y1), (x0,y1)]
            base=component.get('baseHeight',0)
            doors = [v['localOffset'] for v in building['venues']
                     if x0+64 <= v['localOffset'] <= x1-64
                     and v.get('localDepth',0)==y0 and v.get('heightAbovePad',0)==base]
            if roof_kind == 'lean_to':
                self.stock_shelter(panels, component, palette)
            elif roof_kind in ['arcane_tower','apse']:
                author_landmarks.polygon_hall(self,panels,component,palette,doors)
            elif roof_kind=='watch_tower':
                author_watchtower.shaft(self,panels,component,
                                       {**palette,'terrace':SPEC['palettes']['garrote_curtain']['floor']},doors)
            elif roof_kind=='royal_tower':
                author_castle.royal_tower(self,panels,component,palette)
            elif roof_kind=='castle_gate':
                author_castle.entry_arch(self,panels,component,palette,building)
            elif roof_kind=='court_paving':
                author_castle.paving(self,panels,component,palette,building)
            elif roof_kind=='camp_shelter':
                author_camps.shelter(self,panels,component,palette,building)
            elif roof_kind=='camp_tent':
                author_camps.tent(self,panels,component,palette,building)
            elif roof_kind=='camp_wagon':
                author_camps.wagon(self,panels,component,palette,building)
            elif roof_kind=='natural_recess':
                author_natural_entrances.rock_recess(self,panels,component,palette,building,
                                                    (PROJECT/'landscape/heightmap.raw').read_bytes())
            elif roof_kind=='sewer_vault':
                author_sewer.vault(self,panels,component,palette,building)
            elif roof_kind=='skyrope_brace':
                author_skyrope.branch(self,panels,palette)
            elif roof_kind=='sewer_landing':
                author_sewer.landing(self,panels,component,palette,building,
                                     (PROJECT/'landscape/heightmap.raw').read_bytes())
            elif roof_kind=='canopy':
                for x in [x0,x1-24]:
                    for y in [y0,y1-24]:
                        self.box(panels,[x,y,-32,x+24,y+24,component['eave']-16],palette['trim'])
                self.roof(panels,component['bounds'],component['eave'],component['top'],'hip',palette)
                self.panel(panels,[(x0,y1,component['eave']-16),(x1,y1,component['eave']-16),
                                   (x1,y0,component['eave']-16),(x0,y0,component['eave']-16)],palette['trim'])
                # Back display board and narrow service shelf remain inside the small stall envelope.
                self.box(panels,[x0+24,y1-32,80,x1-24,y1-24,208],palette['trim'])
                self.box(panels,[x0+40,y1-104,80,x1-40,y1-32,96],palette['trim'])
            elif roof_kind == 'entry_hood':
                low,high=component['eave'],component['top']
                roof=[(x0,y0,low),(x1,y0,low),(x1,y1,high),(x0,y1,high)]
                underside=[(x,y,z-16) for x,y,z in roof]
                self.panel(panels,roof,palette['roof'])
                self.panel(panels,list(reversed(underside)),palette['trim'])
                for i in range(4):
                    self.panel(panels,[underside[i],underside[(i+1)%4],roof[(i+1)%4],roof[i]],palette['trim'])
                post=component.get('postWidth',64)
                for x in [x0,x1-post]:
                    self.box(panels,[x,y0,-64,x+post,y0+post,low-16],palette['stone'])
            else:
                self.panel(panels, [(*p,-64) for p in reversed(ring)], palette['stone'])
                for i, a in enumerate(ring):
                    b = ring[(i+1)%4]
                    self.wall(panels, a, b, -64, 0, palette)
                    if building['id']=='training' and i==0:
                        self.wall(panels,a,b,0,256,palette,doors,front=True)
                        upper=component['eave']
                        points=[(x0,0,256),(x1,0,256),(x1,0,upper),(x0,0,upper)]
                        self.panel(panels,points,palette['frieze'],
                                   [(x/128,(z-upper+256)/256) for x,y,z in points])
                    else:
                        self.wall(panels, a, b, 0, component['eave'], palette, doors, front=i==0,
                                  window_levels=component.get('windowLevels'))
                self.roof(panels, component['bounds'], component['eave'], component['top'], roof_kind, palette,
                          component.get('ridgeAxis','x'))
            if base:
                panels=[([(x,y,z+base) for x,y,z in points],key,uv) for points,key,uv in panels]
            self.model(building['id'] + '_' + component['id'], panels, building)
        self.service_details(building, palette)
        author_public_notices.author_notices(self,building,SPEC['palettes']['working_props'])
        for v in building['venues']:
            x = v['localOffset']
            panels = []
            if v.get('interactionSurface')=='climbing rope and coil':
                author_skyrope.rope(self,panels,palette)
            elif v.get('interactionSurface')=='barred sewer recess':
                author_sewer.interaction(self,panels,building,palette,v)
            elif v.get('interactionSurface')=='recessed rock descent':
                author_natural_entrances.interaction(self,panels,building,palette,v)
            elif v.get('interactionSurface') in ['camp counter','tent flap']:
                author_camps.interaction(self,panels,building,palette,v)
            elif v.get('interactionSurface')=='stall counter':
                self.box(panels,[-176,32,-32,176,112,96],palette['trim'])
                depth=building['localFootprint'][1]
                self.panel(panels,[(-64,depth-33,80),(64,depth-33,80),(64,depth-33,208),(-64,depth-33,208)],
                           SPEC['palettes']['stall_documents']['map'],[(0,0),(1,0),(1,1),(0,1)])
                for left,bottom in [(-128,40),(32,56)]:
                    self.panel(panels,[(left,bottom,97),(left+64,bottom,97),
                                       (left+64,bottom+48,97),(left,bottom+48,97)],
                               SPEC['palettes']['stall_documents']['map'],[(0,0),(1,0),(1,1),(0,1)])
                if building['id']=='joe':
                    # The small notice belongs to the existing counter venue, not a separate service or NPC.
                    self.box(panels,[-164,26,4,-12,32,84],palette['trim'])
                    self.panel(panels,[(-160,24,8),(-16,24,8),(-16,24,80),(-160,24,80)],
                               SPEC['palettes']['stall_documents']['absenceSign'],[(0,0),(1,0),(1,1),(0,1)])
            else:
                y,z=v.get('localDepth',0),v.get('heightAbovePad',0)
                self.panel(panels, [(x-64,y,z),(x+64,y,z),(x+64,y,z+256),(x-64,y,z+256)], palette['door'],
                           [(0,0),(1,0),(1,1),(0,1)])
                if building['id']=='jail':
                    metal=SPEC['palettes']['working_props']['metal']
                    for offset in [-48,-24,0,24,48]:
                        self.box(panels,[x+offset-3,-8,0,x+offset+3,0,256],metal)
                    for z in [72,184]:
                        self.box(panels,[x-56,-16,z,x+56,-8,z+8],metal)
            self.model(building['id'] + '_door_' + str(building['venues'].index(v)), panels, building,
                       {'semantic_id':v['id'], 'label':v['displayLabel'],
                        'id':v['eventId'], 'behavior':'status-only placeholder'})
        self.semantic['buildings'].append(building)

    def save(self):
        for name, data in [('mm5_sw.geometry.yml', self.metadata), ('mm5_sw.semantic.json', self.semantic)]:
            (SOURCE / name).write_text(json.dumps(data, indent=2) + '\n')
        bpy.data.libraries.write(str(SOURCE / 'mm5_sw.blend'), {self.scene}, fake_user=True, compress=True)
        print({'scene': self.scene.name, 'assemblies':len(self.semantic['buildings']),
               'bmodels':len(self.metadata['bmodels']), 'status':self.semantic['status']})


author = Author()
for entry in SPEC['buildings']:
    if entry['id'] in SELECTED:
        author.building(entry)
for prop in SPEC['props']:
    if prop['id'] == 'healing_fountain':
        author.fountain(prop)
    elif prop['id']=='training_pool':
        author_props.author_training_pool(author,prop,SPEC['palettes'][prop['palette']])
    elif prop['id']=='luna_altar':
        author_retreats.altar(author,prop,SPEC['palettes'][prop['palette']])
    elif prop.get('kind')=='town sewer grate':
        author_town_sewers.author_grate(author,prop,SPEC['palettes'][prop['palette']])
    elif prop.get('kind')=='town chest':
        author_town_chests.author_chest(author,prop,SPEC['palettes'][prop['palette']])
    elif prop.get('kind')=='source well':
        author_source_wells.author_well(author,prop,SPEC['palettes'][prop['palette']])
    elif prop.get('kind')=='source sign':
        author_source_signs.author_sign(author,prop,SPEC['palettes'][prop['palette']])
    elif prop.get('kind')=='source shrine':
        author_source_shrine.author_shrine(author,prop,SPEC['palettes'][prop['palette']])
    elif prop.get('kind')=='message bottle':
        author_message_bottles.author_bottle(author,prop,SPEC['palettes'][prop['palette']])
    elif prop.get('kind')=='source wreck':
        author_wreck.author_wreck(author,prop,SPEC['palettes'][prop['palette']])
    elif prop.get('kind')=='barbarian camp':
        author_barbarian_camp.author_camp(author,prop,SPEC['palettes'][prop['palette']],
                                        (PROJECT/'landscape/heightmap.raw').read_bytes())
    elif prop.get('kind')=='closed pyramid':
        author_pyramid.author_pyramid(author,prop,SPEC['palettes'][prop['palette']])
    elif prop.get('kind')=='melon patch':
        author_melon_patches.author_patch(author,prop,SPEC['palettes'][prop['palette']],
                                         (PROJECT/'landscape/heightmap.raw').read_bytes())
    elif prop.get('kind')=='town working detail':
        author_town_working_details.author_detail(author,prop,SPEC['palettes'][prop['palette']],
                                                   (PROJECT/'landscape/heightmap.raw').read_bytes())
    elif prop.get('kind')=='training target':
        author_training_yard.author_target(author,prop,SPEC['palettes'][prop['palette']])
    elif prop.get('kind')=='woodcraft setting':
        author_ranger_yard.author_yard(author,prop,SPEC['palettes'][prop['palette']],
                                      (PROJECT/'landscape/heightmap.raw').read_bytes())
for gate in SPEC['gates']:
    author_fortifications.author_gate(author,gate,SPEC['palettes'][gate['palette']])
author_fortifications.author_curtain(author,SPEC,(PROJECT/'landscape/heightmap.raw').read_bytes())
author_props.author_props(author,SPEC,PROJECT)
author_chapter_court.author_court(author,SPEC,PROJECT)
prepare_town_sewers.review_fit([p for p in SPEC['props'] if p.get('kind')=='town sewer grate'],
                              SPEC,author.semantic)
prepare_town_chests.review_fit([p for p in SPEC['props'] if p.get('kind')=='town chest'],SPEC,author.semantic)
prepare_source_wells.review_fit([p for p in SPEC['props'] if p.get('kind')=='source well'],SPEC,author.semantic)
prepare_bridges.prepare()
bridge_spec=json.loads((PROJECT/'implementation/bridge_layout.json').read_text())
for bridge in bridge_spec['bridges']:
    author_bridges.author_bridge(author,bridge,SPEC['palettes']['working_props'],
                                 (PROJECT/'landscape/heightmap.raw').read_bytes())
author.semantic['face_overrides'] = world_rim.author_rim(author, SPEC['worldRim'])
author.semantic['world_rim'] = SPEC['worldRim']
author_route_placeholders.author_routes(author, PROJECT)
author.save()
