"""Original open stone portico with four supported columns and a flat layered entablature."""
import math


def author_shrine(author,prop,palette):
    panels = []
    for foot in prop['foundation']['columns']:
        x,y = foot['center']
        bottom = foot['bottomZ']-prop['padHeight']
        author.box(panels,[x-72,y-72,bottom,x+72,y+72,24],palette['stone'])
        author.box(panels,[x-80,y-80,24,x+80,y+80,40],palette['rim'])
        def ring(radius,z):
            return [(x+round(radius*math.cos(i*math.tau/12)),
                     y+round(radius*math.sin(i*math.tau/12)),z) for i in range(12)]
        for radius0,z0,radius1,z1,key in [(64,40,64,56,'rim'),(64,56,48,72,'rim'),
                                        (48,72,48,568,'column'),(48,568,64,584,'rim'),
                                        (64,584,64,600,'rim')]:
            a,b = ring(radius0,z0),ring(radius1,z1)
            for i in range(12):
                j = (i+1)%12
                author.panel(panels,[a[i],a[j],b[j],b[i]],palette[key])
        author.box(panels,[x-80,y-80,600,x+80,y+80,624],palette['rim'])
    author.box(panels,[-288,-224,624,288,224,656],palette['stone'])
    author.box(panels,[-304,-240,656,304,240,680],palette['rim'])
    author.box(panels,[-288,-224,680,288,224,696],palette['stone'])
    author.model(prop['id'],panels,prop,{'semantic_id':prop['semanticId'],'label':prop['title'],
                                      'id':prop['eventId'],'behavior':prop['behavior']})
    author.semantic['props'].append(prop)
