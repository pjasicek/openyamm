"""Consolidate the accepted Alvar/Garrote design into editable native authoring inputs.

The earlier wireframe remains source evidence. This specification owns implementation
forms and materials; no native reference vertices are imported or transformed.
"""
import hashlib
import json
import math
import subprocess
import shutil
from pathlib import Path
import prepare_camps
import prepare_natural_entrances
import prepare_sewer
import prepare_skyrope
import prepare_clearings
import prepare_town_sewers
import prepare_town_chests
import prepare_source_wells
import prepare_source_signs
import prepare_source_shrine
import prepare_message_bottles
import prepare_melon_patches
import prepare_wreck
import prepare_barbarian_camp
import prepare_pyramid
import author_ranger_yard
import author_training_yard
import author_town_working_details
import author_frontage_signs
import author_public_notices

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
OUTPUT = PROJECT / 'implementation'

# Form, eave and highest roof/parapet above the local pad. These are authored
# dimensions, not scale factors applied to reference meshes.
CHOICES = {
    'guild': ('wing_hall', 384, 640),
    'forge': ('workshop', 384, 640),
    'training': ('institution', 448, 512),
    'jail': ('fortified_hall', 640, 768),
    'monks_n': ('long_hip', 256, 448),
    'monks_s': ('long_hip', 256, 384),
    'bank': ('paired_frontage', 384, 576),
    'tavern': ('wing_hall', 448, 704),
    'lodging': ('gable_hall', 384, 640),
    'maps': ('wing_hall', 384, 640),
    'mayor': ('civic_wing', 448, 704),
    'workyard': ('workshop', 256, 448),
    'joe': ('canopy', 240, 304),
    'ranger': ('hip_cottage', 256, 448),
    'herbalist': ('cottage_shed', 256, 448),
    'nadia': ('hip_cottage', 256, 384),
    'diviners': ('gable_hall', 320, 512),
    'king': ('fortified_hall', 704, 896),
    'tower': ('arcane_tower', 2304, 3072),
    'temple': ('apsed_hall', 704, 1024),
    'crafts': ('paired_frontage', 320, 512),
    'workers': ('long_hip', 256, 384),
    'keeper': ('cottage_shed', 256, 448),
    'puzzle': ('institution', 512, 704),
    'dreyfus': ('canopy', 256, 384),
    'ruby': ('workshop', 352, 512),
    'emerald': ('workshop', 352, 480),
    'sapphire': ('workshop', 352, 512),
    'diamond': ('workshop', 352, 512),
    'reger': ('hip_cottage', 288, 416),
    'falista': ('sanctuary', 0, 0),
    'luna': ('cottage_shed', 288, 416),
    'justine': ('canopy', 192, 256),
    'yog': ('canvas_camp', 256, 432),
    'vespar': ('hip_cottage', 320, 512),
    'kramer': ('caravan_yard', 256, 384),
    'nibbler': ('natural_shelter', 0, 0),
    'kalindra': ('royal_keep', 2048, 3584),
    'western': ('watch_tower', 2432, 2816),
    'mine': ('rock_portal', 256, 384),
    'troll_a': ('descent_rim', 0, 0),
    'troll_b': ('descent_rim', 0, 0),
    'troll_c': ('descent_rim', 0, 0),
    'sewer_out': ('masonry_drain', 256, 384),
    'skyrope': ('rope_anchor', 0, 0),
}
FACING = {'S': (0, -1), 'E': (1, 0), 'N': (0, 1), 'W': (-1, 0)}
COUNTRY_FACING = {
    'dreyfus': 'S', 'ruby': 'S', 'emerald': 'W', 'sapphire': 'W', 'diamond': 'S',
    'reger': 'E', 'luna': 'S', 'justine': 'W', 'yog': 'S', 'vespar': 'W',
    'kramer': 'S', 'kalindra': 'E', 'western': 'E', 'mine': 'S', 'sewer_out': 'S',
}
PALETTES = {
    'training_targets': author_training_yard.PALETTE,
    'frontage_signs': author_frontage_signs.PALETTE,
    'public_notices': author_public_notices.PALETTE,
    'source_sign': prepare_source_signs.PALETTE,
    'source_shrine': prepare_source_shrine.PALETTE,
    'message_bottle': prepare_message_bottles.PALETTE,
    'melon_patch': prepare_melon_patches.PALETTE,
    'source_wreck': prepare_wreck.PALETTE,
    'barbarian_camp': prepare_barbarian_camp.PALETTE,
    'closed_pyramid': prepare_pyramid.PALETTE,
    'source_well': prepare_source_wells.PALETTE,
    'town_chest': prepare_town_chests.PALETTE,
    'town_sewer': prepare_town_sewers.PALETTE,
    'courtyard_stone': {'stone': 'gcst2-bs', 'rim': 'gstn1bot', 'column': 'gstn1cl', 'water': 'wtrtyl'},
    'working_props': {'stone':'t18b01', 'wood':'t05a10', 'crate':'crate_w64', 'water':'wtrtyl',
                      'metal':'gn_mtl03', 'ore':'t68a03a'},
    'alvar_domestic': {'wall': 't05a01', 'stone': 't05a01c', 'roof': 't05a05',
                      'door': 't05a03', 'window': 't05a04c', 'corner': 't05a07a',
                      'corner_other': 't05a07b', 'trim': 't05a10', 'step': 't05fstep'},
    'alvar_civic': {'wall': 't05c01', 'stone': 't05a01c', 'roof': 't05a05',
                   'door': 't05b03', 'window': 't05c04c', 'corner': 't05a07a',
                   'corner_other': 't05a07b', 'trim': 't05a10', 'step': 't05fstep'},
    'garrote_fortified': {'wall': 't18a01a', 'stone': 't18b01', 'roof': 't18a05',
                         'door': 't18a03c', 'window': 't18a04c', 'corner': 't18a06',
                         'corner_other': 't18a07', 'trim': 't18a11a', 'step': 't05fstep'},
    'garrote_curtain': {'wall':'t18a01a', 'stone':'t18a02a', 'trim':'t18a11a',
                        'corner':'t18a06', 'corner_other':'t18a07', 'window':'t18a01b',
                        'floor':'t32a05b', 'plaque':'t18a12b'},
}
PALETTES['alvar_institution']={**PALETTES['alvar_domestic'],'frieze':'t05a01b','pier':'t05a06a'}
PALETTES['garrote_jail']={**PALETTES['garrote_fortified'],'window':'t18a01b'}
PALETTES['stall_documents']={'map':'mm5map','absenceSign':'mm5lunch'}
PALETTES['gemsmith_signs']={gem:'mm5'+gem for gem in ['ruby','emerald','sapphire','diamond']}
PALETTES['gemsmith_signs']['sapphire']='mm5saph'
PALETTES['alvar_temple']={**PALETTES['alvar_civic'],'window':'t05c04b',
                         'corner':'t05c07b','corner_other':'t05a07d','gable':'t05a01'}
