# Source me: PY = gltf venv with system yaml on the path; run from the project folder.
export REPO=/home/pjasicek/github/OpenYAMM
export P=$REPO/level_generation/creatures/mm9_lizardorc_claude
export S=$REPO/level_generation/creatures/claude_shared
export G=$S/gltf_venv/bin/python
export PYTHONPATH=$(python3 -c "import yaml,os;print(os.path.dirname(os.path.dirname(yaml.__file__)))")
export TOKEN=da36bd8415a348a380345bd05452be21
