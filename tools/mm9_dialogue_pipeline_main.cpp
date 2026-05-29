#include "tools/Mm9RudeTranscode.h"

#include <filesystem>
#include <iostream>
#include <string>

namespace
{
void printUsage()
{
    std::cerr
        << "usage: mm9_dialogue_pipeline [--check] [--debug-progress] "
        << "<mm9-extracted-root> <mm9-maps-directory> <output-world-root>\n";
}
}

int main(int argc, char **argv)
{
    bool checkOnly = false;
    bool debugProgress = false;
    int firstPathArgument = 1;
    while (firstPathArgument < argc)
    {
        const std::string argument = argv[firstPathArgument];
        if (argument == "--check")
        {
            checkOnly = true;
            ++firstPathArgument;
            continue;
        }
        if (argument == "--debug-progress")
        {
            debugProgress = true;
            ++firstPathArgument;
            continue;
        }
        if (argument.rfind("--", 0) == 0)
        {
            printUsage();
            return 2;
        }
        break;
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
        OpenYAMM::Game::generateMm9DialoguePipelineFiles(
            extractedRoot,
            mapsDirectory,
            debugProgress ? &std::cerr : nullptr);
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
        OpenYAMM::Game::writeMm9DialoguePipelineFiles(
            outputRoot,
            generateResult.files,
            checkOnly,
            debugProgress ? &std::cerr : nullptr);
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
