import json,sys
# print descriptions of properties matching a path fragment
f,pat=sys.argv[1],sys.argv[2]
d=json.load(open(f))
def walk(n,path):
    if isinstance(n,dict):
        if 'description' in n and pat in path: print(path,':',n['description'][:1500]); print()
        for k,v in n.items(): walk(v,path+'/'+k)
    elif isinstance(n,list):
        for i,v in enumerate(n): walk(v,path+'[%d]'%i)
walk(d,'')
