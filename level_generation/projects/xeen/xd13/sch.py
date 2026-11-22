import json,sys
d=json.load(open(sys.argv[1]))
path=sys.argv[2:] 
node=d
for p in path:
    node=node['properties'][p] if 'properties' in node else node
    if node.get('type')=='array': node=node['items']
def short(s,n=160): return (s or '').replace('\n',' ')[:n]
props=node.get('properties',{})
for k,v in props.items():
    t=v.get('type') or ('enum' if 'enum' in v else ('ref' if '$ref' in v else ''))
    extra=(' enum='+str(v['enum'])) if 'enum' in v else ''
    print(f"{k} [{t}]{extra}: {short(v.get('description'))}")
