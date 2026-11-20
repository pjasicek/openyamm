from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
runpy.run_path(str(p/'author_clips.py'),run_name='__main__')
runpy.run_path(str(p/'cloth.py'),run_name='__main__')
runpy.run_path(str(p/'review_authored.py'),run_name='__main__')
