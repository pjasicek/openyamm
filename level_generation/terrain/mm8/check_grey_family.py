"""Screen shared grey-family art in compatible joins and assembled island/hole layouts."""
import json
from PIL import ImageDraw
from common import *
from check_land import checks
from inventory import GROUPS

F = P / 'transitions/grey_family_v1'
baseline = json.loads((P/'reports/land_validation.json').read_text())
build = json.loads((F/'build.json').read_text())
images, files = {}, {}
for relative, expected in baseline['files'].items():
    path=P/relative
    assert sha(path)==expected,path
    name=GROUPS[path.stem][0] if path.parent==M/'runtime' else path.stem
    images[name],files[name]=read(path),path
for r in build['tiles']:
    name=r['name'];path=F/'runtime'/(name+'.png')
    assert sha(path)==r['runtime_sha256'],name
    images[name],files[name]=read(path),path
results=[]
for r in baseline['checks']:
    a,b,side=r['a'],r['b'],r['side']
    metrics,_,_=checks.metrics(images[a],images[b],side)
    results.append(dict(a=a,b=b,side=side,**metrics))
layouts={
    'island':[['gsnw','gsn','gsne'],['gsw','gstyl','gse'],['gssw','gss','gsse']],
    'hole':[['gsxse','gss','gsxsw'],['gse','gdtyl','gsw'],['gsxne','gsn','gsxnw']]}
for label,grid in layouts.items():
    sheet=Image.new('RGB',(1536,800),'#202933');draw=ImageDraw.Draw(sheet)
    for i in range(2):
        draw.text((i*768+4,8),label+' '+['native','restored candidate'][i],fill='white')
        for y,row in enumerate(grid):
            for x,name in enumerate(row):
                tile=Image.open(P/'references'/(name+'.png')).convert('RGB').resize((256,256)) if i==0 else Image.fromarray(seams.byte(images[name]))
                sheet.paste(tile,(i*768+x*256,32+y*256))
    sheet.save(F/(label+'.png'))
report=dict(scope='All screened compatible opaque land joins with thirteen grey-family substitutions',
            compatible_checks=len(results),failures=[r for r in results if not r['passed']],checks=results,
            files={str(path.relative_to(P)):sha(path) for path in files.values()},
            build_sha256=sha(F/'build.json'),layouts=layouts,visual_acceptance=False)
(F/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(len(results),'joins;',len(report['failures']),'failures')
print([(r['a'],r['side'],r['b']) for r in report['failures'][:20]])
