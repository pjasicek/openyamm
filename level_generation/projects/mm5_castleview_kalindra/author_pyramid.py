"""Independent small stone pyramid with a recessed, sealed triangular passage."""
from author_camps import beam


def author_pyramid(author,prop,palette):
    panels=[]
    author.box(panels,[-256,-256,prop['foundation']['bottomZ']-prop['padHeight'],256,256,16],palette['stone'])
    corners=[(-240,-240,16),(240,-240,16),(240,240,16),(-240,240,16)]
    apex=(0,0,528)
    for i in [1,2,3]:
        points=[corners[i],corners[(i+1)%4],apex]
        along=lambda p:p[1] if i==1 else -p[0] if i==2 else -p[1]
        author.panel(panels,points,palette['stone'],[((along(p)+240)/256,(p[2]-16)/256) for p in points])
    outer=[corners[0],corners[1],apex]
    opening=[(-144,-225,48),(144,-225,48),(0,-105,304)]
    sealed=[(x,y+64,z) for x,y,z in opening]
    for i in range(3):
        j=(i+1)%3
        # Separate planar triangles preserve the sloping stone face around the actual recess.
        for points in [[outer[i],outer[j],opening[j]],[outer[i],opening[j],opening[i]]]:
            author.panel(panels,points,palette['stone'],[((p[0]+240)/256,(p[2]-16)/256) for p in points])
        author.panel(panels,[opening[i],opening[j],sealed[j],sealed[i]],palette['stone'])
    author.panel(panels,sealed,palette['stone'],[((p[0]+240)/256,(p[2]-16)/256) for p in sealed])
    # Two braces make the sealed state readable without an invented sign or working destination.
    for z,width in [(96,104),(192,48)]:
        y=-161+(z-48)*120/256-5
        beam(author,panels,(-width,y,z),(width,y,z),12,palette['metal'])
    author.model(prop['id'],panels,prop,{'semantic_id':prop['semanticId'],'label':prop['title'],
                                      'id':prop['eventId'],'behavior':prop['behavior']})
    author.semantic['props'].append(prop)
