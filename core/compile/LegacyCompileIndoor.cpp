#include "core/compile/LegacyCompileIndoor.h"

#include "core/compile/IndoorGeometryMetadata.h"
#include "core/compile/IndoorSourceGeometryCompiler.h"
#include "game/indoor/IndoorMapData.h"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <optional>
#include <sstream>
#include <string>
#include <string_view>
#include <vector>

namespace
{
bool readTextFile(const std::filesystem::path &path, std::string &text)
{
    std::ifstream stream(path);
    if (!stream)
    {
        return false;
    }

    std::ostringstream buffer;
    buffer << stream.rdbuf();
    text = buffer.str();
    return true;
}

bool writeBinaryFile(const std::filesystem::path &path, const std::vector<uint8_t> &bytes)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream stream(path, std::ios::binary);
    if (!stream)
    {
        return false;
    }

    stream.write(reinterpret_cast<const char *>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
    return stream.good();
}

void writeIntegerSequence(std::ostream &stream, const std::vector<uint16_t> &values)
{
    stream << "[";

    for (size_t index = 0; index < values.size(); ++index)
    {
        if (index != 0)
        {
            stream << ", ";
        }

        stream << values[index];
    }

    stream << "]";
}

void writeIntegerSequence(std::ostream &stream, const std::vector<int16_t> &values)
{
    stream << "[";

    for (size_t index = 0; index < values.size(); ++index)
    {
        if (index != 0)
        {
            stream << ", ";
        }

        stream << values[index];
    }

    stream << "]";
}

bool writeGeneratedDoorsYaml(
    const std::filesystem::path &path,
    const std::vector<OpenYAMM::Game::IndoorSceneDoor> &doors)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream stream(path);

    if (!stream)
    {
        return false;
    }

    if (doors.empty())
    {
        stream << "[]\n";
        return stream.good();
    }

    for (const OpenYAMM::Game::IndoorSceneDoor &sceneDoor : doors)
    {
        const OpenYAMM::Game::MapDeltaDoor &door = sceneDoor.door;
        stream << "- door_index: " << sceneDoor.doorIndex << "\n";
        stream << "  legacy_attributes: " << door.attributes << "\n";
        stream << "  door_id: " << door.doorId << "\n";
        stream << "  time_since_triggered_ms: " << door.timeSinceTriggered << "\n";
        stream << "  direction: [" << door.directionX << ", " << door.directionY << ", " << door.directionZ << "]\n";
        stream << "  move_length: " << door.moveLength << "\n";
        stream << "  open_speed: " << door.openSpeed << "\n";
        stream << "  close_speed: " << door.closeSpeed << "\n";
        stream << "  state: " << door.state << "\n";
        stream << "  vertex_ids: ";
        writeIntegerSequence(stream, door.vertexIds);
        stream << "\n";
        stream << "  face_ids: ";
        writeIntegerSequence(stream, door.faceIds);
        stream << "\n";
        stream << "  sector_ids: ";
        writeIntegerSequence(stream, door.sectorIds);
        stream << "\n";
        stream << "  delta_us: ";
        writeIntegerSequence(stream, door.deltaUs);
        stream << "\n";
        stream << "  delta_vs: ";
        writeIntegerSequence(stream, door.deltaVs);
        stream << "\n";
        stream << "  x_offsets: ";
        writeIntegerSequence(stream, door.xOffsets);
        stream << "\n";
        stream << "  y_offsets: ";
        writeIntegerSequence(stream, door.yOffsets);
        stream << "\n";
        stream << "  z_offsets: ";
        writeIntegerSequence(stream, door.zOffsets);
        stream << "\n";
    }

    return stream.good();
}

