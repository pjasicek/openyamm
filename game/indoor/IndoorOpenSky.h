#pragma once

#include "game/FaceEnums.h"

#include <string>

namespace OpenYAMM::Game
{
// Scene `sky` (devdocs/INDOOR_OPEN_SKY.md): an indoor map open to the sky (an MM9 city as a BLV). Its IndoorSky faces
// are not drawn; the Enhanced outdoor sky (level_generation/lighting/SKY_RENDERING.md) shows where they are, with the
// game's time of day. Off by default: every other map draws its sky faces with the projected indoor sky, as before.
struct IndoorOpenSky
{
    bool enabled = false;
    // An original sky texture the Enhanced sky takes its legacy preset from ("plansky3"), empty for the default.
    std::string skyTexture;
    // A named sky preset that overrides the automatic choice, empty for none.
    std::string preset;
    // `view: outdoor`: the view as an outdoor map's (devdocs/INDOOR_OPEN_SKY.md "Outdoor view"): the player's view
    // distance (video view_distance x viewDistanceScale) is the far plane and the portal walk's reach, and the scene
    // fades into the sky's colour by the outdoor haze instead of the scene fog. Off: the scene's own fog and view.
    bool outdoorView = false;
    float viewDistanceScale = 1.0f;
    // `weather: rain | snow | rain_and_snow`: the outdoor weather (WeatherModel, weather.yml chances by map file) over
    // the open sky: rain and snow fall where the camera is in the open, and the sky follows them. Off by default.
    bool weatherRain = false;
    bool weatherSnow = false;
};

// Whether a face with these attributes is left out of the drawn faces, the open sky showing in its place.
inline bool indoorFaceShowsOpenSky(const IndoorOpenSky &sky, uint32_t attributes)
{
    return sky.enabled && hasFaceAttribute(attributes, FaceAttribute::IndoorSky);
}
}
