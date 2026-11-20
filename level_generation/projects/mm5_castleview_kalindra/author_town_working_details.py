"""Small owned exterior work settings; no actors, pickups or service behavior."""
import math

from author_props import ground_at


def prepare(height):
    definitions = [
        ('hiring_repair', 'workyard', [-7900, -4810], [0, 1], [-1, 0], [-144, -48, 144, 48],
         'A trestle table with a partly repaired timber box and hammer beside the hiring hall.'),
        ('keeper_workbench', 'keeper', [760, 2280], [1, 0], [0, 1], [-144, -48, 144, 48],
         'A narrow outdoor workbench and cut boards on the cottage side, clear of its kennel and door.'),
        ('nadia_storage', 'nadia', [-8020, 1280], [0, 1], [-1, 0], [-100, -48, 100, 48],
         'Unequal stacked personal-storage boxes behind the worn cottage, away from the west-gate lane.'),
        ('workers_sweep', 'workers', [-5360, 2612], [1, 0], [0, -1], [-40, -28, 56, 60],
         'A broom and long-handled scraper in a compact rear-wall setting, leaving the shared bench clear.'),
        ('fountain_court_seat', 'bank', [-3650, -900], [0, -1], [-1, 0], [-144, -38, 144, 42],
         'One public bench facing the healing fountain from its clear eastern pocket; preserve both bank approaches.'),
    ]
    return [{'id':name, 'semanticId':'mm5:castleview/'+owner+'/'+name, 'owner':owner,
             'title':name.replace('_',' '), 'kind':'town working detail', 'frontOrigin':point,
             'frontTangent':tangent, 'frontOutward':outward, 'bounds':bounds,
             'padHeight':math.ceil(ground_at(height,point)/32)*32, 'palette':'working_props',
             'radius':math.ceil(max(math.hypot(x,y) for x in bounds[::2] for y in bounds[1::2])),
             'purpose':purpose, 'behavior':'inert scenery; no actor, pickup, reward or event'}
            for name,owner,point,tangent,outward,bounds,purpose in definitions]


def author_detail(author, prop, palette, height):
    panels, supports = [], []

    def world(x,y):
        return [prop['frontOrigin'][i]+prop['frontTangent'][i]*x-prop['frontOutward'][i]*y for i in range(2)]

    def box(bounds, material='wood', fitted=False, whole_bitmap=False):
        x0,y0,z0,x1,y1,z1 = bounds
        if fitted:
            footprint = [world(x,y) for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]]
            bottom = math.floor(min(ground_at(height,point) for point in footprint))-16
            z0 = bottom-prop['padHeight']
            supports.append({'footprint':footprint,'bottom':bottom})
        start = len(panels)
        author.box(panels,[x0,y0,z0,x1,y1,z1],palette[material])
        if whole_bitmap:
            for i in range(start,len(panels)):
                vertices,key,_ = panels[i]
                panels[i] = vertices,key,[(0,0),(1,0),(1,1),(0,1)]

    if prop['id']=='fountain_court_seat':
        for y in [-32,-9,14]:
            box([-144,y,64,144,y+20,80])
        for x in [-108,84]:
            box([x,-26,0,x+24,30,64],fitted=True)
            box([x,22,64,x+24,38,160])
        box([-144,26,110,144,42,138])
    elif prop['id'] in ['hiring_repair','keeper_workbench']:
        for y in [-48,-16,16]:
            box([-144,y,104,144,y+30,120])
        for x in [-120,96]:
            box([x,-40,0,x+24,40,104],fitted=True)
        box([-120,-8,44,120,8,64])
        if prop['id']=='hiring_repair':
            # An open box under repair: bottom, two ends and one side; the fourth side remains absent.
            box([-100,-28,120,4,28,128])
            for x in [-100,-4]:
                box([x,-28,128,x+8,28,176])
            for z in [128,152]:
                box([-92,20,z,-4,28,z+20])
            box([24,-28,120,120,-10,128])
            box([44,10,120,100,18,128])
            box([90,2,124,112,26,140],'metal')
        else:
            box([-110,-28,120,18,-4,128])
            box([-48,4,120,110,32,132])
            box([102,-26,120,110,-2,132],'metal')
    elif prop['id']=='nadia_storage':
        box([-100,-44,0,12,44,96],'crate',fitted=True,whole_bitmap=True)
        box([20,-32,0,100,48,64],'crate',fitted=True,whole_bitmap=True)
        box([-88,-32,96,-8,32,152],'crate',whole_bitmap=True)
    else:
        # A tapered bundle gives the twig broom a different silhouette from the scraper.
        footprint = [world(-8+24*math.cos(i*math.tau/12),24*math.sin(i*math.tau/12)) for i in range(12)]
        bottom = math.floor(min(ground_at(height,p) for p in footprint))-16
        lower = [(-8+24*math.cos(i*math.tau/12),24*math.sin(i*math.tau/12),bottom-prop['padHeight'])
                 for i in range(12)]
        upper = [(-8+8*math.cos(i*math.tau/12),8*math.sin(i*math.tau/12),52) for i in range(12)]
        for i in range(12):
            author.panel(panels,[lower[i],lower[(i+1)%12],upper[(i+1)%12],upper[i]],palette['wood'])
        author.panel(panels,upper,palette['wood'])
        supports.append({'footprint':footprint,'bottom':bottom})
        box([-12,-8,40,-4,0,216])
        box([-19,-11,40,3,11,48],'metal')
        scraper_start = len(panels)
        box([36,-6,0,44,2,196],fitted=True)
        box([26,-6,4,56,-2,36],'metal')
        # Lean each tool onto the actual rear wall at local Y=56. Keep its buried feet in place.
        for i,(vertices,key,uv) in enumerate(panels):
            slope = 56/216 if i < scraper_start else 54/196
            panels[i] = ([(x,y+max(0,z)*slope,z) for x,y,z in vertices],key,uv)
    prop['groundSupports'] = supports
    author.model(prop['id'],panels,prop)
    author.semantic['props'].append(prop)
