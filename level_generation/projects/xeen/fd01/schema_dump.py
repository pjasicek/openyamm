#!/usr/bin/env python3
"""schema_dump.py <schema.json> <top key> [maxlen]: prints the property paths under a top-level key with descriptions."""
import json, sys
s = json.load(open(sys.argv[1]))
top = sys.argv[2]
ml = int(sys.argv[3]) if len(sys.argv) > 3 else 220
defs = s.get('$defs', {})

def res(n):
    r = n.get('$ref')
    if r and r.startswith('#/$defs/'):
        return defs[r[8:]]
    return n

def walk(n, path, depth):
    n = res(n)
    if depth > 6:
        return
    if 'items' in n:
        walk(n['items'], path + '[]', depth + 1); return
    for k in ('oneOf', 'anyOf'):
        for i, sub in enumerate(n.get(k, [])):
            walk(sub, path + f'<{k}{i}>', depth + 1)
    for k, v in n.get('properties', {}).items():
        v2 = res(v)
        d = (v.get('description') or v2.get('description') or '').replace('\n', ' ')
        t = v2.get('type', v2.get('enum', v.get('$ref', '')))
        print(f'{path}.{k} [{t}] {d[:ml]}')
        walk(v2, path + '.' + k, depth + 1)

walk(s['properties'][top], top, 0)
