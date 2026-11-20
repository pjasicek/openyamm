#include "game/render/WeatherRenderer.h"

#include "game/render/RuntimeShader.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
// Four vertices per drop with 16-bit indices.
constexpr uint32_t MaxDrops = 16383;
constexpr uint32_t CurtainSegments = 48;
constexpr float TwoPi = 6.28318530717958647692f;
constexpr float TimeWrapSeconds = 3600.0f;
// A teleport or map change must not read as a fast camera move.
constexpr float MaxCameraSpeed = 2500.0f;
constexpr float CameraVelocityFollowSeconds = 0.15f;

// Rain: a box about 25 m across around the party, drops falling ~18 m/s with a short motion streak.
constexpr std::array<float, 3> RainBox = {2600.0f, 2600.0f, 2000.0f};
constexpr float RainBoxLift = 450.0f;
constexpr float RainFallSpeed = 1900.0f;
constexpr float RainWindShare = 0.85f;
constexpr float RainStreakSeconds = 0.045f;
constexpr float RainWidth = 1.1f;
constexpr float RainNearFade = 220.0f;
// A sparser far rain box fills the space between the near box and the curtain, so rain never visibly stops around
// the party. Its drops only fade in beyond the near box.
constexpr std::array<float, 3> FarRainBox = {7000.0f, 7000.0f, 3600.0f};
constexpr float FarRainBoxLift = 900.0f;
constexpr float FarRainNearFade = 1200.0f;
constexpr float FarRainWidth = 1.8f;
// The camera's own motion slants rain streaks and smears snow, but only partly, as the eye tracks them.
constexpr float RainCameraMotionShare = 0.6f;
// Splash crowns: the colour the engine's snow had before flakes became data (WeatherFlakeLook's default).
constexpr std::array<float, 3> SplashColor = {1.2f, 1.22f, 1.26f};

// Snow and ash flakes: a near box drifting with the wind and a sparser far box for depth. Their colour, fall speed,
// sizes, opacities and sway are data (WeatherFlakeLook, weather.yml flakes).
constexpr std::array<float, 3> NearSnowBox = {2600.0f, 2600.0f, 2000.0f};
constexpr float NearSnowBoxLift = 450.0f;
constexpr std::array<float, 3> FarSnowBox = {6000.0f, 6000.0f, 3200.0f};
constexpr float FarSnowBoxLift = 800.0f;
// Flakes are drawn along their motion over this time, so strong wind smears them.
constexpr float SnowStreakSeconds = 0.03f;
constexpr float NearSnowFade = 180.0f;
// The far layer only fills in beyond the near box.
constexpr float FarSnowFade = 1100.0f;

// Distant rain curtain: rings of falling streak sheets around the party.
constexpr std::array<float, 2> CurtainRadii = {2700.0f, 4200.0f};
constexpr float CurtainBottom = -1600.0f;
constexpr float CurtainTop = 2600.0f;
constexpr float CurtainStreakSpacing = 18.0f;
constexpr float CurtainRepeats = 6.0f;

// Splashes: short crowns where drops hit the ground in front of the party.
constexpr float SplashesPerSecond = 1000.0f;
constexpr float SplashLifeSeconds = 0.32f;
constexpr float SplashMinDistance = 140.0f;
// Splashes thin out with distance instead of ending at a visible edge.
constexpr float SplashMaxDistance = 1500.0f;
constexpr float SplashHalfAngle = 1.2f;
constexpr float SplashSize = 12.0f;

struct QualityBudget
{
    uint32_t rain = 0;
    uint32_t farRain = 0;
    uint32_t nearSnow = 0;
    uint32_t farSnow = 0;
    uint32_t curtainRings = 0;
    uint32_t splashes = 0;
};

QualityBudget qualityBudget(WeatherQuality quality)
{
    switch (quality)
    {
        case WeatherQuality::Low:
            return {1800, 1200, 3000, 0, 1, 0};
        case WeatherQuality::Medium:
            return {4500, 2500, 7000, 1800, 2, 180};
        case WeatherQuality::High:
            return {9000, 5000, 12000, 4000, 2, 360};
        case WeatherQuality::Off:
        default:
            return {};
    }
}

