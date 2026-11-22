"""Run a repository Blender tool (e.g. tools/build_actor_lods.py) under the creature wrapper, which only launches
project scripts. Args: -- <tool path relative to the repository> [tool arguments...]"""
import sys, os, runpy
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
a = sys.argv[sys.argv.index('--') + 1:]
tool = os.path.join(REPO, a[0])
sys.argv = [tool, '--'] + a[1:]
os.chdir(REPO)
runpy.run_path(tool, run_name='__main__')
