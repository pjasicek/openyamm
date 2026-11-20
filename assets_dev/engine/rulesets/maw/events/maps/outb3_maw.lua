-- MAW content of this map (devdocs/maw/MAPS_CONTENT.md): loaded after the world's events, for MAW games only.

-- The New World Computing hideout opens up to MAW difficulty, or to a party whose first hero has reached level 255
-- (§3.1); Doom and the modes after it close it for good (Maps/outb3.lua:56-67).
ReplaceMapEvent(92, nil, function()
    local mode = evt.RulesetInfo().challengeMode
    if mode == "doom" or mode == "road_to_insanity" or mode == "beyond_madness" then
        evt.StatusText("Access has been destroyed")
        return
    end
    evt.ForPlayer(Players.Member0)
    if evt.RulesetInfo().difficulty > 2 and not IsAtLeast(BaseLevel, 255) then
        evt.StatusText("You must prove your worth first")
        return
    end
    evt.MoveToMap(-640, 512, -416, 512, 0, 0, 0, 0, "znwc.blv") -- New World Computing
end)
