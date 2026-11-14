#include "game/render/FirstPersonViewModelFx.h"

#include "engine/BgfxContext.h"
#include "game/render/RuntimeShader.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
// How long a blade sample lingers in the trail, and how many pieces each gap between samples is drawn in (the swing
// moves far between frames).
constexpr float TrailSeconds = 0.11f;
constexpr int TrailSubdivisions = 4;
// The ribbon starts this far up the blade from the hilt (the hand stays clear) and ends a little past the tip.
constexpr float TrailInnerFraction = 0.2f;
constexpr float TrailOuterOvershoot = 0.08f;
constexpr float FlashSeconds = 0.16f;
constexpr int TextureSize = 64;

using Vec3 = std::array<float, 3>;

Vec3 add(const Vec3 &a, const Vec3 &b)
{
    return {a[0] + b[0], a[1] + b[1], a[2] + b[2]};
}

Vec3 sub(const Vec3 &a, const Vec3 &b)
{
    return {a[0] - b[0], a[1] - b[1], a[2] - b[2]};
}

Vec3 scale(const Vec3 &a, float s)
{
    return {a[0] * s, a[1] * s, a[2] * s};
}

Vec3 mix(const Vec3 &a, const Vec3 &b, float t)
{
    return add(a, scale(sub(b, a), t));
}

// Catmull-Rom through p1..p2 with neighbours p0 and p3.
Vec3 catmullRom(const Vec3 &p0, const Vec3 &p1, const Vec3 &p2, const Vec3 &p3, float t)
{
    const float t2 = t * t;
    const float t3 = t2 * t;
    Vec3 out;
    for (size_t i = 0; i < 3; ++i)
    {
        out[i] = 0.5f * (2.0f * p1[i] + (-p0[i] + p2[i]) * t + (2.0f * p0[i] - 5.0f * p1[i] + 4.0f * p2[i] - p3[i]) * t2
            + (-p0[i] + 3.0f * p1[i] - 3.0f * p2[i] + p3[i]) * t3);
    }
    return out;
}

uint32_t packColor(const Vec3 &color, float alpha)
{
    const auto channel = [](float value)
    {
        return uint32_t(std::lround(std::clamp(value, 0.0f, 1.0f) * 255.0f));
    };
    return channel(color[0]) | (channel(color[1]) << 8) | (channel(color[2]) << 16) | (channel(alpha) << 24);
}

// White texels with the shape in alpha: the vertex colour tints them.
bgfx::TextureHandle makeTexture(int width, int height, float (*pShape)(float, float))
{
    std::vector<uint8_t> texels(size_t(width) * size_t(height) * 4);
    for (int y = 0; y < height; ++y)
    {
        for (int x = 0; x < width; ++x)
        {
            const float u = (float(x) + 0.5f) / float(width);
            const float v = (float(y) + 0.5f) / float(height);
            const size_t index = (size_t(y) * size_t(width) + size_t(x)) * 4;
            texels[index] = 255;
            texels[index + 1] = 255;
            texels[index + 2] = 255;
            texels[index + 3] = uint8_t(std::lround(std::clamp(pShape(u, v), 0.0f, 1.0f) * 255.0f));
        }
    }
    return bgfx::createTexture2D(uint16_t(width), uint16_t(height), false, 1, bgfx::TextureFormat::RGBA8,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP, bgfx::copy(texels.data(), uint32_t(texels.size())));
}

// A soft round mote with a brighter core.
float dotShape(float u, float v)
{
    const float x = u * 2.0f - 1.0f;
    const float y = v * 2.0f - 1.0f;
    const float r2 = x * x + y * y;
    return std::exp(-r2 * 5.0f) * 0.75f + std::exp(-r2 * 28.0f) * 0.6f;
}

// A four-pointed twinkle.
float starShape(float u, float v)
{
    const float x = u * 2.0f - 1.0f;
    const float y = v * 2.0f - 1.0f;
    const float r2 = x * x + y * y;
    const float arms = std::exp(-x * x * 160.0f) * std::exp(-y * y * 2.2f)
        + std::exp(-y * y * 160.0f) * std::exp(-x * x * 2.2f);
    return std::min(1.0f, arms * 0.85f + std::exp(-r2 * 30.0f));
}

// Across the trail (v: 0 inner edge, 1 outer edge past the tip): faint near the hand, brightest just inside the tip,
// a soft outer edge; faint streaks along it (u) so it reads as a cut rather than a flat sheet.
float trailShape(float u, float v)
{
    const float rise = v < 0.86f ? std::pow(v / 0.86f, 1.6f) : 1.0f - (v - 0.86f) / 0.14f;
    const float streaks = 0.82f + 0.18f * std::sin(v * 71.0f + std::sin(u * 9.0f) * 1.3f);
    return std::max(0.0f, rise) * streaks;
}
}

