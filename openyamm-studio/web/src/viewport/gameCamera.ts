// The studio's camera against the game's (S5a4's camera check, output/s5a4_shots/camera_*): the same eye over the
// feet, the same 60 degrees of vertical field of view at the same aspect give the same picture; a view narrower than
// the game's frame must widen its field of view, or it shows a slice of the game's picture.
// The game's camera (game/indoor/IndoorRenderer.cpp, game/outdoor/OutdoorGameView.cpp): 60 degrees of vertical field
// of view at the window's aspect, which is the player's monitor (16:9 most often, the pins' pictures too).
const GAME_VERTICAL_FOV_DEGREES = 60;
const GAME_ASPECT = 16 / 9;

// The vertical field of view that shows at least the game's whole frame in a view of this aspect (S5a4's camera
// check): the game's 60 degrees in a view as wide as the game's or wider; in a narrower one (the split view's halves)
// widened until the game's width fits, or the narrow view shows a slice of the game's picture and every wall looks
// closer than in the game.
export function studioVerticalFov(viewAspect: number, gameAspect = GAME_ASPECT): number
{
    if (viewAspect >= gameAspect)
    {
        return GAME_VERTICAL_FOV_DEGREES;
    }
    const halfHeight = Math.tan((GAME_VERTICAL_FOV_DEGREES * Math.PI) / 360) * (gameAspect / viewAspect);
    return (Math.atan(halfHeight) * 360) / Math.PI;
}

// Where the game's frame lies in a view of that size (CSS pixels), centred: what the game shows at the same pose.
export function gameFrameIn(width: number, height: number, gameAspect = GAME_ASPECT): { left: number; top: number; width: number; height: number }
{
    if (width / height >= gameAspect)
    {
        const frameWidth = height * gameAspect;
        return { left: (width - frameWidth) / 2, top: 0, width: frameWidth, height };
    }
    const frameHeight = width / gameAspect;
    return { left: 0, top: (height - frameHeight) / 2, width, height: frameHeight };
}
