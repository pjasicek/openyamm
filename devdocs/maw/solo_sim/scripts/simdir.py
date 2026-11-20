"""The work directory every script reads and writes: $SOLO_SIM_DIR, default <repo>/output/maw_solo_sim (git-ignored).
The scripts themselves live in devdocs/maw/solo_sim/scripts; CODE is that folder."""
import os

CODE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(CODE, '..', '..', '..', '..'))
S = os.environ.get('SOLO_SIM_DIR') or os.path.join(REPO, 'output', 'maw_solo_sim')
