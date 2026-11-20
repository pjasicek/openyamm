"""Build a local comparison gallery for the exact complete MM8 terrain export."""
import html
import json

from common import P, sha
from inventory import family


def main():
    manifest_path = P / 'complete_runtime_x2/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    banks = {r['name']: r['binding']['liquid'] for r in
             json.loads((P / 'liquids/banks_v2/build.json').read_text())['tiles']}
    prefixes = dict(water='hdwtr', lava='hdlav', tar='hwoil')
    cards = []
    for filename, record in sorted(manifest['files'].items()):
        name = filename[:-4]
        original = 'references/' + filename
        enhanced = 'complete_runtime_x2/worlds/mm8/terrain_x2/' + filename
        assert (P / original).is_file(), original
        assert sha(P / enhanced) == record['sha256'], enhanced
        group = family(name)
        background = ''
        if name in banks:
            background = ' style="background-image:url(%s%s000.png)"' % (
                'complete_runtime_x2/worlds/mm8/terrain_x2/', prefixes[banks[name]])
        cards.append('<article data-family="%s" data-name="%s"><h3>%s</h3><div class="pair">'
                     '<figure><img loading="lazy" src="%s" alt="Original %s"><figcaption>Original</figcaption></figure>'
                     '<figure><img loading="lazy"%s src="%s" alt="Restored %s"><figcaption>2x</figcaption></figure>'
                     '</div><small>%s · %s</small></article>' %
                     (group, name, name, original, name, background, enhanced, name,
                      group.replace('_', ' '), html.escape(record['source'])))
    options = ''.join('<option value="%s">%s</option>' % (g, g.replace('_', ' '))
                      for g in sorted({family(n[:-4]) for n in manifest['files']}))
    cycles = ''.join('<figure><img class="cycle" data-prefix="%s" src="complete_runtime_x2/worlds/mm8/terrain_x2/%s000.png"'
                     ' alt="%s animation"><figcaption>%s · 14 frames</figcaption></figure>' %
                     (prefix, prefix, group, group.title()) for group, prefix in prefixes.items())
    document = '''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>MM8 terrain restoration comparisons</title><style>
body{background:#20252a;color:#eee;font:16px system-ui;margin:24px}a{color:#9ed9ff}
header{max-width:1000px}#tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(540px,1fr));gap:16px}
article{background:#30373e;padding:12px;overflow-wrap:anywhere}article[hidden]{display:none}
.pair,#cycles{display:flex;gap:12px;flex-wrap:wrap}figure{margin:0}img{width:256px;height:256px;background-size:256px}
figcaption{padding:4px 0;color:#ccc}small{color:#bbb}input,select,button{font:inherit;padding:8px;margin:8px 8px 16px 0}
</style><header><h1>MM8 terrain · original / 2x</h1>
<p>239 textures: 197 used static names and 42 animation frames, covering all14 outdoor maps.
Painted colours and native feature scale are preserved. Use the map guide for in-game comparisons.</p>
<p><a href="MAPS.md">Map guide</a> · <a href="HANDOFF.md">Handoff and review evidence</a> ·
<a href="complete_runtime_x2/manifest.json">Exact export/provenance</a> ·
<a href="reports/complete_validation.json">24,428 compatible-join checks</a></p>
<p>Shoreline originals show their native magenta key; restored RGBA overlays are shown over liquid frame0.
Animation previews use the native 15/128-second frame period. Actual in-game animation evidence is linked in the handoff.
Native incompatible map placements remain unchanged.</p></header>
<div id="cycles">CYCLES</div><button id="motion">Pause animation</button><br>
<input id="search" placeholder="Filter texture name"><select id="family"><option value="">All families</option>OPTIONS</select>
<span id="count"></span><main id="tiles">CARDS</main><script>
const cards=[...document.querySelectorAll('article')], search=document.querySelector('#search'), family=document.querySelector('#family');
function filter(){let count=0;for(const card of cards){card.hidden=!(card.dataset.name.includes(search.value.toLowerCase())&&(!family.value||card.dataset.family===family.value));if(!card.hidden)count++;}document.querySelector('#count').textContent=count+' textures';}
search.oninput=family.onchange=filter;filter();let phase=0,paused=false;
document.querySelector('#motion').onclick=()=>{paused=!paused;document.querySelector('#motion').textContent=paused?'Play animation':'Pause animation';};
setInterval(()=>{if(paused)return;phase=(phase+1)%14;for(const im of document.querySelectorAll('.cycle'))im.src='complete_runtime_x2/worlds/mm8/terrain_x2/'+im.dataset.prefix+String(phase).padStart(3,'0')+'.png';},15000/128);
</script>'''.replace('CYCLES', cycles).replace('OPTIONS', options).replace('CARDS', '\n'.join(cards))
    (P / 'review.html').write_text(document)
    print('Wrote comparison gallery:', len(cards), 'tiles and three liquid cycles')


if __name__ == '__main__':
    main()
