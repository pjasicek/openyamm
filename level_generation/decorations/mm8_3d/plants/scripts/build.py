"""Blender entry: build one model's LOD objects (recipes.py), export work/<id>/export.glb (+ plant.blend) and render
the review views. Usage: blender --background --python build.py -- <id> [--no-render]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plant_lib as pl
import importlib
args = sys.argv[sys.argv.index('--') + 1:]
sid = args[0]
pl.reset()
import recipes
objects = recipes.build(sid)
pl.export(objects, sid)
if '--no-render' not in args:
    pl.review_renders(objects, sid)
