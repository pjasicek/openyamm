import re, textwrap
p1=open('bm_part1.md').read(); p2=open('bm_part2.md').read(); p3a=open('bm_part3a.md').read(); p3b=open('bm_part3b.md').read()
doc=p1+p2+open('golden_detail.txt').read()+p3a+p3b
if not doc.endswith('\n'): doc+='\n'
def cells(line): return [c.strip() for c in line.strip().strip('|').split('|')]
def wrap(prefix, text):
    return textwrap.fill(text, width=118, initial_indent=prefix, subsequent_indent='  ', break_long_words=False, break_on_hyphens=False)
def convert(doc, header_start, fmt):
    i=doc.index(header_start)
    j=doc.find('\n\n', i)
    if j<0: j=len(doc.rstrip('\n'))
    block=doc[i:j].split('\n')
    rows=[cells(l) for l in block[2:] if l.strip()]
    out='\n'.join(wrap('- ', fmt(r)) for r in rows)
    return doc[:i]+out+doc[j:]
doc=convert(doc, '| Name | Value | Where |', lambda r: f"{r[0]}: {r[1]} ({r[2]})")
doc=convert(doc, '| Where | Says | Code does |', lambda r: f"**{r[0]}.** Says: {r[1]}. Code: {r[2]}.")
doc=convert(doc, '| Lines | Contents |', lambda r: f"{r[0]}: {r[1]}")
if not doc.endswith('\n'): doc+='\n'
open('/home/pjasicek/github/OpenYAMM/devdocs/maw/BALANCE_MODEL.md','w').write(doc)
long=[(n+1,len(l)) for n,l in enumerate(doc.split('\n')) if len(l)>120]
print(len(doc.split('\n')), long[:40])
