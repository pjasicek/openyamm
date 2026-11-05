#include "game/indoor/IndoorPortalDebugView.h"

#include <iomanip>
#include <sstream>

namespace OpenYAMM::Game
{
const char *indoorDebugPassName(IndoorDebugPass pass)
{
    switch (pass)
    {
    case IndoorDebugPass::Decorations:
        return "Indoor pass: decorations";
    case IndoorDebugPass::Actors:
        return "Indoor pass: actors";
    case IndoorDebugPass::OpenSky:
        return "Indoor pass: open sky";
    case IndoorDebugPass::Translucent:
        return "Indoor pass: translucent and effects";
    case IndoorDebugPass::Count:
        break;
    }
    return "Indoor pass";
}

uint32_t indoorPortalDebugSectorColor(int16_t sectorId)
{
    // Golden-ratio hues, full saturation, bright: neighbouring ids differ clearly.
    const float hue = static_cast<float>(static_cast<uint16_t>(sectorId) % 4096u) * 0.61803398875f;
    float fraction = hue - static_cast<float>(static_cast<int>(hue));
    // No cyan: that is the portal faces' colour.
    if (fraction > 0.40f && fraction < 0.60f)
    {
        fraction += 0.25f;
    }
    const float h = fraction * 6.0f;
    const int sextant = static_cast<int>(h);
    const float f = h - static_cast<float>(sextant);
    float r = 1.0f;
    float g = 1.0f;
    float b = 1.0f;
    switch (sextant)
    {
    case 0: r = 1.0f; g = f; b = 0.2f; break;
    case 1: r = 1.0f - f; g = 1.0f; b = 0.2f; break;
    case 2: r = 0.2f; g = 1.0f; b = f; break;
    case 3: r = 0.2f; g = 1.0f - f; b = 1.0f; break;
    case 4: r = f; g = 0.2f; b = 1.0f; break;
    default: r = 1.0f; g = 0.2f; b = 1.0f - f; break;
    }
    const auto channel = [](float value) { return static_cast<uint32_t>(value * 255.0f + 0.5f) & 0xffu; };
    return 0xff000000u | (channel(b) << 16) | (channel(g) << 8) | channel(r);
}

std::string describeIndoorPortalDebugStats(const IndoorPortalDebugStats &stats)
{
    std::ostringstream out;
    out << std::fixed << std::setprecision(1);
    out << "eye=" << stats.eye[0] << ',' << stats.eye[1] << ',' << stats.eye[2]
        << std::setprecision(3) << " yaw=" << stats.yawRadians << " pitch=" << stats.pitchRadians
        << std::setprecision(1)
        << " eye_sector=" << stats.eyeSectorId
        << " sectors_drawn=" << stats.sectorsDrawn
        << " nodes=" << stats.visibilityNodes
        << " portals_tested=" << stats.portalsTested
        << " portals_traversed=" << stats.portalsTraversed
        << " rejected_facing=" << stats.portalsRejectedFacing
        << " rejected_clipped=" << stats.portalsRejectedClipped
        << " rejected_other=" << stats.portalsRejectedOther
        << " visibility_build_us=" << static_cast<double>(stats.visibilityBuildNanoseconds) / 1000.0
        << " visibility_rebuilt=" << (stats.visibilityRebuilt ? 1 : 0)
        << " batches=" << stats.batchesSubmitted
        << " faces=" << stats.facesSubmitted
        << " triangles=" << stats.trianglesSubmitted
        << " faces_in_view=" << stats.facesInView
        << " faces_in_portals=" << stats.facesInPortals
        << " triangles_in_portals=" << stats.trianglesInPortals
        << " tile_draws=" << stats.tileDraws
        << " tile_triangles=" << stats.tileTriangles
        << " batch_textures=" << stats.batchTextures
        << " face_draws=" << stats.faceDraws
        << " cpu_visibility_us=" << static_cast<double>(stats.cpuVisibilityNanoseconds) / 1000.0
        << " cpu_lighting_us=" << static_cast<double>(stats.cpuLightingNanoseconds) / 1000.0
        << " cpu_faces_us=" << static_cast<double>(stats.cpuFacesNanoseconds) / 1000.0
        << " cpu_decorations_us=" << static_cast<double>(stats.cpuDecorationsNanoseconds) / 1000.0
        << " cpu_actors_us=" << static_cast<double>(stats.cpuActorsNanoseconds) / 1000.0
        << " cpu_open_sky_us=" << static_cast<double>(stats.cpuOpenSkyNanoseconds) / 1000.0
        << " cpu_translucent_us=" << static_cast<double>(stats.cpuTranslucentNanoseconds) / 1000.0
        << " cpu_render_us=" << static_cast<double>(stats.cpuTotalNanoseconds) / 1000.0
        << " sectors=";
    for (size_t index = 0; index < stats.sectors.size(); ++index)
    {
        const IndoorPortalDebugSector &sector = stats.sectors[index];
        out << (index == 0 ? "" : ",") << sector.sectorId << ':' << sector.faces << '/' << sector.facesInPortals
            << '/' << sector.triangles << '/' << sector.batches << '/' << sector.tileDraws << '/'
            << sector.tileTriangles << '/' << sector.portalsTested << '/' << sector.totalFaces << '/' << sector.nodes
            << '/' << sector.portalLinks;
    }
    return out.str();
}
}
