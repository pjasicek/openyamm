#!/usr/bin/env python3
"""Side by side of work/lod_check_<a>.json and <b>.json: per LOD tris, rest height (z extent), per clip lowest point (cm) and
stretched faces; flags clips where a LOD's lowest point differs from that file's LOD0 by more than 0.5 cm. Usage: lod_summary.py a b"""
import json, sys
A, B = (json.load(open(f"work/hof{__import__('os').environ['M']}/lod_check_{t}.json")) for t in sys.argv[1:3])
for lv in sorted(A, key=int):
    a, b = A[lv], B[lv]
    h = lambda r: r['rest_max'][2] - r['rest_min'][2]
    print(f"LOD{lv}: tris {a['tris']} -> {b['tris']}, height {h(a):.3f} -> {h(b):.3f} m, stretched max "
          f"{max(c['stretched_faces'] for c in a['clips'].values())} -> {max(c['stretched_faces'] for c in b['clips'].values())}")
    for clip in a['clips']:
        za, zb = a['clips'][clip]['min_z'], b['clips'][clip]['min_z']
        z0a, z0b = A['0']['clips'][clip]['min_z'], B['0']['clips'][clip]['min_z']
        flag = ' <-' if abs(zb - z0b) > 0.005 or abs(za - z0a) > 0.005 else ''
        print(f"   {clip:9s} min {za*100:6.2f} -> {zb*100:6.2f} cm (vs own LOD0 {(za-z0a)*100:+.2f} / {(zb-z0b)*100:+.2f}) "
              f"stretched {a['clips'][clip]['stretched_faces']} -> {b['clips'][clip]['stretched_faces']}{flag}")
