import os,runpy,sys,traceback
script=sys.argv[sys.argv.index('--')+1]
try:runpy.run_path(script,run_name='__main__')
except SystemExit as e:code=int(e.code or 0)
except BaseException:traceback.print_exc();code=1
else:code=0
sys.stdout.flush();sys.stderr.flush();os._exit(code)
