"""Builds the page from page/template.html and the work directory's page/data.json:
- <work>/page/maw_solo_classes.html, the body the claude.ai artifact publishes (the host adds the document head);
- <work>/page/deploy/index.html, a full document with <meta charset="utf-8"> for the web server, which sends
  text/html without a charset (without it, browsers read the UTF-8 text as Windows-1252: "·" shows as "Â·")."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
from simdir import S

here = os.path.dirname(os.path.abspath(__file__))
template = open(os.path.join(here, 'template.html'), encoding='utf-8').read()
data = open(os.path.join(S, 'page', 'data.json'), encoding='utf-8').read()
page = template.replace('__DATA__', data)
open(os.path.join(S, 'page', 'maw_solo_classes.html'), 'w', encoding='utf-8').write(page)
i = page.index('<main>')
os.makedirs(os.path.join(S, 'page', 'deploy'), exist_ok=True)
open(os.path.join(S, 'page', 'deploy', 'index.html'), 'w', encoding='utf-8').write(
    '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    + page[:i].rstrip() + '\n</head>\n<body>\n' + page[i:] + '\n</body>\n</html>\n')
print('wrote', os.path.join(S, 'page', 'maw_solo_classes.html'), 'and deploy/index.html')
