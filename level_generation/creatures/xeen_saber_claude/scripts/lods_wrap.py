"""Run tools/build_actor_lods.py inside this project's Blender wrapper (tools/run_creature_blender.sh accepts only
project scripts). Args: -- <source.glb> <destination.glb> --mesh-node <node>"""
import os, sys, runpy
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
runpy.run_path(os.path.join(REPO, 'tools', 'build_actor_lods.py'), run_name='__main__')