struct DropVertex
{
    float seedX;
    float seedY;
    float seedZ;
    float u;
    float v;
    uint32_t random;
};

struct CurtainVertex
{
    float x;
    float y;
    float height;
    float u;
    float v;
    uint32_t color;
};

bgfx::VertexLayout weatherVertexLayout()
{
    bgfx::VertexLayout layout;
    layout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord0, 2, bgfx::AttribType::Float)
        .add(bgfx::Attrib::Color0, 4, bgfx::AttribType::Uint8, true)
        .end();
    return layout;
}

// splitmix64, so every platform builds the same drop field.
uint64_t nextRandom(uint64_t &state)
{
    uint64_t value = (state += 0x9e3779b97f4a7c15ull);
    value = (value ^ (value >> 30)) * 0xbf58476d1ce4e5b9ull;
    value = (value ^ (value >> 27)) * 0x94d049bb133111ebull;
    return value ^ (value >> 31);
}

float unitRandom(uint64_t &state)
{
    return static_cast<float>(nextRandom(state) >> 40) / static_cast<float>(1ull << 24);
}

float wrapPositive(float value, float period)
{
    const float wrapped = std::fmod(value, period);
    return wrapped < 0.0f ? wrapped + period : wrapped;
}
}

bool WeatherRenderer::initialize()
{
    shutdown();
    const bgfx::VertexLayout layout = weatherVertexLayout();
    std::vector<DropVertex> drops;
    drops.reserve(MaxDrops * 4);
    std::vector<uint16_t> dropIndices;
    dropIndices.reserve(MaxDrops * 6);
    uint64_t state = 0x7765617468657221ull;

    // Seeds are independent, so drawing the first N drops thins the whole volume evenly.
    for (uint32_t drop = 0; drop < MaxDrops; ++drop)
    {
        const float seedX = unitRandom(state);
        const float seedY = unitRandom(state);
        const float seedZ = unitRandom(state);
        const uint32_t random = static_cast<uint32_t>(nextRandom(state));
        const uint16_t base = static_cast<uint16_t>(drop * 4);
        drops.push_back({seedX, seedY, seedZ, 0.0f, -1.0f, random});
        drops.push_back({seedX, seedY, seedZ, 1.0f, -1.0f, random});
        drops.push_back({seedX, seedY, seedZ, 1.0f, 1.0f, random});
        drops.push_back({seedX, seedY, seedZ, 0.0f, 1.0f, random});

        for (const uint16_t corner : {0, 1, 2, 0, 2, 3})
        {
            dropIndices.push_back(static_cast<uint16_t>(base + corner));
        }
    }

    std::vector<CurtainVertex> curtain;
    std::vector<uint16_t> curtainIndices;

    for (uint32_t segment = 0; segment <= CurtainSegments; ++segment)
    {
        const float fraction = static_cast<float>(segment) / static_cast<float>(CurtainSegments);
        const float angle = fraction * TwoPi;
        curtain.push_back({std::cos(angle), std::sin(angle), 0.0f, fraction, 0.0f, 0xffffffffu});
        curtain.push_back({std::cos(angle), std::sin(angle), 1.0f, fraction, 1.0f, 0xffffffffu});

        if (segment < CurtainSegments)
        {
            const uint16_t base = static_cast<uint16_t>(segment * 2);

            for (const uint16_t corner : {0, 2, 3, 0, 3, 1})
            {
                curtainIndices.push_back(static_cast<uint16_t>(base + corner));
            }
        }
    }

    m_dropVertices = bgfx::createVertexBuffer(
        bgfx::copy(drops.data(), static_cast<uint32_t>(drops.size() * sizeof(DropVertex))), layout);
    m_dropIndices = bgfx::createIndexBuffer(
        bgfx::copy(dropIndices.data(), static_cast<uint32_t>(dropIndices.size() * sizeof(uint16_t))));
    m_curtainVertices = bgfx::createVertexBuffer(
        bgfx::copy(curtain.data(), static_cast<uint32_t>(curtain.size() * sizeof(CurtainVertex))), layout);
    m_curtainIndices = bgfx::createIndexBuffer(
        bgfx::copy(curtainIndices.data(), static_cast<uint32_t>(curtainIndices.size() * sizeof(uint16_t))));
    m_rainProgram = loadRuntimeProgram("vs_weather", "fs_weather");
    m_snowProgram = loadRuntimeProgram("vs_weather_snow", "fs_weather_snow");
    m_curtainProgram = loadRuntimeProgram("vs_weather_curtain", "fs_weather_curtain");
    m_splashProgram = loadRuntimeProgram("vs_weather_splash", "fs_weather_splash");
    m_weatherUniform = bgfx::createUniform("u_weather", bgfx::UniformType::Vec4, 6);
    m_roofSampler = bgfx::createUniform("s_weatherRoof", bgfx::UniformType::Sampler);
    m_roofUniform = bgfx::createUniform("u_weatherRoof", bgfx::UniformType::Vec4);
    const float noRoof = WeatherRoofMap::NoSurface;
    m_noRoofTexture = bgfx::createTexture2D(1, 1, false, 1, bgfx::TextureFormat::R32F,
        BGFX_SAMPLER_POINT | BGFX_SAMPLER_UVW_CLAMP, bgfx::copy(&noRoof, sizeof(noRoof)));
    m_roofPlacement = {};

    if (!isReady())
    {
        shutdown();
        return false;
    }

    return true;
}

