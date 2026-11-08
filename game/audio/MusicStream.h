#pragma once

#include "engine/AudioSystem.h"

#include <condition_variable>
#include <cstdint>
#include <memory>
#include <mutex>
#include <thread>
#include <vector>

namespace OpenYAMM::Game
{
// A looping music track decoded while it plays: a worker thread keeps a two-second buffer ahead of the mixer, so a
// track costs its encoded bytes plus 768 KB instead of its whole decoded length (about 160 MB for seven minutes of
// 48 kHz stereo floats). The samples are the same as decoding the whole file, and each loop starts over exactly.
class MusicStream final : public Engine::AudioStreamSource
{
public:
    // Decodes the encoded track (any audio FFmpeg reads) from its start; loopGapSeconds of silence follow each pass
    // (MM9 plays a song once, waits 10 s and plays it again).
    explicit MusicStream(std::shared_ptr<const std::vector<uint8_t>> pEncodedTrack, float loopGapSeconds = 0.0f);
    ~MusicStream() override;

    MusicStream(const MusicStream &) = delete;
    MusicStream &operator=(const MusicStream &) = delete;

    uint32_t read(float *pSamples, uint32_t frameCount) override;
    bool finished() const override;

private:
    static constexpr uint32_t BufferFrames = 2 * 48000;

    void decodeTrack();
    bool writeFrames(const float *pSamples, uint32_t frameCount);

    std::shared_ptr<const std::vector<uint8_t>> m_pEncodedTrack;
    uint32_t m_loopGapFrames = 0;
    std::vector<float> m_buffer;
    uint64_t m_framesWritten = 0;
    uint64_t m_framesRead = 0;
    bool m_stopRequested = false;
    bool m_failed = false;
    mutable std::mutex m_mutex;
    std::condition_variable m_spaceAvailable;
    std::thread m_worker;
};
}
