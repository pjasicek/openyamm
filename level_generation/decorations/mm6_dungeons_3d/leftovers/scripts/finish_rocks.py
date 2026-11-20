"""finish.py table of the leftover rocks (build_rock.py -> work/rocks/<prop>_export.glb)."""
ROCK_BUDGET = [2500, 1000, 300, 100]
TABLE = {
    'rock01': {'output': 'mm6_deco_boulder01.glb', 'budget': ROCK_BUDGET, 'export': 'work/rocks/rock01_export.glb'},
    'rock02': {'output': 'mm6_deco_boulder02.glb', 'budget': ROCK_BUDGET, 'export': 'work/rocks/rock02_export.glb'},
    'rock03': {'output': 'mm6_deco_boulder03.glb', 'budget': ROCK_BUDGET, 'export': 'work/rocks/rock03_export.glb'},
    'rock06': {'output': 'mm6_deco_boulder06.glb', 'budget': [1600, 650, 260, 110],
               'export': 'work/rocks/rock06_export.glb'},
    'rock10': {'output': 'mm6_deco_boulder10.glb', 'budget': ROCK_BUDGET, 'export': 'work/rocks/rock10_export.glb'},
    'rock11': {'output': 'mm6_deco_boulder11.glb', 'budget': ROCK_BUDGET, 'export': 'work/rocks/rock11_export.glb'},
    '6rock02': {'output': 'mm6_deco_rock02.glb', 'budget': ROCK_BUDGET, 'export': 'work/rocks/6rock02_export.glb'},
}