PALETTES['kalindra_royal']={**PALETTES['garrote_fortified'],'towerWindow':'t18a04a',
                           'plainStone':'t18a02a','floor':'t32a05b','banner':'mm5royal'}
PALETTES['camp_equipment']=prepare_camps.PALETTE
PALETTES['natural_entrances']=prepare_natural_entrances.PALETTE
PALETTES['sewer_masonry']=prepare_sewer.PALETTE
PALETTES['skyrope_timber']=prepare_skyrope.PALETTE


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def components(form, width, depth, eave, peak):
    """Rectangles are local X left/right and Y inward from the main frontage."""
    def part(name, x0, y0, x1, y1, roof, wall_top=eave, roof_top=peak):
        return {'id': name, 'bounds': [x0, y0, x1, y1], 'roof': roof,
                'eave': wall_top, 'top': roof_top}

    x0, x1 = -width / 2, width / 2
    if form in ['wing_hall', 'civic_wing', 'cottage_shed']:
        front_depth = round(depth * .57 / 32) * 32
        wing_width = max(256, round(width * .38 / 32) * 32)
        return [part('front_hall', x0, 0, x1, front_depth, 'hip'),
                part('rear_wing', x0, front_depth, x0 + wing_width, depth,
                     'lean_to' if form=='cottage_shed' else 'hip',
                     eave - 64, eave if form=='cottage_shed' else peak - 96)]
    if form == 'paired_frontage':
        return [part('shared_hall',x0,0,x1,depth,'hip')]
    if form == 'workshop':
        hall_depth = round(depth * .7 / 32) * 32
        return [part('work_hall', x0, 0, x1, hall_depth, 'gable'),
                part('stock_canopy', x0, hall_depth, 0, depth, 'lean_to',
                     min(224,eave-32),min(288,eave-16))]
    if form in ['hip_cottage', 'long_hip', 'gable_hall', 'institution', 'fortified_hall', 'canopy']:
        roof = {'gable_hall': 'gable', 'institution': 'parapet', 'fortified_hall': 'parapet',
                'canopy': 'canopy'}.get(form, 'hip')
        return [part('main', x0, 0, x1, depth, roof)]
    # Landmarks and natural sites have separate builders; reserve their actual extent
    # here, without pretending a rectangular placeholder is their finished geometry.
    return [part('site', x0, 0, x1, depth, form)]


def prepare_gates(plan):
    heights = (PROJECT/'landscape/heightmap.raw').read_bytes()
    result = []
    for feature in [f for f in plan['features'] if f['kind'] == 'gate']:
        south = feature['id'] == 'pass_gate'
        point = list(feature['point'])
        # Align the passage with its native road centre, preserving the wall-side coordinate.
        axis = 0 if south else 1
        point[axis] = round((point[axis]-256)/512)*512+256
        normal = [0,-1] if south else [-1,0]
        tangent = [-normal[1],normal[0]]
        if not south:
            perimeter=next(f for f in plan['features'] if f['id']=='town_wall')['polygon']
            a,b=perimeter[4:6]
            t=(point[1]-a[1])/(b[1]-a[1])
            point[0]=a[0]+t*(b[0]-a[0])
            length=math.dist(a,b)
            tangent=[(b[i]-a[i])/length for i in range(2)]
            normal=[tangent[1],-tangent[0]]
        opening = feature['architecture']['opening']
        half = opening[0]/2
        towers = [{'id':'left_guard', 'bounds':[-half-640,-128,-half,512], 'top':1792},
                  {'id':'right_guard', 'bounds':[half,-128,half+512,512], 'top':1536}] if south else [
                  {'id':'left_guard', 'bounds':[-half-512,-128,-half,416], 'top':1536},
                  {'id':'right_shoulder', 'bounds':[half,-128,half+384,384], 'top':1152}]
        points = [(point[0]+tangent[0]*x-normal[0]*y,point[1]+tangent[1]*x-normal[1]*y)
                  for t in towers for x in [t['bounds'][0],t['bounds'][2]]
                  for y in [t['bounds'][1],t['bounds'][3]]]
        c0 = math.floor((min(x for x,y in points)+32768)/512)
        c1 = math.ceil((max(x for x,y in points)+32768)/512)
        r0 = math.floor((32768-max(y for x,y in points))/512)
        r1 = math.ceil((32768-min(y for x,y in points))/512)
        support = [heights[r*128+c]*32 for r in range(r0,r1+1) for c in range(c0,c1+1)]
        pad = heights[round((32768-point[1])/512)*128+round((point[0]+32768)/512)]*32
        result.append({**feature,'semanticId':'mm5:sw/'+feature['id'], 'frontOrigin':point,
                       'frontOutward':normal,'frontTangent':tangent,'padHeight':pad,
                       'palette':'garrote_curtain', 'towers':towers,
                       'foundationBottom':min(support)-64-pad, 'terrainSupportRange':[min(support),max(support)],
                       'openingWidth':opening[0], 'springHeight':max(support)+opening[1]-pad,
                       'passageDepth':384, 'archRise':192, 'headerHeight':max(support)+1152-pad,
                       'eventId':1001 if south else 1002,
                       'behavior':'open passage; plaque status-only; original pass quest deferred',
                       'layoutAdjustment':{'original':feature['point'],'revised':point,
                                           'reason':'Match native road centre across the gate opening'}})
    return result


