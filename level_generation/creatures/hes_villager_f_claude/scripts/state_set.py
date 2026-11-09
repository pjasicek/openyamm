"""Set a key in a creature progress JSON: state_set.py <state.json> <dotted.key> <json value>"""
import json, sys
p, k, v = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
d = json.load(open(p)); cur = d
ks = k.split('.')
for x in ks[:-1]:
    cur = cur.setdefault(x, {})
cur[ks[-1]] = v
json.dump(d, open(p, 'w'), indent=1)
print('STATE', k)
