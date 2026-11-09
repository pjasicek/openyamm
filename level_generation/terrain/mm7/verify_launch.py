"""Smoke-check the user's launcher with its real startup save and terrain settings."""
import json,subprocess,time,configparser
from common import *
def main():
 log=P/'reports/launcher.log'
 with log.open('w') as stream:
  process=subprocess.Popen([str(P/'play.sh'),'enhanced'],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
  try:
   time.sleep(10)
   assert process.poll() is None,'Launcher exited before review'
   subprocess.run(['import','-window','root',str(P/'reports/launcher.png')],check=True)
  finally:
   process.terminate()
   try:process.wait(timeout=5)
   except subprocess.TimeoutExpired:process.kill();process.wait()
 config=configparser.ConfigParser();config.read('/tmp/openyamm-mm7-terrain-review/enhanced/settings.ini')
 assert config['video_quality']['terrain']=='x2' and Path(config['startup']['save_file']).is_file()
 (P/'reports/launcher.json').write_text(json.dumps(dict(command='./level_generation/terrain/mm7/play.sh enhanced',terrain_quality='x2',start_save=config['startup']['save_file'],screenshot_sha256=sha(P/'reports/launcher.png'),binary_sha256=sha(Path('/tmp/openyamm-mm7-terrain-review/openyamm'))),indent=2)+'\n')
 print('Launcher remained running with x2 terrain and the supplied MM7 start save')
if __name__=='__main__':main()