def build():
    plan = json.loads((PROJECT / 'layout.json').read_text())
    alvar = {e['id']: e for e in json.loads((PROJECT / 'alvar_style_candidates.json').read_text())['entries']}
    assert set(CHOICES) == {b['id'] for b in plan['buildings']}
    texture_paths = {}
    for folder in [ROOT / 'assets_dev/worlds/mm8/textures', ROOT / 'assets_dev/engine/textures']:
        for p in sorted(folder.glob('*')):
            texture_paths.setdefault(p.stem.lower(), p)
    local_art={'mm5map':"Original schematic merchandise for Joe's stall; not the world minimap."}
    local_art['mm5lunch']="Joe's planned out-to-lunch counter notice; visual identity only, no resident schedule."
    local_art['mm5royal']='Original subdued crown banner for the restored Kalindra exterior; design interpretation.'
    local_art.update({key:'Original readable timber sign; source meaning and direction retained.'
                      for key in prepare_source_signs.FACES.values()})
    local_art.update({key:'Original low-resolution painted material for retained message bottles; no pickup effect.'
                      for key in prepare_message_bottles.PALETTE.values()})
    local_art.update({key:'Original source-inspired Monga Melon rind or purple leaf material; no quest item grant.'
                      for key in ['mm5melon','mm5vine']})
    local_art.update({key:'Original painted gemsmith trade emblem; no reward or price representation.'
                      for key in PALETTES['gemsmith_signs'].values()})
    local_art.update({key:'Original named mapmaker plaque or craft emblem for an existing venue; decorative only.'
                      for key in author_frontage_signs.PALETTE.values()})
    local_art.update({key:'Original civic, membership or hiring notice display; no functional service or reward.'
                      for key in author_public_notices.PALETTE.values()})
    for key in local_art:
        image=OUTPUT/'runtime/worlds/mm5/textures'/f'{key}.png'
        image.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run(['convert',str(OUTPUT/'art'/f'{key}.svg'),'-strip',str(image)],check=True)
        texture_paths[key]=image
    materials = {}
    pyramid_material=prepare_pyramid.material()
    pyramid_copy=OUTPUT/'runtime/worlds/mm5/textures/mm5pyrst.bmp'
    shutil.copy2(prepare_pyramid.STONE,pyramid_copy)
    texture_paths['mm5pyrst']=pyramid_copy
    for palette in PALETTES.values():
        for key in palette.values():
            p = texture_paths[key]
            materials[key] = {'path': str(p.relative_to(ROOT)),
                              'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
            if key=='mm5pyrst':
                materials[key].update({'sourceBitmap':pyramid_material['sourceBitmap'],
                                       'sourceBitmapSha256':pyramid_material['sha256'],
                                       'purpose':pyramid_material['purpose']})
            if key in local_art:
                original=OUTPUT/'art'/f'{key}.svg'
                materials[key].update({'sourceSvg':str(original.relative_to(ROOT)),
                                       'sourceSvgSha256':hashlib.sha256(original.read_bytes()).hexdigest(),
                                       'purpose':local_art[key]})
    entries = []
    for b in plan['buildings']:
        form, eave, peak = CHOICES[b['id']]
        facing = b.get('doorFacing', COUNTRY_FACING.get(b['id'], 'S'))
        normal = FACING[facing]
        tangent = [-normal[1], normal[0]]
        wx, wy = b['envelope']
        width, depth = (wx, wy) if facing in ['N', 'S'] else (wy, wx)
        # Reserve 32 units for roof overhang on each side. Move the facade inward,
        # preserving the original frontage direction and short approach reservation.
        width -= 64
        depth -= 64
        if b['id']=='reger':
            # The landscape reserves a smaller solid foundation on the river islet.
            # Its larger envelope is roof/shore clearance, not buildable wall area.
            fx,fy=b['foundationFootprint']
            width,depth=(fx,fy) if facing in ['N','S'] else (fy,fx)
        center = b['center']
        origin = [center[i] + normal[i] * depth / 2 for i in range(2)]
        palette = 'alvar_domestic'
        if b['id'] in ['jail', 'king', 'kalindra', 'western', 'sewer_out']:
            palette = 'garrote_fortified'
        elif b['id'] in ['guild', 'bank', 'mayor', 'temple', 'tower']:
            palette = 'alvar_civic'
        elif b['id']=='training':
            palette='alvar_institution'
        if b['id']=='jail':
            palette='garrote_jail'
        if b['id']=='temple':
            palette='alvar_temple'
        if b['id']=='kalindra':
            palette='kalindra_royal'
        if b['id'] in prepare_camps.IDS:
            palette='camp_equipment'
        venues = []
        for v in b.get('venues', []):
            offset = sum((v['door'][i] - origin[i]) * tangent[i] for i in range(2))
            assert abs(offset) + 64 <= width / 2, (b['id'], v['id'], offset)
            venues.append({**v, 'originalDoor': v['door'],
                           'door': [origin[i] + tangent[i] * offset for i in range(2)],
                           'localOffset': offset, 'behavior': 'named status-only placeholder'})
        if not venues and form not in ['sanctuary', 'natural_shelter', 'descent_rim', 'rope_anchor']:
            venues.append({'id': b['semanticId'] + '/entrance', 'door': origin, 'facing': facing,
                           'doorSize': [128, 256], 'localOffset': 0,
                           'occupants': [person['id'] for person in b['architecture']['people']],
                           'behavior': 'named status-only placeholder'})
        for venue in venues:
            # Native bitmap fonts consume legacy bytes, so authored UI labels use
            # plain punctuation. Preserve source typography in title/evidence.
            label = b['title'].split(' / ')[0]
            if ':' in venue['id'].split('/')[-1]:
                contacts = [p['name'] for p in b['architecture']['people']
                            if p['id'] in venue['occupants']]
                assert contacts, venue['id']
                label = ' / '.join(contacts)
            venue['displayLabel'] = label.translate(str.maketrans({'’': "'", '‘': "'", '–': '-', '—': '-'}))
            assert venue['displayLabel'].isascii(), venue['displayLabel']
        parts = components(form, width, depth, eave, peak)
        details=[]
        notes=[]
        if b['id'] in prepare_camps.IDS:
            parts,notes=prepare_camps.configure(b['id'],venues[0],origin,tangent,normal)
        if b['id']=='kalindra':
            parts=[{'id':'main_keep','bounds':[-640,1536,896,3840],'roof':'hip','ridgeAxis':'y',
                    'eave':2048,'top':2560,'windowLevels':[256,768,1280,1792]},
                   {'id':'south_wing','bounds':[-1408,0,-640,2688],'roof':'hip','ridgeAxis':'y',
                    'eave':768,'top':1024,'windowLevels':[256,512]},
                   {'id':'north_wing','bounds':[896,256,1408,3136],'roof':'hip','ridgeAxis':'y',
                    'eave':1024,'top':1280,'windowLevels':[256,768]}]
            for name,cx,cy,radius,cut,top in [('south_tower',-1120,768,352,96,3584),
                                            ('north_tower',1120,3264,320,96,3328)]:
                polygon=[(cx-radius+cut,cy-radius),(cx+radius-cut,cy-radius),
                         (cx+radius,cy-radius+cut),(cx+radius,cy+radius-cut),
                         (cx+radius-cut,cy+radius),(cx-radius+cut,cy+radius),
                         (cx-radius,cy+radius-cut),(cx-radius,cy-radius+cut)]
                parts.append({'id':name,'bounds':[cx-radius,cy-radius,cx+radius,cy+radius],
                              'polygon':polygon,'roof':'royal_tower','eave':top-160,'top':top,
                              'windowLevels':[512,1024,1536,2048,2560,3072]})
            parts += [{'id':'entry_arch','bounds':[-640,0,896,256],'roof':'castle_gate',
                       'openingWidth':768,'eave':576,'archRise':192,'top':1024},
                      {'id':'court_paving','bounds':[-624,-96,880,1536],'roof':'court_paving',
                       'eave':6,'top':6}]
            venues[0].update({'localOffset':128,'localDepth':1536,
                             'door':[origin[i]+tangent[i]*128-normal[i]*1536 for i in range(2)]})
            details=[{'id':'south_court_bench','bounds':[-592,512,-16,-520,800,160]},
                     {'id':'north_court_bench','bounds':[784,1024,-16,856,1312,160]}]
            notes += ['Restored friendly royal composition. A real open arch leads into an unequal courtyard; '
                      'the ordinary 128 by 256 BLV door sits on the offset keep, not across the gate passage.',
                      'Main keep apex 2560, south principal tower 3584, north tower 3328; lower wings 1024/1280. '
                      'Wings terminate into the higher keep and towers. No donor vertices or enlarged door art.',
                      'Court paving is six units above the native pad to avoid coplanar terrain. Two benches '
                      'face usable waiting space; crown banners identify the restored royal seat. '
                      'All court NPCs, services and restoration stages stay in attached interior/source records.']
        if b['id']=='western':
            parts=[{'id':'shaft','bounds':[-672,0,672,1408],'roof':'watch_tower',
                    'eave':eave,'top':peak,'windowLevels':[512,1024,1536,2048]},
                   {'id':'roof_access','bounds':[-384,864,0,1216],'roof':'hip',
                    'eave':272,'top':384,'baseHeight':eave,'windowLevels':[]}]
            venues[0]['displayLabel']='Great Western Tower - ground entrance'
            venues.append({'id':b['semanticId']+'/roof_entrance',
                           'door':[origin[i]+tangent[i]*-192-normal[i]*864 for i in range(2)],
                           'facing':facing,'doorSize':[128,256],'localOffset':-192,'localDepth':864,
                           'heightAbovePad':eave,'occupants':[],
                           'displayLabel':'Great Western Tower - roof entrance',
                           'behavior':'named status-only placeholder; future roof-first access'})
            notes.append('Original square watchtower with narrow high windows, horizontal stone bands and '
                         'crenellated terrace. Terrace 2432 leaves a full-size roof door and its pitched cover '
                         'below the retained 2816 apex; distinct from Ellinger\'s slender pitched octagon.')
            notes.append('Keep the ground and roof routes separate: no exterior staircase bypasses the future '
                         'Dreyfus/Skyroad access problem. Roof arrival local (128,512,2432) has clear walking '
                         'space to the upper door. Both doors are status-only; Skyroad and BLV travel stay deferred.')
        if b['id'] in ['reger','luna','vespar']:
            for venue in venues:
                venue['occupants']=[person['id'] for person in b['architecture']['people']]
            notes.append('Retain the source contact at one ordinary placeholder door; no resident actor or service.')
        if b['id']=='reger':
            parts[0]['ridgeAxis']='y'
            details.append({'id':'study_ledge','bounds':[192,208,96,232,352,128]})
            notes.append('Honor the landscape 448 by 384 world-axis foundation within the larger shore reservation. '
                         'A small wall-supported study ledge faces the quiet south shore; no automatic road spur. '
                         'Eave 288 leaves clearance above the normal 256-high door.')
        if b['id']=='luna':
            parts=[{'id':'care_hut','bounds':[-384,0,128,384],'roof':'hip','eave':eave,'top':peak},
                   {'id':'animal_shelter','bounds':[128,192,384,576],'roof':'lean_to',
                    'eave':208,'top':256,'stockBench':False}]
            details.append({'id':'animal_trough','bounds':[192,448,-32,320,528,64]})
            notes.append('Small dwelling and unequal lower animal shelter; an inert drinking trough replaces '
                         'workshop stock. The separate three-socket altar sits in the western clearing. '
                         'Sockets stay empty: stolen statuettes, animal population and quest rewards are deferred.')
        if b['id']=='vespar':
            parts[0]['ridgeAxis']='y'
            parts.append({'id':'entry_hood','bounds':[-144,-128,144,0],'roof':'entry_hood',
                          'eave':288,'top':304,'postWidth':24})
            details.append({'id':'astronomy_dial','bounds':[416,256,-32,512,352,224]})
            notes.append('Maintained compact retreat with sheltered entrance and one small original metal '
                         'astronomical dial beside the house. This is scenery, not a spell shop or quest item.')
        if form=='paired_frontage':
            notes.append('Distinct venues share one main roof; avoid intersecting hip ends.')
        if form=='cottage_shed':
            notes.append('Open lower rear shed for the working yard, with no invented occupied annex.')
        if b['id']=='tavern':
            parts=[{'id':'entrance_wing','bounds':[-width/2,0,width/2,512],
                    'roof':'hip','eave':320,'top':512},
                   {'id':'guest_hall','bounds':[-384,512,384,depth],
                    'roof':'hip','eave':eave,'top':peak}]
            notes.append('Wide lower entrance wing in front of the taller guest hall; preserve the single shared venue.')
        if b['id']=='jail':
            parts[0]['bounds'][0]+=64
            parts[0]['bounds'][2]-=64
            parts[0]['windowLevels']=[256]
            for x in [-width/2,width/2-64]:
                for y in [0,depth-128]:
                    details.append({'id':'guard_pier','bounds':[x,y,-64,x+64,y+128,768]})
            notes.append('Covered prison wing with high barred windows, four masonry piers and reinforced threshold; '
                         'Jasper and prison beds remain indoors and deferred.')
        if b['id']=='king':
            parts=[{'id':'entry_wing','bounds':[-width/2,0,width/2,384],
                    'roof':'parapet','eave':384,'top':576,'windowLevels':[256]},
                   {'id':'audience_hall','bounds':[-672,384,672,depth],
                    'roof':'hip','eave':704,'top':896,'windowLevels':[256]}]
            notes.append('Low controlled entrance wing and taller covered audience hall. Throne, guards and disks '
                         'belong to the deferred interior, not the outdoor yard.')
        if b['id']=='puzzle':
            parts=[{'id':'desk_wing','bounds':[-width/2,0,width/2,448],
                    'roof':'hip','eave':384,'top':512},
                   {'id':'west_puzzle_bay','bounds':[-width/2,448,-32,depth],
                    'roof':'gable','ridgeAxis':'y','eave':512,'top':704,'windowLevels':[256]},
                   {'id':'east_puzzle_bay','bounds':[32,448,width/2,depth],
                    'roof':'gable','ridgeAxis':'y','eave':512,'top':704,'windowLevels':[256]}]
            notes.append('Two long storage roofs behind a lower public desk wing; the 18 puzzle chests remain '
                         'attached-interior records. One shared exterior venue, no outdoor loot substitutes.')
            details.append({'id':'gutter_spine','bounds':[-32,448,-64,32,depth,512]})
        if b['id']=='joe':
            for venue in venues:
                venue['interactionSurface']='stall counter'
                venue['additionalInteractionSurfaces']=['displayed map']
            notes.append('Four-post open timber stall inside the original 512-square envelope. '
                         'The counter dispatches the retained Joe venue; no invented house door.')
            notes.append('Original SVG cartographic merchandise is schematic, not the authoritative world map; '
                         'rendered at native 128-square texture resolution.')
        if b['id']=='tower':
            half=width/2
            flat=round(half*math.tan(math.pi/8),3)
            parts[0]['polygon']=[[-flat,0],[flat,0],[half,half-flat],[half,half+flat],
                                  [flat,depth],[-flat,depth],[-half,half+flat],[-half,half-flat]]
            parts[0]['windowLevels']=[0,512,1024,1536,2048]
            notes.append('Regular octagonal shaft with five window levels, stone courses and restrained pitched cap; '
                         'highest point remains 3072 above the pad. Normal-size door, no stretched reference mesh.')
            notes.append('Native street review nearly hid the initial 512-high cap behind the shaft. Lowered the '
                         'eave from 2560 to 2304 while preserving the 3072 apex, making the cap visible across town.')
        if b['id']=='temple':
            parts=[{'id':'nave','bounds':[-480,0,320,896],'roof':'gable','ridgeAxis':'y','eave':704,'top':1024},
                   {'id':'service_wing','bounds':[-800,0,-480,960],'roof':'hip','ridgeAxis':'y',
                    'eave':384,'top':512},
                   {'id':'contact_wing','bounds':[320,128,800,832],'roof':'hip','ridgeAxis':'y',
                    'eave':384,'top':576},
                   {'id':'apse','bounds':[-480,896,320,1216],'roof':'apse','eave':512,'top':704,
                    'polygon':[[-480,896],[320,896],[320,1056],[80,1216],[-240,1216],[-480,1056]],
                    'windowLevels':[0]},
                   {'id':'porch','bounds':[-224,-160,224,0],'roof':'entry_hood','eave':352,'top':416}]
            notes.append('Higher nave, unequal lower service/contact wings and faceted rear apse. The single venue '
                         'still includes Imble without making him proprietor. Plain original MOK inscription; '
                         'no imported MM8 religious emblem.')
        if b['id']=='crafts':
            parts += [{'id':'tailor_canopy','bounds':[-576,-160,-48,0],
                       'roof':'entry_hood','eave':272,'top':304,'postWidth':32},
                      {'id':'cobbler_canopy','bounds':[48,-128,464,0],
                       'roof':'entry_hood','eave':272,'top':304,'postWidth':32}]
            notes.append('Unequal shallow work canopies distinguish the two venue bays; retain their original doors.')
        if b['id']=='herbalist':
            details.append({'id':'drying_rack','bounds':[-304,640,0,-144,688,184]})
        if b['id']=='keeper':
            details.append({'id':'kennel','bounds':[-232,536,0,-80,664,144]})
        if b['id']=='forge':
            details += [{'id':'anvil','bounds':[-284,1144,-32,-108,1224,144]},
                        {'id':'ore_bin','bounds':[-432,1104,-32,-328,1200,80]}]
            notes.append('Low anvil and open ore bin within the stock shelter; inert independently authored props.')
        if b['id'] in PALETTES['gemsmith_signs']:
            hall_depth=352 if depth==576 else 512
            canopy_left=0 if b['id'] in ['emerald','diamond'] else -width/2
            canopy_right=width/2 if b['id'] in ['emerald','diamond','sapphire'] else 0
            parts=[{'id':'work_hall','bounds':[-width/2,0,width/2,hall_depth],
                    'roof':'gable','ridgeAxis':'y' if depth>width else 'x','eave':eave,'top':peak},
                   {'id':'sorting_canopy','bounds':[canopy_left,hall_depth,canopy_right,depth],
                    'roof':'lean_to','eave':256,'top':304}]
            notes.append('Compact independent gemsmith shop with a 128 by 256 door, painted trade emblem, '
                         'covered sorting bench, inert stone trays and open side access. Preserve individual '
                         'future recipes; no actors, services, loose inventory items or rewards.')
            notes.append('Rear sorting canopy uses the left side for ruby, right side for emerald/diamond and '
                         'full rear bay for sapphire. Sign and stock are original details within the reserved envelope.')
            notes.append('The first render clipped the trade sign behind the fascia. Eaves raised from 320 to '
                         '352, preserving the roof apex and ordinary door; 16 units remain above the sign.')
        if b['id']=='diviners':
            details.extend({'id':'entrance_step','bounds':[-128,d,-112,128,d+64,z]}
                           for d,z in [(-192,-64),(-128,-32),(-64,0)])
            notes.append('Three shallow native stone treads join the graded lane to the original 864-unit threshold; '
                         'their declared bounds reserve the approach during scenery placement.')
        if b['id']=='training':
            notes.append('Narrow hall walls within the original envelope for full-height piers; hood extends '
                         '160 units into the frontage while preserving both door positions.')
            parts[0]['bounds'][0]+=64
            parts[0]['bounds'][2]-=64
            parts.append({'id':'entrance_hood','bounds':[-320,-160,320,0],
                          'roof':'entry_hood','eave':288,'top':352})
            for x,direction in [(-width/2+64,-1),(width/2-64,1)]:
                for y in [48,512,1024,depth-48]:
                    other=x+direction*96
                    details.append({'id':'pier','bounds':[min(x,other),y-48,-64,max(x,other),y+48,576]})
        entries.append({
            'id': b['id'], 'semanticId': b['semanticId'], 'title': b['title'], 'label': b['label'],
            'district': b['district'], 'quality': b['quality'], 'qualityEvidence': b['qualityEvidence'],
            'purpose': b['purpose'], 'form': form, 'palette': palette,
            'center': center, 'reservedEnvelope': b['envelope'], 'frontOrigin': origin,
            'frontOutward': normal, 'frontTangent': tangent, 'facing': facing,
            'localFootprint': [width, depth], 'padHeight': b.get('padHeightProposal'),
            'components': parts, 'venues': venues, 'details':details,
            'implementationNotes':notes,
            'people': b['architecture']['people'], 'plannedProps': b.get('props', []),
            'interiorContacts': [{k: contact[k] for k in ['id', 'name', 'role', 'placement']}
                                 for contact in plan['attachedInteriorContacts']
                                 if contact['exteriorOwner'] == b['id']],
            'sourceIdentities': b['sources'], 'referenceIntent': b['architecture']['newComposition'],
            'alvarReference': alvar.get(b['id']), 'garroteReference': b['architecture']['referenceModels'],
            'geometryStatus': 'specified; geometry and native visual acceptance pending',
        })
        if b['id']=='western':
            entries[-1]['arrivals']=[
                {'id':b['semanticId']+'/ground_return',
                 'position':[origin[i]+normal[i]*256 for i in range(2)]+[b['padHeightProposal']],
                 'purpose':'Future ground BLV return; not the roof route','active':False},
                {'id':b['semanticId']+'/skyroad_roof',
                 'position':[origin[i]+tangent[i]*128-normal[i]*512 for i in range(2)]
                            +[b['padHeightProposal']+eave],
                 'purpose':'Future Skyroad roof arrival and upper BLV return; clear terrace east of access hut',
                 'active':False}]
        if b['id']=='kalindra':
            entries[-1]['arrivals']=[{'id':b['semanticId']+'/ground_return',
                                      'position':[origin[i]+normal[i]*512 for i in range(2)]
                                                 +[b['padHeightProposal']],
                                      'purpose':'Future castle BLV return outside the open entry arch',
                                      'active':False}]
    event_ids=json.loads((OUTPUT/'venue_event_ids.json').read_text())
    assert len(event_ids)==len(set(event_ids.values()))
    for entry in entries:
        author_frontage_signs.configure(entry)
        if entry['id'] in author_public_notices.BOARDS:
            entry['publicNotice'] = {**author_public_notices.BOARDS[entry['id']],
                                     'texture': author_public_notices.PALETTE[entry['id']]}
        if entry['id'] in prepare_natural_entrances.IDS:
            prepare_natural_entrances.configure(entry,(PROJECT/'landscape/heightmap.raw').read_bytes())
        if entry['id']=='sewer_out':
            prepare_sewer.configure(entry,(PROJECT/'landscape/heightmap.raw').read_bytes())
        if entry['id']=='skyrope':
            prepare_skyrope.configure(entry,(PROJECT/'landscape/heightmap.raw').read_bytes())
        if entry['id'] in prepare_clearings.PLACEMENTS:
            prepare_clearings.configure(entry,(PROJECT/'landscape/heightmap.raw').read_bytes())
        for venue in entry['venues']:
            venue['eventId']=event_ids[venue['id']]
            if 'nativeDecorationId' in venue:
                record=next(r for r in entry['nativeScenery'] if r['id']==venue['nativeDecorationId'])
                record['eventId']=venue['eventId']
    fountain = next(r for r in json.loads((PROJECT/'landscape/decorations.json').read_text())['records']
                    if r['featureId'] == 'healing_fountain')
    props = [{'id':'healing_fountain', 'semanticId':fountain['id'], 'title':'Healing Fountain',
              'frontOrigin':fountain['position'][:2], 'frontOutward':[0,-1], 'frontTangent':[1,0],
              'padHeight':fountain['foundation']['platformZ'], 'palette':'courtyard_stone',
              'purpose':fountain['purpose'], 'foundation':fountain['foundation'],
              'futureInteraction':fountain['interaction'], 'eventId':1000,
              'behavior':'status-only placeholder; no healing yet', 'radius':256}]
    pool = next(f for f in plan['features'] if f['id']=='training_pool')
    props.append({'id':'training_pool', 'semanticId':'mm5:sw/feature/training_pool',
                  'title':"Ordana's practice pool", 'frontOrigin':pool['point'],
                  'frontOutward':[0,-1], 'frontTangent':[1,0], 'padHeight':832,
                  'palette':'courtyard_stone', 'bounds':[-448,-256,448,320],
                  'localFootprint':[896,576], 'radius':544, 'purpose':pool['purpose'],
                  'sourceFeature':pool, 'foundation':{'platformZ':832,'skirtBottomZ':608},
                  'behavior':'inert constructed basin; swimming instruction remains at the training door',
                  'implementationNotes':['Retaining basin above the north-rising native grade; water at 832, rim at 848.',
                                         'One 64-deep north step at 816 faces the higher yard; preserve the south passage.']})
    luna=next(b for b in entries if b['id']=='luna')
    props.append({'id':'luna_altar','semanticId':'mm5:sw/feature/luna_altar',
                  'title':"Luna's altar of magical beasts",
                  'frontOrigin':[luna['frontOrigin'][0]-640,luna['frontOrigin'][1]+200],
                  'frontOutward':[0,-1],'frontTangent':[1,0],'padHeight':576,
                  'palette':'courtyard_stone','bounds':[-160,-80,160,80],
                  'localFootprint':[320,160],'radius':180,'eventId':1010,
                  'approachDistance':400,'standingRadius':256,
                  'purpose':'Three empty sockets preserve the source stolen-statuette quest setting.',
                  'futureInteraction':'Three returned golden statuettes restore the altar aura through Luna; deferred.',
                  'behavior':'status-only placeholder; no statuettes, healing, levels or quest progress',
                  'foundation':{'platformZ':576,'skirtBottomZ':544}})
    props.extend(prepare_town_sewers.prepare((PROJECT/'landscape/heightmap.raw').read_bytes()))
    props.extend(prepare_town_chests.prepare((PROJECT/'landscape/heightmap.raw').read_bytes()))
    props.extend(prepare_source_wells.prepare((PROJECT/'landscape/heightmap.raw').read_bytes()))
    props.extend(prepare_source_signs.prepare((PROJECT/'landscape/heightmap.raw').read_bytes()))
    props.append(prepare_source_shrine.prepare((PROJECT/'landscape/heightmap.raw').read_bytes()))
    props.extend(prepare_message_bottles.prepare((PROJECT/'landscape/heightmap.raw').read_bytes()))
    props.extend(prepare_melon_patches.prepare((PROJECT/'landscape/heightmap.raw').read_bytes()))
    props.extend(prepare_wreck.prepare((PROJECT/'landscape/heightmap.raw').read_bytes()))
    props.extend(prepare_barbarian_camp.prepare((PROJECT/'landscape/heightmap.raw').read_bytes()))
    props.extend(prepare_pyramid.prepare((PROJECT/'landscape/heightmap.raw').read_bytes()))
    props.append(author_ranger_yard.prepare((PROJECT/'landscape/heightmap.raw').read_bytes()))
    props.extend(author_training_yard.prepare((PROJECT/'landscape/heightmap.raw').read_bytes()))
    props.extend(author_town_working_details.prepare((PROJECT/'landscape/heightmap.raw').read_bytes()))
    from prepare_regional_understory import prepare as prepare_regional_understory
    scenery_groups = prepare_regional_understory((PROJECT/'landscape/heightmap.raw').read_bytes())
    from world_rim import plan_rim
    rim = plan_rim(PROJECT)
    rock = ROOT/'assets_dev/worlds/mm8/textures/RCTYL.bmp'
    materials['rctyl'] = {'path': str(rock.relative_to(ROOT)),
                          'sha256': hashlib.sha256(rock.read_bytes()).hexdigest()}
    write(OUTPUT/'world_rim.json', rim)
    spec = {'version': 1, 'world': 'mm5', 'map': 'mm5_sw.odm', 'semanticId': 'mm5:sw',
            'status': 'architectural implementation specification; not visual acceptance',
            'sourceLayoutSha256': hashlib.sha256((PROJECT / 'layout.json').read_bytes()).hexdigest(),
            'geometryPolicy': 'New geometry only; catalogue native meshes are read-only references.',
            'artPolicy': 'Original resolution; no upscale or new AI art required for this milestone.',
            'interactionPolicy': 'Status-only placeholders; zero rewards, NPCs, monsters and encounters.',
            'palettes': PALETTES, 'materials': materials, 'buildings': entries, 'props':props,
            'sceneryGroups': scenery_groups,
            'worldRim': rim,
            'fortifications': next(f for f in plan['features'] if f['id'] == 'town_wall'),
            'gates': prepare_gates(plan),
            'bridges': [f for f in plan['features'] if f['kind'] == 'bridge']}
    write(OUTPUT / 'architecture.json', spec)
    lines = ['# Castleview–Kalindra implementation architecture', '',
             'This is the current Alvar/Garrote implementation assignment derived from the accepted goal.',
             'It supersedes the earlier all-Garrote material assignment in the historical wireframe.',
             'Locations, people, venue identities and source interactions remain grounded in `layout.json`.', '',
             'The [structured specification](architecture.json) records every component footprint, roof form,',
             'height, facade basis, transformed door, resident/venue ownership and actual texture source.',
             'Geometry is newly authored. Reference mesh dimensions are comparisons, never scale instructions.', '',
             'Facade planes start 32 units inside the planning envelope to reserve roof overhang; exact road',
             'snapping and native terrain contact can require documented corrections during the blockout.',
             'Natural sites retain specialist forms and receive no invented domestic building.', '',
             'See [the specification audit](../review/architecture_specification/README.md) for retained identities',
             'and [town detail completion](TOWN_DETAIL_COMPLETION.md) for remaining exterior work versus deferred interiors.', '',
             '| Premises | Form | Material family | Eave / highest top above pad | Venues |',
             '| --- | --- | --- | ---: | ---: |']
    for e in entries:
        parts = e['components']
        lines.append(f'| {e["label"]} {e["title"]} | {e["form"]} | {e["palette"]} | '
                     f'{max(p["eave"] for p in parts)} / {max(p["top"] for p in parts)} | {len(e["venues"])} |')
    lines += ['', '## First visual checks', '',
              'Review guild, forge, training hall, one modest shared home and the fountain court with the south gate.',
              'Keep ordinary door panels 128×256 and facade modules at one native unit per texel. Inspect matching',
              'front/oblique and player-height views; correct the largest discrepancy before repeating the kit.',
              'Alvar civilian materials and Garrote fortifications must also be reviewed together in native lighting.', '',
              '## Rebuild', '', 'From the repository root:', '', '```sh',
              'python3 level_generation/projects/mm5_castleview_kalindra/prepare_architecture.py', '```', '',
              'This regenerates the implementation specification only. It does not regenerate the historical',
              'wireframe, copy native geometry or claim native/runtime completion.', '']
    (OUTPUT / 'ARCHITECTURE.md').write_text('\n'.join(lines))
    print(f'Prepared {len(entries)} assemblies/sites, {sum(len(e["venues"]) for e in entries)} entrance venues, '
          f'{len(materials)} verified material files.')


if __name__ == '__main__':
    build()