void FirstPersonViewModelFx::addTrailSample(size_t blade, float time, const Vec3 &hilt, const Vec3 &tip,
    float strength)
{
    std::vector<TrailSample> &trail = m_trails[std::min(blade, m_trails.size() - 1)];
    trail.push_back({time, hilt, tip, std::clamp(strength, 0.0f, 1.0f)});
    while (!trail.empty() && time - trail.front().time > TrailSeconds * 2.0f)
    {
        trail.erase(trail.begin());
    }
}

void FirstPersonViewModelFx::clearTrail()
{
    for (std::vector<TrailSample> &trail : m_trails)
    {
        trail.clear();
    }
}

void FirstPersonViewModelFx::setTrailColor(const Vec3 &color, float intensity)
{
    m_trailColor = color;
    m_trailIntensity = intensity;
}

void FirstPersonViewModelFx::setCastGlow(const std::vector<Vec3> &palms, const Vec3 &color, float charge)
{
    m_glowPalms = palms;
    m_glowColor = color;
    m_glowCharge = std::clamp(charge, 0.0f, 1.0f);
    m_glowing = !palms.empty();
}

void FirstPersonViewModelFx::stopCastGlow()
{
    m_glowing = false;
    m_glowPalms.clear();
}

void FirstPersonViewModelFx::releaseCast(const std::vector<Vec3> &palms, const Vec3 &color)
{
    m_flashPalms = palms;
    m_flashColor = color;
    m_flashAge = 0.0f;
    std::uniform_real_distribution<float> unit(-1.0f, 1.0f);
    for (const Vec3 &palm : palms)
    {
        for (int spark = 0; spark < 18; ++spark)
        {
            Mote mote;
            mote.position = palm;
            // Forward (+Y), spread around it.
            const float speed = 55.0f + 60.0f * (unit(m_random) * 0.5f + 0.5f);
            mote.velocity = {unit(m_random) * 32.0f, speed, unit(m_random) * 32.0f};
            mote.life = 0.22f + 0.18f * (unit(m_random) * 0.5f + 0.5f);
            mote.size = 0.7f + 0.6f * (unit(m_random) * 0.5f + 0.5f);
            mote.color = mix(color, {1.0f, 1.0f, 1.0f}, 0.25f * (unit(m_random) * 0.5f + 0.5f));
            mote.star = spark % 2 == 0;
            m_motes.push_back(mote);
        }
    }
    stopCastGlow();
}

void FirstPersonViewModelFx::spawnMote(const Vec3 &palm, const Vec3 &color, bool gathering)
{
    std::uniform_real_distribution<float> unit(-1.0f, 1.0f);
    Vec3 direction = {unit(m_random), unit(m_random), unit(m_random)};
    const float length = std::max(0.001f, std::sqrt(direction[0] * direction[0] + direction[1] * direction[1]
        + direction[2] * direction[2]));
    direction = scale(direction, 1.0f / length);
    Mote mote;
    const float radius = gathering ? 4.5f + 3.5f * (unit(m_random) * 0.5f + 0.5f) : 1.0f;
    mote.position = add(palm, scale(direction, radius));
    // A swirl around the palm (about the forward axis) on top of the pull in.
    mote.velocity = scale(Vec3{-direction[2], 0.0f, direction[0]}, 14.0f + 10.0f * unit(m_random));
    mote.anchor = palm;
    mote.attract = gathering ? 55.0f : 0.0f;
    mote.life = 0.35f + 0.2f * (unit(m_random) * 0.5f + 0.5f);
    mote.size = 0.45f + 0.55f * (unit(m_random) * 0.5f + 0.5f);
    mote.color = mix(color, {1.0f, 1.0f, 1.0f}, 0.15f * (unit(m_random) * 0.5f + 0.5f));
    mote.star = (m_random() % 4) == 0;
    m_motes.push_back(mote);
}

void FirstPersonViewModelFx::update(float deltaSeconds)
{
    const float delta = std::clamp(deltaSeconds, 0.0f, 0.1f);
    if (m_glowing)
    {
        // About 55 motes a second per palm at full charge, fewer while it builds.
        m_spawnDebt += delta * 55.0f * (0.35f + 0.65f * m_glowCharge) * float(m_glowPalms.size());
        while (m_spawnDebt >= 1.0f)
        {
            m_spawnDebt -= 1.0f;
            spawnMote(m_glowPalms[m_random() % m_glowPalms.size()], m_glowColor, true);
        }
    }
    for (Mote &mote : m_motes)
    {
        mote.age += delta;
        if (mote.attract > 0.0f)
        {
            mote.velocity = add(mote.velocity, scale(sub(mote.anchor, mote.position), mote.attract * delta));
            mote.velocity = scale(mote.velocity, std::max(0.0f, 1.0f - 3.0f * delta));
        }
        mote.position = add(mote.position, scale(mote.velocity, delta));
    }
    m_motes.erase(
        std::remove_if(m_motes.begin(), m_motes.end(), [](const Mote &mote) { return mote.age >= mote.life; }),
        m_motes.end());
    m_flashAge += delta;
}

