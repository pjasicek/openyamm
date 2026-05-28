#include "editor/document/IndoorGeometryMetadata.h"
#include "editor/import/IndoorSourceGeometryCompiler.h"
#include "game/indoor/IndoorMapData.h"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <optional>
#include <sstream>
#include <string>
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
}

int main(int argc, char **argv)
{
    if (argc != 4)
    {
        std::cerr << "usage: mm9_compile_indoor_source <source.glb> <geometry.yml> <output.blv>\n";
        return 2;
    }

    const std::filesystem::path sourcePath = argv[1];
    const std::filesystem::path metadataPath = argv[2];
    const std::filesystem::path outputPath = argv[3];

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

    std::cout << "wrote " << outputPath << " (" << bytes->size() << " bytes), sectors="
              << compileResult.indoorGeometry.sectors.size()
              << " vertices=" << compileResult.indoorGeometry.vertices.size()
              << " faces=" << compileResult.indoorGeometry.faces.size()
              << " warnings=" << compileResult.warnings.size() << "\n";
    for (const std::string &warning : compileResult.warnings)
    {
        std::cout << "warning: " << warning << "\n";
    }

    return 0;
}
