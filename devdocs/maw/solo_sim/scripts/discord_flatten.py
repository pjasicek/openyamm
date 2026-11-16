import json, sys, collections
src, out = sys.argv[1], sys.argv[2]
d = json.load(open(src, encoding='utf-8'))
msgs = d['messages']
by_id = {m['id']: m for m in msgs}
authors = collections.Counter()
months = collections.Counter()
with open(out, 'w', encoding='utf-8') as f:
    for m in msgs:
        a = m['author'].get('nickname') or m['author']['name']
        roles = ','.join(r['name'] for r in m['author'].get('roles', []))
        authors[(a, roles)] += 1
        months[m['timestamp'][:7]] += 1
        c = (m.get('content') or '').replace('\n', ' / ')
        ref = m.get('reference') or {}
        rp = ''
        if ref.get('messageId') in by_id:
            r = by_id[ref['messageId']]
            rp = ' [re ' + (r['author'].get('nickname') or r['author']['name']) + ': ' + (r.get('content') or '')[:80].replace('\n', ' ') + ']'
        att = ' [+%d att]' % len(m['attachments']) if m.get('attachments') else ''
        f.write(f"{m['timestamp'][:16]} {a}:{rp} {c}{att}\n")
print(len(msgs), 'messages')
for (a, r), n in authors.most_common(25): print(n, a, r)
for k in sorted(months): print(k, months[k])
