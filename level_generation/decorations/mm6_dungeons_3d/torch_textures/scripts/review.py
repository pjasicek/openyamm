"""The torch batch's review renders (../../torches/scripts/review.py: flat light-one front, lit views, every LOD) with
this folder's materials and output in torch_textures/review/<prop>/.
Usage: blender --background --python review.py -- <prop> <export.glb>"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ttex  # noqa: E402

ttex.tlib.HERE = ttex.HERE
source = os.path.join(ttex.HERE, '..', 'torches', 'scripts', 'review.py')
exec(compile(open(source).read(), source, 'exec'), {'__file__': source, '__name__': '__main__'})
