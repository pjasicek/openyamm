#!/bin/bash
# strips of every clip, every tier. Project folder.
for t in a b c; do python3 scripts/strips.py nb_$t review/strips_$t.png 6 --fresh; done
echo DONE1
