-- MMMerge map supplement: Gharik's Forge lava wall.

-- The lever also clears the lava wall in front of door 53 and puts it back on the next pull (devdocs/maw/
-- MAPS_CONTENT.md §3.1). The wall face has cog 1 from ../../maps/6d18_1.scene.yml.
local LavaWallCog = 1

ReplaceMapEvent(35, "Lever", function()
    evt.SetDoorState(43, DoorAction.Trigger)
    evt.SetDoorState(53, DoorAction.Trigger)
    local cleared = evt.GetMapVar("LavaWallCleared", 0) == 0
    evt.SetMapVar("LavaWallCleared", cleared and 1 or 0)
    evt.SetFacetBit(LavaWallCog, FacetBits.Invisible, cleared and 1 or 0)
    evt.SetFacetBit(LavaWallCog, FacetBits.Untouchable, cleared and 1 or 0)
end, "Lever")
