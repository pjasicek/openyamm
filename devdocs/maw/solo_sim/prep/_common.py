"""Paths for the preparation scripts: the work directory ($SOLO_SIM_DIR, default <repo>/output/maw_solo_sim) and its
inv/ and route/ folders."""
import os

CODE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(CODE, '..', '..', '..', '..'))
S = os.environ.get('SOLO_SIM_DIR') or os.path.join(REPO, 'output', 'maw_solo_sim')
INV = os.path.join(S, 'inv')
ROUTE = os.path.join(S, 'route')
os.makedirs(INV, exist_ok=True)
os.makedirs(ROUTE, exist_ok=True)

# Difficulty keys and the ruleset each one starts.
DIFFS = [('normal', '{id: maw, difficulty: normal, progression: free}'),
         ('maw', '{id: maw, difficulty: maw, progression: free}'),
         ('hard', '{id: maw, difficulty: hard, progression: free}'),
         ('hell', '{id: maw, difficulty: hell, progression: free}'),
         ('nightmare', '{id: maw, difficulty: nightmare, progression: free}'),
         ('doom', '{id: maw, difficulty: nightmare, progression: horizontal, challenge_mode: doom}'),
         ('insanity', '{id: maw, difficulty: nightmare, progression: horizontal, challenge_mode: road_to_insanity}'),
         ('madness', '{id: maw, difficulty: nightmare, progression: horizontal, challenge_mode: beyond_madness}')]
# The same, as the harness's options string (SoloRoute).
ROUTE_OPTIONS = {'normal': 'normal:free', 'maw': 'maw:free', 'hard': 'hard:free', 'hell': 'hell:free',
                 'nightmare': 'nightmare:free', 'doom': 'nightmare:horizontal:doom',
                 'insanity': 'nightmare:horizontal:road_to_insanity',
                 'madness': 'nightmare:horizontal:beyond_madness'}

# The solo run's level stages: a snapshot when the character first reaches each level (1 = the start, before the first
# map). Runs that end below a stage simply do not have it; every run also has its end snapshot.
STAGES = [1, 10, 20, 30, 50, 100, 150, 200, 300, 400, 500, 600, 700, 800]
