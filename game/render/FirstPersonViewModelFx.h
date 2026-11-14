#pragma once

#include <bgfx/bgfx.h>

#include <array>
#include <cstdint>
#include <random>
#include <vector>

namespace OpenYAMM::Game
{
// The first-person arms' own effects, drawn in their view after them (FirstPersonViewModelView): the weapon trail, a
// faint ribbon swept by the blade between hilt and tip over the last tenth of a second while it moves fast, and the
// casting glow, motes gathering on the casting hand during a cast clip that burst out at its release, coloured by the
// spell's school. Positions are in the arms' model space (the eye looks along +Y with +Z up). Textures are made here,
// so the effects need no assets. devdocs/solo_action/README.md "Weapon trail" and "Casting".
class FirstPersonViewModelFx
{
public:
    // One blade sample: the hilt and the tip, and how fast the tip moved (0: at rest, 1: a full swing). blade 0 is the
    // main hand's, 1 the off hand's (dual wielding); each leaves its own trail.
    void addTrailSample(size_t blade, float time, const std::array<float, 3> &hilt, const std::array<float, 3> &tip,
        float strength);
    void clearTrail();
    // The trail's colour (an enchantment's element, else steel) and peak opacity.
    void setTrailColor(const std::array<float, 3> &color, float intensity);

    // While charging, motes gather on each palm and a core glows there, growing with charge (0..1).
    void setCastGlow(const std::vector<std::array<float, 3>> &palms, const std::array<float, 3> &color, float charge);
    void stopCastGlow();
    // The spell leaves: a flash and a burst of sparks from each palm, forward (+Y).
    void releaseCast(const std::vector<std::array<float, 3>> &palms, const std::array<float, 3> &color);

    void update(float deltaSeconds);
    void render(uint16_t viewId, float time);
    void shutdown();

private:
    struct TrailSample
    {
        float time = 0.0f;
        std::array<float, 3> hilt = {};
        std::array<float, 3> tip = {};
        float strength = 0.0f;
    };
    struct Mote
    {
        std::array<float, 3> position = {};
        std::array<float, 3> velocity = {};
        // Pulled towards this point (a palm), or free when attract is 0.
        std::array<float, 3> anchor = {};
        float attract = 0.0f;
        float age = 0.0f;
        float life = 0.5f;
        float size = 1.0f;
        std::array<float, 3> color = {};
        bool star = false;
    };
    struct Vertex
    {
        float x;
        float y;
        float z;
        float u;
        float v;
        uint32_t abgr;
    };

    bool ensureResources();
    void spawnMote(const std::array<float, 3> &palm, const std::array<float, 3> &color, bool gathering);

    std::array<std::vector<TrailSample>, 2> m_trails;
    std::array<float, 3> m_trailColor = {0.82f, 0.88f, 1.0f};
    float m_trailIntensity = 0.45f;
    std::vector<Mote> m_motes;
    std::vector<std::array<float, 3>> m_glowPalms;
    std::array<float, 3> m_glowColor = {};
    float m_glowCharge = 0.0f;
    bool m_glowing = false;
    float m_spawnDebt = 0.0f;
    // A release flash at each palm, fading out.
    std::vector<std::array<float, 3>> m_flashPalms;
    std::array<float, 3> m_flashColor = {};
    float m_flashAge = 1.0f;
    std::mt19937 m_random{0x5eedu};

    bool m_resourcesAttempted = false;
    bgfx::ProgramHandle m_program = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_textureSampler = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_paramsUniform = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle m_dotTexture = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle m_starTexture = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle m_trailTexture = BGFX_INVALID_HANDLE;
    bgfx::VertexLayout m_layout;
};
}
