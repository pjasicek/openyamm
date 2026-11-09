import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
sys.argv = ['x', '--', args[0]]
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'apply_preview.py')).read())
sys.argv = ['x', '--', args[1], '--textured']
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'views.py')).read())