bool FirstPersonViewModelFx::ensureResources()
{
    if (bgfx::isValid(m_program))
    {
        return true;
    }
    if (m_resourcesAttempted || bgfx::getRendererType() == bgfx::RendererType::Noop)
    {
        return false;
    }
    m_resourcesAttempted = true;
    m_program = loadRuntimeProgram("vs_particle", "fs_particle");
    if (!bgfx::isValid(m_program))
    {
        return false;
    }
    m_textureSampler = bgfx::createUniform("s_texColor", bgfx::UniformType::Sampler);
    m_paramsUniform = bgfx::createUniform("u_particleParams", bgfx::UniformType::Vec4);
    m_dotTexture = makeTexture(TextureSize, TextureSize, dotShape);
    m_starTexture = makeTexture(TextureSize, TextureSize, starShape);
    m_trailTexture = makeTexture(16, TextureSize, trailShape);
    m_layout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord0, 2, bgfx::AttribType::Float)
        .add(bgfx::Attrib::Color0, 4, bgfx::AttribType::Uint8, true)
        .end();
    return true;
}

void FirstPersonViewModelFx::render(uint16_t viewId, float time)
{
    const bool anything = m_trails[0].size() >= 2 || m_trails[1].size() >= 2 || !m_motes.empty() || m_glowing
        || m_flashAge < FlashSeconds;
    if (!anything || !ensureResources())
    {
        return;
    }
    // Additive light over the arms. The trail is hidden by the arms in front of it; the casting glow is light in the
    // palm, so it shows through the fingers that hold it (it sits inside the hand's depth).
    const uint64_t trailState =
        BGFX_STATE_WRITE_RGB | BGFX_STATE_BLEND_ADD | BGFX_STATE_DEPTH_TEST_LESS | BGFX_STATE_MSAA;
    const uint64_t glowState = BGFX_STATE_WRITE_RGB | BGFX_STATE_BLEND_ADD | BGFX_STATE_MSAA;
    const float params[4] = {1.0f, 0.0f, 0.0f, 0.0f};
    const auto submit = [&](const std::vector<Vertex> &vertices, bgfx::TextureHandle texture, uint64_t state)
    {
        if (vertices.empty() || bgfx::getAvailTransientVertexBuffer(uint32_t(vertices.size()), m_layout)
                < vertices.size())
        {
            return;
        }
        bgfx::TransientVertexBuffer buffer;
        bgfx::allocTransientVertexBuffer(&buffer, uint32_t(vertices.size()), m_layout);
        std::copy(vertices.begin(), vertices.end(), reinterpret_cast<Vertex *>(buffer.data));
        bgfx::setVertexBuffer(0, &buffer);
        bgfx::setTexture(0, m_textureSampler, texture);
        bgfx::setUniform(m_paramsUniform, params);
        bgfx::setState(state);
        bgfx::submit(viewId, m_program);
    };

    // Each trail: Catmull-Rom through the recent hilt and tip samples, faded by age and by how fast the blade went.
    for (const std::vector<TrailSample> &trail : m_trails)
    {
        std::vector<TrailSample> samples;
        for (const TrailSample &sample : trail)
        {
            if (time - sample.time < TrailSeconds)
            {
                samples.push_back(sample);
            }
        }
        if (samples.size() >= 2)
        {
            std::vector<TrailSample> points;
            for (size_t index = 0; index + 1 < samples.size(); ++index)
            {
                const TrailSample &p0 = samples[index == 0 ? 0 : index - 1];
                const TrailSample &p1 = samples[index];
                const TrailSample &p2 = samples[index + 1];
                const TrailSample &p3 = samples[std::min(index + 2, samples.size() - 1)];
                for (int step = 0; step < TrailSubdivisions; ++step)
                {
                    const float t = float(step) / float(TrailSubdivisions);
                    TrailSample point;
                    point.time = p1.time + (p2.time - p1.time) * t;
                    point.strength = p1.strength + (p2.strength - p1.strength) * t;
                    point.hilt = catmullRom(p0.hilt, p1.hilt, p2.hilt, p3.hilt, t);
                    point.tip = catmullRom(p0.tip, p1.tip, p2.tip, p3.tip, t);
                    points.push_back(point);
                }
            }
            points.push_back(samples.back());
            std::vector<Vertex> vertices;
            vertices.reserve(points.size() * 6);
            const auto edge = [&](const TrailSample &point, float u, Vertex &inner, Vertex &outer)
            {
                const Vec3 blade = sub(point.tip, point.hilt);
                const Vec3 innerPoint = add(point.hilt, scale(blade, TrailInnerFraction));
                const Vec3 outerPoint = add(point.tip, scale(blade, TrailOuterOvershoot));
                const float age = std::clamp((time - point.time) / TrailSeconds, 0.0f, 1.0f);
                const float alpha = m_trailIntensity * point.strength * std::pow(1.0f - age, 1.5f);
                const uint32_t color = packColor(m_trailColor, alpha);
                inner = {innerPoint[0], innerPoint[1], innerPoint[2], u, 0.0f, color};
                outer = {outerPoint[0], outerPoint[1], outerPoint[2], u, 1.0f, color};
            };
            for (size_t index = 0; index + 1 < points.size(); ++index)
            {
                Vertex a0;
                Vertex a1;
                Vertex b0;
                Vertex b1;
                edge(points[index], float(index) / float(points.size()), a0, a1);
                edge(points[index + 1], float(index + 1) / float(points.size()), b0, b1);
                vertices.insert(vertices.end(), {a0, a1, b1, a0, b1, b0});
            }
            submit(vertices, m_trailTexture, trailState);
        }
    }

    // Motes, the palm glow and the release flash: quads facing the eye (right +X, up +Z in the arms' space).
    std::vector<Vertex> dots;
    std::vector<Vertex> stars;
    const auto quad = [](std::vector<Vertex> &out, const Vec3 &center, float size, const Vec3 &color, float alpha)
    {
        const float h = size * 0.5f;
        const uint32_t packed = packColor(color, alpha);
        const Vertex v0 = {center[0] - h, center[1], center[2] - h, 0.0f, 1.0f, packed};
        const Vertex v1 = {center[0] + h, center[1], center[2] - h, 1.0f, 1.0f, packed};
        const Vertex v2 = {center[0] + h, center[1], center[2] + h, 1.0f, 0.0f, packed};
        const Vertex v3 = {center[0] - h, center[1], center[2] + h, 0.0f, 0.0f, packed};
        out.insert(out.end(), {v0, v1, v2, v0, v2, v3});
    };
    for (const Mote &mote : m_motes)
    {
        const float t = mote.age / mote.life;
        const float fade = std::min(1.0f, t / 0.2f) * std::min(1.0f, (1.0f - t) / 0.4f);
        quad(mote.star ? stars : dots, mote.position, mote.size * (mote.star ? 2.2f : 1.0f), mote.color, fade);
    }
    if (m_glowing)
    {
        const float pulse = 1.0f + 0.08f * std::sin(time * 19.0f);
        for (const Vec3 &palm : m_glowPalms)
        {
            quad(dots, palm, (2.6f + 4.2f * m_glowCharge) * pulse, m_glowColor, 0.35f + 0.5f * m_glowCharge);
            quad(dots, palm, (1.2f + 1.6f * m_glowCharge) * pulse, mix(m_glowColor, {1.0f, 1.0f, 1.0f}, 0.3f),
                0.4f + 0.4f * m_glowCharge);
        }
    }
    if (m_flashAge < FlashSeconds)
    {
        const float t = m_flashAge / FlashSeconds;
        for (const Vec3 &palm : m_flashPalms)
        {
            quad(dots, palm, 5.0f + 7.0f * t, m_flashColor, 1.0f - t);
            quad(stars, palm, 7.0f + 6.0f * t, mix(m_flashColor, {1.0f, 1.0f, 1.0f}, 0.35f), (1.0f - t) * 0.9f);
        }
    }
    submit(dots, m_dotTexture, glowState);
    submit(stars, m_starTexture, glowState);
}

void FirstPersonViewModelFx::shutdown()
{
    clearTrail();
    m_motes.clear();
    stopCastGlow();
    m_flashAge = 1.0f;
    if (Engine::BgfxContext::isBgfxInitialized())
    {
        for (bgfx::TextureHandle *pTexture : {&m_dotTexture, &m_starTexture, &m_trailTexture})
        {
            if (bgfx::isValid(*pTexture))
            {
                bgfx::destroy(*pTexture);
            }
        }
        if (bgfx::isValid(m_textureSampler))
        {
            bgfx::destroy(m_textureSampler);
        }
        if (bgfx::isValid(m_paramsUniform))
        {
            bgfx::destroy(m_paramsUniform);
        }
        if (bgfx::isValid(m_program))
        {
            bgfx::destroy(m_program);
        }
    }
    m_dotTexture = m_starTexture = m_trailTexture = BGFX_INVALID_HANDLE;
    m_textureSampler = m_paramsUniform = BGFX_INVALID_HANDLE;
    m_program = BGFX_INVALID_HANDLE;
    m_resourcesAttempted = false;
}
}
