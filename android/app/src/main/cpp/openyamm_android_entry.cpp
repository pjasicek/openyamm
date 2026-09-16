#include "game/app/OpenYammMain.h"
#include "AndroidShaderPaths.h"

#include <android/log.h>
#include <android/asset_manager_jni.h>
#include <jni.h>
#include <SDL3/SDL_filesystem.h>
#include <SDL3/SDL_hints.h>
#include <SDL3/SDL_iostream.h>
#include <SDL3/SDL_main.h>
#include <SDL3/SDL_system.h>

#include <algorithm>
#include <array>
#include <cstdarg>
#include <cstdint>
#include <exception>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <streambuf>
#include <string>
#include <vector>

namespace
{
constexpr const char *LogTag = "OpenYAMM";
constexpr size_t CopyBufferSize = 1024 * 1024;

struct PackagedAsset
{
    const char *pApkPath;
    const char *pExtractedPath;
};

class AndroidLogBuffer final : public std::streambuf
{
public:
    explicit AndroidLogBuffer(android_LogPriority priority)
        : m_priority(priority)
    {
    }

protected:
    int overflow(int character) override
    {
        if (character == traits_type::eof())
        {
            return traits_type::not_eof(character);
        }

        appendCharacter(static_cast<char>(character));
        return character;
    }

    int sync() override
    {
        flushLine();
        return 0;
    }

private:
    void appendCharacter(char character)
    {
        if (character == '\n')
        {
            flushLine();
            return;
        }

        m_line.push_back(character);

        if (m_line.size() >= 512)
        {
            flushLine();
        }
    }

    void flushLine()
    {
        if (m_line.empty())
        {
            return;
        }

        __android_log_print(m_priority, LogTag, "%s", m_line.c_str());
        m_line.clear();
    }