void WeatherRenderer::shutdown()
{
    for (bgfx::ProgramHandle *pProgram : {&m_rainProgram, &m_snowProgram, &m_curtainProgram, &m_splashProgram})
    {
        if (bgfx::isValid(*pProgram))
        {
            bgfx::destroy(*pProgram);
        }

        *pProgram = BGFX_INVALID_HANDLE;
    }

    for (bgfx::VertexBufferHandle *pBuffer : {&m_dropVertices, &m_curtainVertices})
    {
        if (bgfx::isValid(*pBuffer))
        {
            bgfx::destroy(*pBuffer);
        }

        *pBuffer = BGFX_INVALID_HANDLE;
    }

    for (bgfx::IndexBufferHandle *pBuffer : {&m_dropIndices, &m_curtainIndices})
    {
        if (bgfx::isValid(*pBuffer))
        {
            bgfx::destroy(*pBuffer);
        }

        *pBuffer = BGFX_INVALID_HANDLE;
    }

    for (bgfx::UniformHandle *pUniform : {&m_weatherUniform, &m_roofSampler, &m_roofUniform})
    {
        if (bgfx::isValid(*pUniform))
        {
            bgfx::destroy(*pUniform);
        }

        *pUniform = BGFX_INVALID_HANDLE;
    }

    for (bgfx::TextureHandle *pTexture : {&m_roofTexture, &m_noRoofTexture})
    {
        if (bgfx::isValid(*pTexture))
        {
            bgfx::destroy(*pTexture);
        }

        *pTexture = BGFX_INVALID_HANDLE;
    }

    m_roofPlacement = {};
    m_splashes.clear();
    resetCamera();
}

bool WeatherRenderer::isReady() const
{
    return bgfx::isValid(m_dropVertices) && bgfx::isValid(m_dropIndices) && bgfx::isValid(m_curtainVertices)
        && bgfx::isValid(m_curtainIndices) && bgfx::isValid(m_rainProgram) && bgfx::isValid(m_snowProgram)
        && bgfx::isValid(m_curtainProgram) && bgfx::isValid(m_splashProgram) && bgfx::isValid(m_weatherUniform)
        && bgfx::isValid(m_roofSampler) && bgfx::isValid(m_roofUniform) && bgfx::isValid(m_noRoofTexture);
}

