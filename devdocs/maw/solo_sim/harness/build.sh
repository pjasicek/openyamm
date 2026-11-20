#!/bin/bash
# Builds solo_harness from SoloHarness.cpp and SoloRoute.cpp against the unit-test build: compiled with the unit
# tests' flags, linked with all their objects (doctest's main included) and the game and engine libraries. The binary
# and objects go to the work directory. Build the unit tests first:
#   cmake --build build --target openyamm_unit_tests -j25
set -e
H="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$H/../../../.." && pwd)"
S="${SOLO_SIM_DIR:-$REPO/output/maw_solo_sim}"
mkdir -p "$S"
cd "$REPO/build/tests"
INC=$(grep CXX_INCLUDES CMakeFiles/openyamm_unit_tests.dir/flags.make | sed 's/CXX_INCLUDES = //')
DEF=$(grep CXX_DEFINES CMakeFiles/openyamm_unit_tests.dir/flags.make | sed 's/CXX_DEFINES = //')
eval c++ -O2 -std=c++20 $DEF $INC -c "$H/SoloHarness.cpp" -o "$S/SoloHarness.o"
eval c++ -O2 -std=c++20 $DEF $INC -c "$H/SoloRoute.cpp" -o "$S/SoloRoute.o"
L=CMakeFiles/openyamm_unit_tests.dir/link.txt
OBJS=$(tr ' ' '\n' < $L | grep '\.o"\?$' | tr -d '"')
LIBS=$(tr ' ' '\n' < $L | grep -v '\.o"\?$' | grep -E '^\.\./|^/usr/lib|^-l' | tr '\n' ' ')
c++ -O2 -pthread -o "$S/solo_harness" "$S/SoloHarness.o" "$S/SoloRoute.o" $OBJS ../game/libopenyamm_game.a \
    ../engine/libopenyamm_engine.a $LIBS
echo "built $S/solo_harness"