bool writeGeneratedFaceGroupsYaml(
    const std::filesystem::path &path,
    const std::vector<OpenYAMM::Editor::IndoorSourceFaceGroup> &faceGroups)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream stream(path);
    if (!stream)
    {
        return false;
    }

    if (faceGroups.empty())
    {
        stream << "[]\n";
        return stream.good();
    }

    constexpr std::string_view InteractionPrefix = "INTERACT_";
    constexpr std::string_view PersistentVariantPrefix = "IPVAR_";
    constexpr std::string_view BarrelLiquidPrefix = "BARRELLIQUID_";
    for (const OpenYAMM::Editor::IndoorSourceFaceGroup &faceGroup : faceGroups)
    {
        stream << "- source_node: \"" << faceGroup.sourceNodeName << "\"\n";
        if (faceGroup.sourceNodeName.starts_with(InteractionPrefix))
        {
            stream << "  source_object_index: "
                   << faceGroup.sourceNodeName.substr(InteractionPrefix.size()) << "\n";
        }
        else if (faceGroup.sourceNodeName.starts_with(PersistentVariantPrefix))
        {
            const std::string suffix = faceGroup.sourceNodeName.substr(PersistentVariantPrefix.size());
            const size_t separator = suffix.rfind('_');
            if (separator != std::string::npos)
            {
                stream << "  source_object_index: " << suffix.substr(0, separator) << "\n";
                stream << "  variant_index: " << suffix.substr(separator + 1) << "\n";
            }
        }
        else if (faceGroup.sourceNodeName.starts_with(BarrelLiquidPrefix))
        {
            stream << "  source_object_index: "
                   << faceGroup.sourceNodeName.substr(BarrelLiquidPrefix.size()) << "\n";
            stream << "  barrel_liquid: true\n";
        }
        stream << "  face_ids: ";
        writeIntegerSequence(stream, faceGroup.faceIds);
        stream << "\n";
    }
    return stream.good();
}
}

namespace OpenYAMM::Compile
{
int runLegacyCompileIndoor(int argc, char **argv)
{
    if (argc < 4 || argc > 6)
    {
        std::cerr << "usage: mm9_compile_indoor_source <source.glb> <geometry.yml> <output.blv> "
                  << "[generated_doors.yml] [generated_face_groups.yml]\n";
        return 2;
    }

    const std::filesystem::path sourcePath = argv[1];
    const std::filesystem::path metadataPath = argv[2];
    const std::filesystem::path outputPath = argv[3];
    const std::optional<std::filesystem::path> generatedDoorsPath =
        argc >= 5
            ? std::optional<std::filesystem::path>(argv[4])
            : std::nullopt;
    const std::optional<std::filesystem::path> generatedFaceGroupsPath =
        argc >= 6
            ? std::optional<std::filesystem::path>(argv[5])
            : std::nullopt;

    std::string metadataText;
    if (!readTextFile(metadataPath, metadataText))
    {
        std::cerr << "could not read geometry metadata: " << metadataPath << "\n";
        return 1;
    }

    std::string errorMessage;
    std::optional<OpenYAMM::Editor::EditorIndoorGeometryMetadata> metadata =
        OpenYAMM::Editor::loadIndoorGeometryMetadataFromText(metadataText, errorMessage);
    if (!metadata)
    {
        std::cerr << "could not parse geometry metadata: " << errorMessage << "\n";
        return 1;
    }

    OpenYAMM::Editor::normalizeIndoorGeometryMetadata(*metadata, outputPath.filename().string());

    OpenYAMM::Editor::IndoorSourceGeometryCompileResult compileResult = {};
    if (!OpenYAMM::Editor::compileIndoorSourceGeometry(sourcePath, *metadata, compileResult, errorMessage))
    {
        std::cerr << "could not compile indoor source geometry: " << errorMessage << "\n";
        return 1;
    }

    OpenYAMM::Game::IndoorMapDataWriter writer = {};
    const std::optional<std::vector<uint8_t>> bytes = writer.buildBytes(compileResult.indoorGeometry);
    if (!bytes)
    {
        std::cerr << "could not serialize indoor geometry\n";
        return 1;
    }

    if (!writeBinaryFile(outputPath, *bytes))
    {
        std::cerr << "could not write indoor geometry: " << outputPath << "\n";
        return 1;
    }

    if (generatedDoorsPath.has_value() && !writeGeneratedDoorsYaml(*generatedDoorsPath, compileResult.generatedDoors))
    {
        std::cerr << "could not write generated indoor doors: " << *generatedDoorsPath << "\n";
        return 1;
    }

    if (generatedFaceGroupsPath.has_value()
        && !writeGeneratedFaceGroupsYaml(*generatedFaceGroupsPath, compileResult.generatedFaceGroups))
    {
        std::cerr << "could not write generated indoor face groups: " << *generatedFaceGroupsPath << "\n";
        return 1;
    }

    std::cout << "wrote " << outputPath << " (" << bytes->size() << " bytes), sectors="
              << compileResult.indoorGeometry.sectors.size()
              << " vertices=" << compileResult.indoorGeometry.vertices.size()
              << " faces=" << compileResult.indoorGeometry.faces.size()
              << " doors=" << compileResult.generatedDoors.size()
              << " warnings=" << compileResult.warnings.size() << "\n";
    for (const std::string &warning : compileResult.warnings)
    {
        std::cout << "warning: " << warning << "\n";
    }

    return 0;
}
}