bool WeatherRenderer::setRoofMap(const WeatherRoofMap *pRoofMap)
{
    if (bgfx::isValid(m_roofTexture))
    {
        bgfx::destroy(m_roofTexture);
        m_roofTexture = BGFX_INVALID_HANDLE;
    }

    m_roofPlacement = {};

    if (pRoofMap == nullptr || pRoofMap->empty() || !isReady())
    {
        return pRoofMap == nullptr || pRoofMap->empty();
    }

    const bgfx::Caps *pCaps = bgfx::getCaps();

    // Read in the vertex shader, as the grass reads its lightmaps (vs_terrain_decoration): every renderer in use
    // (GL 3.3, GLES 3, Vulkan) reads textures there, though bgfx's GL renderer does not report the vertex cap.
    if (pCaps == nullptr || (pCaps->formats[bgfx::TextureFormat::R32F] & BGFX_CAPS_FORMAT_TEXTURE_2D) == 0
        || pRoofMap->width() > pCaps->limits.maxTextureSize || pRoofMap->height() > pCaps->limits.maxTextureSize)
    {
        return false;
    }

    const std::vector<float> &heights = pRoofMap->heights();
    m_roofTexture = bgfx::createTexture2D(static_cast<uint16_t>(pRoofMap->width()),
        static_cast<uint16_t>(pRoofMap->height()), false, 1, bgfx::TextureFormat::R32F,
        BGFX_SAMPLER_POINT | BGFX_SAMPLER_UVW_CLAMP,
        bgfx::copy(heights.data(), static_cast<uint32_t>(heights.size() * sizeof(float))));

    if (!bgfx::isValid(m_roofTexture))
    {
        return false;
    }

    m_roofPlacement = {pRoofMap->originX(), pRoofMap->originY(),
        1.0f / (pRoofMap->cellSize() * static_cast<float>(pRoofMap->width())),
        1.0f / (pRoofMap->cellSize() * static_cast<float>(pRoofMap->height()))};
    return true;
}

void WeatherRenderer::resetCamera()
{
    m_hasCamera = false;
    m_cameraVelocity = {};
}

void WeatherRenderer::advanceLayer(Layer &layer, const std::array<float, 3> &velocity,
    const std::array<float, 3> &box, float deltaSeconds) const
{
    for (size_t axis = 0; axis < 3; ++axis)
    {
        layer.offset[axis] = wrapPositive(layer.offset[axis] + velocity[axis] * deltaSeconds, box[axis]);
    }
}

void WeatherRenderer::updateSplashes(const WeatherDrawFrame &frame, float rainLevel, uint32_t maxSplashes)
{
    const float dt = std::max(frame.deltaSeconds, 0.0f);

    for (Splash &splash : m_splashes)
    {
        splash.age += dt / SplashLifeSeconds;
    }

    std::erase_if(m_splashes, [](const Splash &splash) { return splash.age >= 1.0f; });

    if (maxSplashes == 0 || rainLevel <= 0.0f || !frame.groundHeight)
    {
        m_splashAccumulator = 0.0f;
        return;
    }

    m_splashAccumulator += dt * SplashesPerSecond * rainLevel;
    const float forwardAngle = std::atan2(frame.forward[1], frame.forward[0]);

    while (m_splashAccumulator >= 1.0f)
    {
        m_splashAccumulator -= 1.0f;

        if (m_splashes.size() >= maxSplashes)
        {
            continue;
        }

        // Even coverage of the ground area: radius grows with the square root.
        const float angle = forwardAngle + (unitRandom(m_splashRandom) * 2.0f - 1.0f) * SplashHalfAngle;
        const float minSquared = SplashMinDistance * SplashMinDistance;
        const float maxSquared = SplashMaxDistance * SplashMaxDistance;
        const float distance = std::sqrt(minSquared + (maxSquared - minSquared) * unitRandom(m_splashRandom));
        const float x = frame.camera[0] + std::cos(angle) * distance;
        const float y = frame.camera[1] + std::sin(angle) * distance;
        const std::optional<float> ground = frame.groundHeight(x, y);

        if (ground)
        {
            m_splashes.push_back({x, y, *ground, 0.0f, unitRandom(m_splashRandom)});
        }
    }
}

