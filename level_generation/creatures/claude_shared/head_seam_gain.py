"""Measure the colour step across the head/body texture seam (CLAUDE_CREATURE_TEXTURES.md "Head-only retexture").

For every mesh edge between a `head` face and a body face, samples the body base colour on the body face and the
head base colour on the head face, a little inside each face from the edge midpoint, and writes the median linear
colours and a luminance gain (body / head) as JSON. compose_head_set.py applies the gain so the neck seam matches;
a head that shares no edge with the body (a separate shell) gets gain 1.
Run: blender --background <master.blend> --python head_seam_gain.py -- --mesh Peasant --body body.png
       --head head.png --out seam.json"""
import argparse
import json
import sys

import bmesh
import bpy
import numpy as np

args = argparse.ArgumentParser()
args.add_argument('--mesh', required=True)
args.add_argument('--body', required=True)
args.add_argument('--head', required=True)
args.add_argument('--out', required=True)
options = args.parse_args(sys.argv[sys.argv.index('--') + 1:])


def load(path):
    image = bpy.data.images.load(path)
    image.colorspace_settings.name = 'Non-Color'
    width, height = image.size
    pixels = np.array(image.pixels[:], dtype=np.float32).reshape(height, width, 4)[..., :3]
    return np.where(pixels <= 0.04045, pixels / 12.92, ((pixels + 0.055) / 1.055) ** 2.4)


def sample(texture, uv):
    height, width = texture.shape[:2]
    x = int(np.clip(uv.x % 1.0 * width, 0, width - 1))
    y = int(np.clip(uv.y % 1.0 * height, 0, height - 1))
    return texture[y, x]


body, head = load(options.body), load(options.head)
mesh = bpy.data.objects[options.mesh].data
flags = [0] * len(mesh.polygons)
mesh.attributes['head'].data.foreach_get('value', flags)
data = bmesh.new()
data.from_mesh(mesh)
uv_layer = data.loops.layers.uv.active
body_samples, head_samples = [], []
for edge in data.edges:
    faces = edge.link_faces
    if len(faces) != 2 or flags[faces[0].index] == flags[faces[1].index]:
        continue
    for face in faces:
        loops = [loop for loop in face.loops if loop.vert in edge.verts]
        centre = sum((loop[uv_layer].uv for loop in face.loops), loops[0][uv_layer].uv * 0) / len(face.loops)
        middle = (loops[0][uv_layer].uv + loops[1][uv_layer].uv) / 2
        point = middle.lerp(centre, 0.35)
        if flags[face.index]:
            head_samples.append(sample(head, point))
        else:
            body_samples.append(sample(body, point))
data.free()
luma = np.array([0.2126, 0.7152, 0.0722])
if head_samples:
    body_colour, head_colour = np.median(body_samples, 0), np.median(head_samples, 0)
    result = {'edges': len(head_samples), 'body_linear': body_colour.round(5).tolist(),
              'head_linear': head_colour.round(5).tolist(),
              'luminance_gain': float(body_colour @ luma / max(head_colour @ luma, 1e-5))}
else:
    # The head is a separate shell (e.g. a neck running under a mantle): no visible seam to match.
    result = {'edges': 0, 'luminance_gain': 1.0, 'note': 'head shares no edge with the body; gain left at 1'}
open(options.out, 'w').write(json.dumps(result, indent=1) + '\n')
print('SEAM', json.dumps(result))
