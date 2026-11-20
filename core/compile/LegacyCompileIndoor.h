#pragma once

namespace OpenYAMM::Compile
{
// The legacy indoor build: mm9_compile_indoor_source <source.glb> <geometry.yml> <output.blv>
// [generated_doors.yml] [generated_face_groups.yml]. The tool and `oymap compile-indoor` both run it.
int runLegacyCompileIndoor(int argc, char **argv);
}
