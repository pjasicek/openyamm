"""finish.py table for the batch-B corpses (build_corpses_b.py): one-off budgets, four LODs."""
BUDGET = [6000, 3000, 1300, 300]
TABLE = {
    'corpse01': {'output': 'mm6_deco_corpse01.glb', 'budget': BUDGET, 'materials': {}},
    'corpse02': {'output': 'mm6_deco_corpse02.glb', 'budget': BUDGET, 'materials': {}},
    'corpse03': {'output': 'mm6_deco_corpse03.glb', 'budget': BUDGET, 'materials': {}},
    'corpse09': {'output': 'mm6_deco_corpse09.glb', 'budget': BUDGET, 'materials': {}},
    # the hair curtain is a single alpha-tested sheet seen from both sides
    'corpse10': {'output': 'mm6_deco_corpse10.glb', 'budget': BUDGET,
                 'materials': {'Hair': {'alpha': 'MASK', 'cutoff': 0.5, 'double': True}}},
}
