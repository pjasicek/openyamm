"""Two compact inert practice targets on the clear south side of Tog's hall."""
import math

from author_props import ground_at

PALETTE = {'wood':'t05a10', 'cloth':'gnecclg2', 'metal':'gn_mtl03'}


def prepare(height):
    props = []
    for name, point, kind in [('training_pell',[-464,-348],'padded striking post'),
                              ('training_shield',[-72,-400],'timber shield target')]:
        pad = math.ceil(ground_at(height,point)/32)*32
        foot = [[point[0]+x,point[1]+y] for x,y in [(-20,0),(20,0),(20,32),(-20,32)]]
        bottom = math.floor(min(ground_at(height,p) for p in foot))-16
        props.append({'id':name,'semanticId':'mm5:castleview/'+name,'owner':'training','title':kind,
                      'kind':'training target','targetKind':kind,'frontOrigin':point,
                      'frontTangent':[1,0],'frontOutward':[0,-1],'padHeight':pad,
                      'palette':'training_targets','radius':80,'bounds':[-76,-44,76,36],
                      'groundSupports':[{'footprint':foot,'bottom':bottom}],
                      'clearApproach':[-100,-240,100,-72],
                      'behavior':'inert architectural scenery; no actor, damage, training or reward handler',
                      'purpose':'Close practice beside the training hall; preserve both west doors and north pool route.'})
    return props


def author_target(author, prop, palette):
    panels = []
    bottom = prop['groundSupports'][0]['bottom']-prop['padHeight']
    author.box(panels,[-20,0,bottom,20,32,248 if prop['targetKind']=='padded striking post' else 224],palette['wood'])
    if prop['targetKind']=='padded striking post':
        # A chamfered, cloth-covered pad strapped to the pole, with a small wooden crosspiece.
        author.box(panels,[-76,4,164,76,24,184],palette['wood'])
        outline=[(-32,-40),(32,-40),(44,-28),(44,4),(32,16),(-32,16),(-44,4),(-44,-28)]
        for i,(x,y) in enumerate(outline):
            xx,yy=outline[(i+1)%len(outline)]
            author.panel(panels,[(x,y,104),(xx,yy,104),(xx,yy,220),(x,y,220)],palette['cloth'])
        author.panel(panels,[(x,y,220) for x,y in outline],palette['cloth'])
        author.panel(panels,[(x,y,104) for x,y in reversed(outline)],palette['cloth'])
        for z in [120,196]:
            band=[(x*1.025,(y+12)*1.025-12) for x,y in outline]
            for i,(x,y) in enumerate(band):
                xx,yy=band[(i+1)%len(band)]
                author.panel(panels,[(x,y,z),(xx,yy,z),(xx,yy,z+6),(x,y,z+6)],palette['metal'])
    else:
        # A twelve-sided wooden shield fixed to the post: an unmistakable solid practice target.
        outline=[(round(72*math.cos(i*math.tau/12),3),round(176+72*math.sin(i*math.tau/12),3))
                 for i in range(12)]
        for i,(x,z) in enumerate(outline):
            xx,zz=outline[(i+1)%len(outline)]
            author.panel(panels,[(x,-24,z),(x,-4,z),(xx,-4,zz),(xx,-24,zz)],palette['wood'])
        width,height=author.sizes[palette['wood']]
        author.panel(panels,[(x,-24,z) for x,z in outline],palette['wood'],
                     [(x/width,(z-104)/height) for x,z in outline])
        author.panel(panels,[(x,-4,z) for x,z in reversed(outline)],palette['wood'])
        boss=[(round(20*math.cos(i*math.tau/8),3),round(176+20*math.sin(i*math.tau/8),3))
              for i in range(8)]
        for i,(x,z) in enumerate(boss):
            xx,zz=boss[(i+1)%len(boss)]
            author.panel(panels,[(x,-25,z),(xx,-25,zz),(0,-40,176)],palette['metal'])
        # Two horizontal back cleats join the shield to its vertical support.
        for z in [128,208]:
            author.box(panels,[-52,-4,z,52,8,z+8],palette['wood'])
    author.model(prop['id'],panels,prop)
    author.semantic['props'].append(prop)