void WeatherRenderer::submitDrops(uint16_t viewId, bgfx::ProgramHandle program, uint32_t count, uint64_t state) const
{
    bgfx::setVertexBuffer(0, m_dropVertices);
    bgfx::setIndexBuffer(m_dropIndices, 0, std::min(count, MaxDrops) * 6);
    // Drops under the roof map's surfaces are not drawn (none without a map).
    bgfx::setTexture(0, m_roofSampler, bgfx::isValid(m_roofTexture) ? m_roofTexture : m_noRoofTexture);
    bgfx::setUniform(m_roofUniform, m_roofPlacement.data());
    bgfx::setState(state);
    bgfx::submit(viewId, program);
}

void WeatherRenderer::render(uint16_t viewId, const WeatherDrawFrame &frame)
{
    const float dt = std::max(frame.deltaSeconds, 0.0f);
    m_timeSeconds = std::fmod(m_timeSeconds + dt, TimeWrapSeconds);

    if (m_hasCamera && dt > 0.0f)
    {
        std::array<float, 3> velocity = {};
        float speedSquared = 0.0f;

        for (size_t axis = 0; axis < 3; ++axis)
        {
            velocity[axis] = (frame.camera[axis] - m_lastCamera[axis]) / dt;
            speedSquared += velocity[axis] * velocity[axis];
        }

        const float scale = speedSquared > MaxCameraSpeed * MaxCameraSpeed ? 0.0f : 1.0f;
        const float follow = 1.0f - std::exp(-dt / CameraVelocityFollowSeconds);

        for (size_t axis = 0; axis < 3; ++axis)
        {
            m_cameraVelocity[axis] += (velocity[axis] * scale - m_cameraVelocity[axis]) * follow;
        }
    }

    m_lastCamera = frame.camera;
    m_hasCamera = true;
    const std::array<float, 3> rainVelocity = {
        frame.windX * RainWindShare, frame.windY * RainWindShare, -RainFallSpeed};
    const std::array<float, 3> snowVelocity = {frame.windX, frame.windY, -frame.snowLook.fallSpeed};
    const std::array<float, 3> ashVelocity = {frame.windX, frame.windY, -frame.ashLook.fallSpeed};
    advanceLayer(m_rain, rainVelocity, RainBox, dt);
    advanceLayer(m_farRain, rainVelocity, FarRainBox, dt);
    advanceLayer(m_nearSnow, snowVelocity, NearSnowBox, dt);
    advanceLayer(m_farSnow, snowVelocity, FarSnowBox, dt);

    if (frame.ashLevel > 0.0f)
    {
        advanceLayer(m_nearAsh, ashVelocity, NearSnowBox, dt);
        advanceLayer(m_farAsh, ashVelocity, FarSnowBox, dt);
    }
    // The curtain's streak pattern scrolls down at the rain's fall speed.
    m_curtainPhase = wrapPositive(
        m_curtainPhase + dt * RainFallSpeed / (CurtainTop - CurtainBottom) * CurtainRepeats, 1.0f);

    const QualityBudget budget = qualityBudget(frame.quality);
    updateSplashes(frame, std::clamp(frame.rainLevel, 0.0f, 1.0f), budget.splashes);

    if (!isReady() || budget.rain == 0
        || (frame.rainLevel <= 0.001f && frame.snowLevel <= 0.001f && frame.ashLevel <= 0.001f))
    {
        return;
    }

    const uint64_t blendState = BGFX_STATE_WRITE_RGB | BGFX_STATE_DEPTH_TEST_LEQUAL | BGFX_STATE_MSAA
        | BGFX_STATE_BLEND_FUNC(BGFX_STATE_BLEND_ONE, BGFX_STATE_BLEND_INV_SRC_ALPHA);
    const auto setUniforms = [&](const std::array<float, 3> &centre, const std::array<float, 3> &box, float nearFade,
        const std::array<float, 4> &layerData, const std::array<float, 4> &motion,
        const std::array<float, 3> &color, float alpha, const std::array<float, 4> &extra)
    {
        const std::array<std::array<float, 4>, 6> values = {{
            {centre[0], centre[1], centre[2], m_timeSeconds},
            {box[0], box[1], box[2], nearFade},
            layerData,
            motion,
            {color[0] * frame.light[0], color[1] * frame.light[1], color[2] * frame.light[2], alpha},
            extra,
        }};
        bgfx::setUniform(m_weatherUniform, values.data(), 6);
    };

    if (frame.rainLevel > 0.001f)
    {
        const float level = std::clamp(frame.rainLevel, 0.0f, 1.0f);
        const std::array<float, 4> relativeVelocity = {
            rainVelocity[0] - m_cameraVelocity[0] * RainCameraMotionShare,
            rainVelocity[1] - m_cameraVelocity[1] * RainCameraMotionShare,
            rainVelocity[2] - m_cameraVelocity[2] * RainCameraMotionShare,
            RainStreakSeconds};
        setUniforms({frame.camera[0], frame.camera[1], frame.camera[2] + RainBoxLift}, RainBox, RainNearFade,
            {m_rain.offset[0], m_rain.offset[1], m_rain.offset[2], RainWidth}, relativeVelocity, frame.rainColor,
            0.3f + 0.3f * level, {0.0f, 0.0f, 0.0f, frame.pixelWorldSize});
        submitDrops(viewId, m_rainProgram, static_cast<uint32_t>(static_cast<float>(budget.rain) * level),
            blendState);

        if (budget.farRain > 0)
        {
            setUniforms({frame.camera[0], frame.camera[1], frame.camera[2] + FarRainBoxLift}, FarRainBox,
                FarRainNearFade, {m_farRain.offset[0], m_farRain.offset[1], m_farRain.offset[2], FarRainWidth},
                relativeVelocity, frame.rainColor, 0.3f + 0.3f * level, {0.0f, 0.0f, 0.0f, frame.pixelWorldSize});
            submitDrops(viewId, m_rainProgram, static_cast<uint32_t>(static_cast<float>(budget.farRain) * level),
                blendState);
        }

        if (!m_splashes.empty())
        {
            const bgfx::VertexLayout layout = weatherVertexLayout();
            const uint32_t vertexCount = static_cast<uint32_t>(m_splashes.size() * 6);

            if (bgfx::getAvailTransientVertexBuffer(vertexCount, layout) >= vertexCount)
            {
                bgfx::TransientVertexBuffer buffer;
                bgfx::allocTransientVertexBuffer(&buffer, vertexCount, layout);
                DropVertex *pVertex = reinterpret_cast<DropVertex *>(buffer.data);

                for (const Splash &splash : m_splashes)
                {
                    // Age and variation travel in the colour channels (normalised bytes).
                    const uint32_t age = static_cast<uint32_t>(std::clamp(splash.age, 0.0f, 1.0f) * 255.0f);
                    const uint32_t variation = static_cast<uint32_t>(splash.random * 255.0f);
                    const uint32_t packed = age | (variation << 8) | 0xff000000u;
                    const std::array<std::array<float, 2>, 6> corners = {{
                        {-1.0f, 0.0f}, {1.0f, 0.0f}, {1.0f, 1.0f}, {-1.0f, 0.0f}, {1.0f, 1.0f}, {-1.0f, 1.0f}}};

                    for (const std::array<float, 2> &corner : corners)
                    {
                        *pVertex++ = {splash.x, splash.y, splash.z, corner[0], corner[1], packed};
                    }
                }

                setUniforms(frame.camera, {SplashMaxDistance, 0.0f, 0.0f}, 0.0f, {0.0f, 0.0f, 0.0f, SplashSize}, {},
                    SplashColor, 0.6f + 0.3f * level, {0.0f, 0.0f, 0.0f, frame.pixelWorldSize});
                bgfx::setVertexBuffer(0, &buffer);
                bgfx::setState(blendState);
                bgfx::submit(viewId, m_splashProgram);
            }
        }

        // Heavy rain also falls in sheets in the distance.
        const float curtainAlpha = 0.35f * std::pow(level, 1.5f);

        for (uint32_t ring = 0; frame.curtain && ring < budget.curtainRings && curtainAlpha > 0.01f; ++ring)
        {
            const float radius = CurtainRadii[ring];
            const float columns = std::round(TwoPi * radius / CurtainStreakSpacing);
            setUniforms(frame.camera, {CurtainBottom, CurtainTop, 0.0f}, 0.0f,
                {0.0f, m_curtainPhase + 0.37f * static_cast<float>(ring), columns, CurtainRepeats},
                {rainVelocity[0] / RainFallSpeed, rainVelocity[1] / RainFallSpeed, 0.0f, 0.0f}, frame.rainColor,
                curtainAlpha,
                {0.0f, 0.0f, radius, frame.pixelWorldSize});
            bgfx::setVertexBuffer(0, m_curtainVertices);
            bgfx::setIndexBuffer(m_curtainIndices);
            bgfx::setState(blendState);
            bgfx::submit(viewId, m_curtainProgram);
        }
    }

    if (frame.snowLevel > 0.001f)
    {
        submitFlakes(viewId, frame, frame.snowLook, frame.snowLevel, m_nearSnow, m_farSnow, budget.nearSnow,
            budget.farSnow, blendState);
    }

    if (frame.ashLevel > 0.001f)
    {
        submitFlakes(viewId, frame, frame.ashLook, frame.ashLevel, m_nearAsh, m_farAsh, budget.nearSnow,
            budget.farSnow, blendState);
    }
}

