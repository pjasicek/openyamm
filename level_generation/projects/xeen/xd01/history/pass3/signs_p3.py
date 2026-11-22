#!/usr/bin/env python3
"""Pass 3, step 3: every sign, notice and readable panel opens a message window on a click (the `message` effect), as
the shipped maps' signs do (evt.SetMessage), instead of a status line; their hover names say what they are."""
import sys, yio
L = sys.argv[1]
wiring = yio.load(f'{L}/wiring.yml')
titles = {'evt:bay_sign': 'Sign', 'evt:feeding_sign': 'Sign', 'evt:heart_sign': 'Sign', 'evt:keep_out_sign': 'Sign',
          'evt:rules': 'Sign', 'evt:pest_notice': 'Notice', 'evt:notice_board': 'Notice board', 'evt:ledger': "Joe's ledgers",
          'evt:shutter': 'Shuttered window'}
n = 0
for e in wiring['events']:
    if e['id'] not in titles: continue
    e['title'] = titles[e['id']]
    text = e.pop('text')
    e['effects'] = [{'message': text}]
    for alt in e.get('else_effects', []):
        if 'text' in alt: alt['message'] = alt.pop('text')
    n += 1
yio.save(f'{L}/wiring.yml', wiring)
print('signs', n)
