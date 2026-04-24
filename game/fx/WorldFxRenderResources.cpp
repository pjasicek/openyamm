#include "game/fx/WorldFxRenderResources.h"

#include <algorithm>
#include <utility>

namespace OpenYAMM::Game
{
bgfx::VertexLayout WorldFxParticleVertex::ms_layout;

void WorldFxParticleVertex::init()
{
    ms_layout.begin()
        .add(bgfx::Attrib::Position, 3, bgfx::AttribType::Float)
        .add(bgfx::Attrib::TexCoord0, 2, bgfx::AttribType::Float)
        .add(bgfx::Attrib::Color0, 4, bgfx::AttribType::Uint8, true)
        .end();
}

void WorldFxRenderResources::reset()
{
    m_particleProgramHandle = BGFX_INVALID_HANDLE;
    m_particleParamsUniformHandle = BGFX_INVALID_HANDLE;
    m_textureSamplerHandle = BGFX_INVALID_HANDLE;
    m_particleTextures.clear();
    m_particleTextureHandleIndices.fill(bgfx::kInvalidHandle);
    m_particleVertexBatches = {};
}

void WorldFxRenderResources::shutdown()
{
    if (bgfx::isValid(m_particleProgramHandle))
    {
        bgfx::destroy(m_particleProgramHandle);
    }

    if (bgfx::isValid(m_particleParamsUniformHandle))
    {
        bgfx::destroy(m_particleParamsUniformHandle);
    }

    if (bgfx::isValid(m_textureSamplerHandle))
    {
        bgfx::destroy(m_textureSamplerHandle);
    }

    for (const WorldFxParticleTexture &texture : m_particleTextures)
    {
        if (bgfx::isValid(texture.textureHandle))
        {
            bgfx::destroy(texture.textureHandle);
        }
    }

    reset();
}

bool WorldFxRenderResources::isReady() const
{
    return bgfx::isValid(m_particleProgramHandle)
        && bgfx::isValid(m_particleParamsUniformHandle)
        && bgfx::isValid(m_textureSamplerHandle);
}

bgfx::ProgramHandle WorldFxRenderResources::particleProgramHandle() const
{
    return m_particleProgramHandle;
}

void WorldFxRenderResources::setParticleProgramHandle(bgfx::ProgramHandle handle)
{
    m_particleProgramHandle = handle;
}

bgfx::UniformHandle WorldFxRenderResources::particleParamsUniformHandle() const
{
    return m_particleParamsUniformHandle;
}

void WorldFxRenderResources::setParticleParamsUniformHandle(bgfx::UniformHandle handle)
{
    m_particleParamsUniformHandle = handle;
}

bgfx::UniformHandle WorldFxRenderResources::textureSamplerHandle() const
{
    return m_textureSamplerHandle;
}

void WorldFxRenderResources::setTextureSamplerHandle(bgfx::UniformHandle handle)
{
    m_textureSamplerHandle = handle;
}

const std::array<uint16_t, WorldFxRenderResources::ParticleMaterialCount>
    &WorldFxRenderResources::particleTextureHandleIndices() const
{
    return m_particleTextureHandleIndices;
}

std::array<uint16_t, WorldFxRenderResources::ParticleMaterialCount>
    &WorldFxRenderResources::particleTextureHandleIndices()
{
    return m_particleTextureHandleIndices;
}

const std::array<std::vector<WorldFxParticleVertex>, WorldFxRenderResources::ParticleBatchCount>
    &WorldFxRenderResources::particleVertexBatches() const
{
    return m_particleVertexBatches;
}

std::array<std::vector<WorldFxParticleVertex>, WorldFxRenderResources::ParticleBatchCount>
    &WorldFxRenderResources::particleVertexBatches()
{
    return m_particleVertexBatches;
}

const WorldFxParticleTexture *WorldFxRenderResources::findParticleTexture(const std::string &textureName) const
{
    const auto textureIterator =
        std::find_if(
            m_particleTextures.begin(),
            m_particleTextures.end(),
            [&textureName](const WorldFxParticleTexture &texture)
            {
                return texture.textureName == textureName;
            });

    if (textureIterator == m_particleTextures.end())
    {
        return nullptr;
    }

    return &*textureIterator;
}

void WorldFxRenderResources::addParticleTexture(WorldFxParticleTexture texture)
{
    m_particleTextures.push_back(std::move(texture));
}
}
