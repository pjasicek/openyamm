#include "tools/Mm9RudeTranscode.h"

#include <filesystem>
#include <iostream>
#include <string>

namespace
{
void printUsage()
{
    std::cerr
        << "usage: mm9_dialogue_pipeline [--check] "
        << "<mm9-extracted-root> <mm9-maps-directory> <output-world-root>\n";
}
}

int main(int argc, char **argv)
{
    bool checkOnly = false;
    int firstPathArgument = 1;
    if (argc > 1 && std::string(argv[1]) == "--check")
    {
        checkOnly = true;
        firstPathArgument = 2;
    }

    if (argc - firstPathArgument != 3)
    {
        printUsage();
        return 2;
    }

    const std::filesystem::path extractedRoot = argv[firstPathArgument];
    const std::filesystem::path mapsDirectory = argv[firstPathArgument + 1];
    const std::filesystem::path outputRoot = argv[firstPathArgument + 2];

    const OpenYAMM::Game::Mm9DialoguePipelineResult generateResult =
        OpenYAMM::Game::generateMm9DialoguePipelineFiles(extractedRoot, mapsDirectory);
    for (const OpenYAMM::Game::Mm9RudeParseError &error : generateResult.errors)
    {
        std::cerr << "error: " << error.sourcePath;
        if (error.rowNumber != 0)
        {
            std::cerr << ':' << error.rowNumber;
        }
        std::cerr << ": " << error.message << '\n';
    }

    if (!generateResult.errors.empty())
    {
        return 1;
    }

    const OpenYAMM::Game::Mm9DialoguePipelineWriteResult writeResult =
        OpenYAMM::Game::writeMm9DialoguePipelineFiles(outputRoot, generateResult.files, checkOnly);
    for (const OpenYAMM::Game::Mm9RudeParseError &error : writeResult.errors)
    {
        std::cerr << "error: " << error.sourcePath << ": " << error.message << '\n';
    }

    std::cout << (checkOnly ? "checked " : "generated ") << generateResult.files.size()
              << " files, written=" << writeResult.writtenFileCount
              << " unchanged=" << writeResult.unchangedFileCount
              << " stale=" << writeResult.staleFileCount << '\n';

    return writeResult.errors.empty() ? 0 : 1;
}
