import json,struct,sys
d=open(sys.argv[1],'rb').read()
l=struct.unpack('<I',d[12:16])[0]; j=json.loads(d[20:20+l])
acc=j['accessors']
print('nodes with mesh:')
for i,n in enumerate(j['nodes']):
    if 'mesh' in n:
        m=j['meshes'][n['mesh']]
        print(i,n.get('name'),'mesh',n['mesh'],m.get('name'),'skin',n.get('skin'), n.get('extras'))
        for p in m['primitives']:
            mat=j['materials'][p['material']]
            tris=acc[p['indices']]['count']//3
            print('   ',mat.get('name'),tris,'alpha',mat.get('alphaMode'),'ds',mat.get('doubleSided'),'variants' if 'KHR_materials_variants' in p.get('extensions',{}) else '', list(p['attributes'].keys()))
print('materials',len(j['materials']),[m['name'] for m in j['materials']])
print('images',len(j.get('images',[])))
print('anims',[a['name'] for a in j.get('animations',[])])
print('ext',j.get('extensionsUsed'), j.get('extras'))
print(json.dumps(j['nodes'][0])[:300])
