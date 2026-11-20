"""Material settings and triangle budgets of every model (finish.py; review.py reads it to cull back faces as the
engine does)."""
FLAME = {'alpha': 'BLEND', 'double': True, 'unlit': True}
HALO = {'alpha': 'BLEND', 'double': True, 'unlit': True}
UNLIT = {'unlit': True}
FOLIAGE = {'alpha': 'MASK', 'cutoff': 0.5, 'double': True}
FINISH = {
    'orb': {'output': 'mm8_deco_air_orb.glb', 'budget': [200, 100, 50], 'materials': {'Halo': HALO}},
    'seaweed': {'output': 'mm8_deco_seaweed.glb', 'budget': [1200, 500, 160], 'materials': {'Frond': FOLIAGE}},
    'coral': {'output': 'mm8_deco_coral.glb', 'budget': [1200, 500, 160],
              'materials': {'Coral': FOLIAGE, 'Tendril': FOLIAGE}},
    'lantern': {'output': 'mm8_deco_lantern.glb', 'budget': [2500, 1000, 400],
                'materials': {'Flame': FLAME, 'Halo': HALO}},
    'chandelier1': {'output': 'mm8_deco_chandelier1.glb', 'budget': [4000, 1600, 700],
                    'materials': {'Flame': FLAME, 'Candle': FLAME, 'CandleFar': FLAME}},
    'chandelier2': {'output': 'mm8_deco_chandelier2.glb', 'budget': [4000, 1600, 700],
                    'materials': {'Candle': FLAME, 'CandleFar': FLAME}},
    'candlestick': {'output': 'mm8_deco_candlestick.glb', 'budget': [6000, 2000, 600],
                    'materials': {'Candle': FLAME, 'CandleFar': FLAME, 'Flame': FLAME}},
    'torch': {'output': 'mm8_deco_standing_torch.glb', 'budget': [1500, 700, 250],
              'materials': {'Flame': FLAME, 'Blaze': FLAME, 'Sparks': FLAME, 'Halo': HALO}},
    'campfire': {'output': 'mm8_deco_campfire.glb', 'budget': [1500, 700, 300],
                 'materials': {'Flame': FLAME, 'Blaze': FLAME, 'Sparks': FLAME, 'Halo': HALO}},
    'buoy': {'output': 'mm8_deco_bell_buoy.glb', 'budget': [4000, 1600, 700], 'materials': {}},
}
