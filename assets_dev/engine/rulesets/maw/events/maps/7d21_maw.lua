-- MAW content of this map (devdocs/maw/MAPS_CONTENT.md): loaded after the world's events, for MAW games only.

-- Troglodyte ambushes (§3.2): a trap in the northern hall, then the queen with her brood further west.
local function partyIn(minX, maxX, minY, maxY)
    local x, y = evt.GetPartyPosition()
    return x > minX and x < maxX and y > minY and y < maxY
end

RegisterMapTimerEvent(60001, 60, function()
    if evt.GetMapVar("MawAmbush", 0) == 0 and partyIn(-1183, 526, 10342, 12144) then
        evt.SetMapVar("MawAmbush", 1)
        evt.StatusText("It's a trap!")
        evt.SummonMonstersById{monster = 412, x = -3723, y = 9579, z = 1, count = 8, tiers = {70, 30, 0}, radius = 256,
            group = 1}
    end
end, "MAW ambush")

RegisterMapTimerEvent(60002, 60, function()
    if evt.GetMapVar("MawAmbush", 0) ~= 0 and evt.GetMapVar("MawQueen", 0) == 0
        and partyIn(-5321, -4316, 8514, 9882) then
        evt.SetMapVar("MawQueen", 1)
        evt.StatusText("Queen Arrived!")
        evt.SummonMonstersById{monster = 412, x = -6396, y = 6862, z = 1, count = 10, tiers = {70, 30, 0}, radius = 256,
            group = 1}
        evt.SummonMonstersById{monster = 412, x = -6396, y = 6862, z = 1, count = 1, tiers = {0, 0, 100}, radius = 256,
            group = 1, hpScale = 2}
    end
end, "MAW queen")