void WeatherRenderer::submitFlakes(uint16_t viewId, const WeatherDrawFrame &frame, const WeatherFlakeLook &look,
    float shownLevel, const Layer &nearLayer, const Layer &farLayer, uint32_t nearCount, uint32_t farCount,
    uint64_t state)
{
    const float level = std::clamp(shownLevel, 0.0f, 1.0f);
    const std::array<float, 4> sway = {look.sway, look.swayRate, 0.0f, frame.pixelWorldSize};
    const std::array<float, 4> relativeVelocity = {
        frame.windX - m_cameraVelocity[0] * RainCameraMotionShare,
        frame.windY - m_cameraVelocity[1] * RainCameraMotionShare,
        -look.fallSpeed - m_cameraVelocity[2] * RainCameraMotionShare,
        SnowStreakSeconds};
    const auto setUniforms = [&](const std::array<float, 3> &centre, const std::array<float, 3> &box, float nearFade,
        const Layer &layer, float size, float alpha)
    {
        const std::array<std::array<float, 4>, 6> values = {{
            {centre[0], centre[1], centre[2], m_timeSeconds},
            {box[0], box[1], box[2], nearFade},
            {layer.offset[0], layer.offset[1], layer.offset[2], size},
            relativeVelocity,
            {look.color[0] * frame.light[0], look.color[1] * frame.light[1], look.color[2] * frame.light[2], alpha},
            sway,
        }};
        bgfx::setUniform(m_weatherUniform, values.data(), 6);
    };

    if (farCount > 0)
    {
        setUniforms({frame.camera[0], frame.camera[1], frame.camera[2] + FarSnowBoxLift}, FarSnowBox, FarSnowFade,
            farLayer, look.size[1], look.alpha[1]);
        submitDrops(viewId, m_snowProgram, static_cast<uint32_t>(static_cast<float>(farCount) * level), state);
    }

    setUniforms({frame.camera[0], frame.camera[1], frame.camera[2] + NearSnowBoxLift}, NearSnowBox, NearSnowFade,
        nearLayer, look.size[0], look.alpha[0]);
    submitDrops(viewId, m_snowProgram, static_cast<uint32_t>(static_cast<float>(nearCount) * level), state);
}
}