    android_LogPriority m_priority;
    std::string m_line;
};

constexpr std::array<PackagedAsset, 1> PackagedRuntimeFiles = {{
    {"settings.ini", "settings.ini"}
}};

void openYammLog(const char *pFormat, ...)
{
    va_list args;
    va_start(args, pFormat);
    __android_log_vprint(ANDROID_LOG_INFO, LogTag, pFormat, args);
    va_end(args);
}

std::filesystem::path getAndroidExternalStorageRoot()
{
    const Uint32 storageState = SDL_GetAndroidExternalStorageState();

    if ((storageState & SDL_ANDROID_EXTERNAL_STORAGE_WRITE) == 0)
    {
        throw std::runtime_error("Android external storage is not writable");
    }

    const char *pExternalStoragePath = SDL_GetAndroidExternalStoragePath();

    if (pExternalStoragePath == nullptr || pExternalStoragePath[0] == '\0')
    {
        throw std::runtime_error("SDL_GetAndroidExternalStoragePath returned no path");
    }

    return pExternalStoragePath;
}

bool extractedAssetIsCurrent(SDL_IOStream &sourceStream, const std::filesystem::path &targetPath, Sint64 sourceSize)
{
    if (sourceSize < 0)
    {
        return false;
    }

    std::error_code sizeError;
    const uintmax_t targetSize = std::filesystem::file_size(targetPath, sizeError);

    if (sizeError || targetSize != static_cast<uintmax_t>(sourceSize))
    {
        return false;
    }

    std::ifstream targetStream(targetPath, std::ios::binary);
    std::array<char, 4096> sourceBytes;
    std::array<char, 4096> targetBytes;
    uintmax_t remainingBytes = targetSize;

    while (remainingBytes > 0)
    {
        const size_t chunkSize = std::min<uintmax_t>(remainingBytes, sourceBytes.size());
        if (SDL_ReadIO(&sourceStream, sourceBytes.data(), chunkSize) != chunkSize)
        {
            return false;
        }
        targetStream.read(targetBytes.data(), chunkSize);
        if (!targetStream || !std::equal(sourceBytes.begin(), sourceBytes.begin() + chunkSize, targetBytes.begin()))
        {
            return false;
        }
        remainingBytes -= chunkSize;
    }

    return true;
}

void copyPackagedAssetToFile(SDL_IOStream &sourceStream, const std::filesystem::path &targetPath, Sint64 sourceSize)
{
    std::filesystem::create_directories(targetPath.parent_path());

    const std::filesystem::path temporaryPath = targetPath.string() + ".tmp";
    std::ofstream outputStream(temporaryPath, std::ios::binary | std::ios::trunc);

    if (!outputStream)
    {
        throw std::runtime_error("Failed to create " + temporaryPath.string());
    }

    std::vector<uint8_t> buffer(CopyBufferSize);
    uint64_t copiedBytes = 0;

    while (true)
    {
        const size_t readBytes = SDL_ReadIO(&sourceStream, buffer.data(), buffer.size());

        if (readBytes == 0)
        {
            const SDL_IOStatus status = SDL_GetIOStatus(&sourceStream);

            if (status == SDL_IO_STATUS_EOF)
            {
                break;
            }

            throw std::runtime_error(std::string("Failed to read APK asset: ") + SDL_GetError());
        }

        outputStream.write(reinterpret_cast<const char *>(buffer.data()), static_cast<std::streamsize>(readBytes));

        if (!outputStream)
        {
            throw std::runtime_error("Failed to write " + temporaryPath.string());
        }

        copiedBytes += readBytes;
    }

    outputStream.close();

    if (!outputStream)
    {
        throw std::runtime_error("Failed to finish writing " + temporaryPath.string());
    }

    if (sourceSize >= 0 && copiedBytes != static_cast<uint64_t>(sourceSize))
    {
        throw std::runtime_error(
            "Short copy for " + targetPath.string() + ": copied " + std::to_string(copiedBytes)
            + " of " + std::to_string(sourceSize));
    }

    std::error_code removeError;
    std::filesystem::remove(targetPath, removeError);

    std::error_code renameError;
    std::filesystem::rename(temporaryPath, targetPath, renameError);

    if (renameError)
    {
        throw std::runtime_error("Failed to install " + targetPath.string() + ": " + renameError.message());
    }
}

// SDL_IOFromFile tries Android internal storage before the APK for relative paths. Older extracted
// shaders can therefore shadow their replacements even after an APK update. Read the APK explicitly.
std::vector<uint8_t> readApkAsset(const char *pPath)
{
    JNIEnv *pEnvironment = static_cast<JNIEnv *>(SDL_GetAndroidJNIEnv());
    jobject activity = static_cast<jobject>(SDL_GetAndroidActivity());
    if (pEnvironment == nullptr || activity == nullptr)
    {
        throw std::runtime_error("Android activity unavailable while opening APK assets");
    }
    jclass activityClass = pEnvironment->GetObjectClass(activity);
    jmethodID getAssets = pEnvironment->GetMethodID(activityClass, "getAssets", "()Landroid/content/res/AssetManager;");
    jobject assetManager = pEnvironment->CallObjectMethod(activity, getAssets);
    AAssetManager *pManager = AAssetManager_fromJava(pEnvironment, assetManager);
    AAsset *pAsset = pManager != nullptr ? AAssetManager_open(pManager, pPath, AASSET_MODE_BUFFER) : nullptr;
    pEnvironment->DeleteLocalRef(assetManager);
    pEnvironment->DeleteLocalRef(activityClass);
    pEnvironment->DeleteLocalRef(activity);
    if (pAsset == nullptr)
    {
        throw std::runtime_error(std::string("Missing APK asset: ") + pPath);
    }
    const off64_t length = AAsset_getLength64(pAsset);
    // Only shaders and the small initial settings file are extracted through this path.
    if (length <= 0 || length > 16 * 1024 * 1024)
    {
        AAsset_close(pAsset);
        throw std::runtime_error(std::string("Invalid APK runtime asset length: ") + pPath);
    }
    std::vector<uint8_t> bytes(size_t(length), uint8_t(0));
    size_t offset = 0;
    while (offset < bytes.size())
    {
        const int count = AAsset_read(pAsset, bytes.data() + offset, bytes.size() - offset);
        if (count <= 0)
        {
            AAsset_close(pAsset);
            throw std::runtime_error(std::string("Short APK runtime asset read: ") + pPath);
        }
        offset += size_t(count);
    }
    AAsset_close(pAsset);
    return bytes;
}

void extractPackagedAssetIfNeeded(const std::filesystem::path &storageRoot, const PackagedAsset &asset)
{
    const std::vector<uint8_t> sourceBytes = readApkAsset(asset.pApkPath);
    SDL_IOStream *pSourceStream = SDL_IOFromConstMem(sourceBytes.data(), sourceBytes.size());

    if (pSourceStream == nullptr)
    {
        throw std::runtime_error(std::string("Failed to open APK asset ") + asset.pApkPath + ": " + SDL_GetError());
    }

    const Sint64 sourceSize = SDL_GetIOSize(pSourceStream);
    const std::filesystem::path targetPath = storageRoot / asset.pExtractedPath;

    if (extractedAssetIsCurrent(*pSourceStream, targetPath, sourceSize))
    {
        SDL_CloseIO(pSourceStream);
        openYammLog("Asset current: %s", targetPath.string().c_str());
        return;
    }

    if (SDL_SeekIO(pSourceStream, 0, SDL_IO_SEEK_SET) < 0)
    {
        SDL_CloseIO(pSourceStream);
        throw std::runtime_error(std::string("Failed to rewind APK asset: ") + asset.pApkPath);
    }

    openYammLog(
        "Extracting %s to %s (%lld bytes)",
        asset.pApkPath,
        targetPath.string().c_str(),
        static_cast<long long>(sourceSize));

    try
    {
        copyPackagedAssetToFile(*pSourceStream, targetPath, sourceSize);
    }
    catch (...)
    {
        SDL_CloseIO(pSourceStream);

        std::error_code removeError;
        std::filesystem::remove(targetPath.string() + ".tmp", removeError);
        throw;
    }

    SDL_CloseIO(pSourceStream);
    openYammLog("Extracted %s", targetPath.string().c_str());
}

void extractPackagedAssetIfMissing(const std::filesystem::path &storageRoot, const PackagedAsset &asset)
{
    const std::filesystem::path targetPath = storageRoot / asset.pExtractedPath;

    if (std::filesystem::is_regular_file(targetPath))
    {
        openYammLog("Preserving writable runtime file: %s", targetPath.string().c_str());
        return;
    }

    extractPackagedAssetIfNeeded(storageRoot, asset);
}

void prepareAndroidAssetRoot()
{
    const std::filesystem::path storageRoot = getAndroidExternalStorageRoot();

    for (const char *pShaderPath : OpenYAMM::Game::AndroidShaderPaths)
    {
        extractPackagedAssetIfNeeded(storageRoot, {pShaderPath, pShaderPath});
    }

    for (const PackagedAsset &runtimeFile : PackagedRuntimeFiles)
    {
        extractPackagedAssetIfMissing(storageRoot, runtimeFile);
    }

    std::filesystem::current_path(storageRoot);
    openYammLog("Android working directory: %s", storageRoot.string().c_str());
    openYammLog("Android asset root: installed APK assets");
}

void installAndroidLogStreams()
{
    static AndroidLogBuffer outputBuffer(ANDROID_LOG_INFO);
    static AndroidLogBuffer errorBuffer(ANDROID_LOG_ERROR);

    std::cout.rdbuf(&outputBuffer);
    std::cerr.rdbuf(&errorBuffer);
}
}

int main(int argc, char **argv)
{
    try
    {
        installAndroidLogStreams();
        if (!SDL_SetHintWithPriority(SDL_HINT_TOUCH_MOUSE_EVENTS, "0", SDL_HINT_OVERRIDE))
        {
            throw std::runtime_error("Failed to disable SDL touch-generated mouse events");
        }
        openYammLog("Starting shared OpenYAMM game entry argc=%d", argc);
        prepareAndroidAssetRoot();
        const int result = OpenYAMM::Game::runApplication(argc, argv);
        openYammLog("Shared OpenYAMM game entry returned %d", result);
        return result;
    }
    catch (const std::exception &exception)
    {
        openYammLog("Fatal error: %s", exception.what());
        return 1;
    }
    catch (...)
    {
        openYammLog("Fatal unknown error");
        return 1;
    }
}
