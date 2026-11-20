-- MAW content of this map (devdocs/maw/MAPS_CONTENT.md): loaded after the world's events, for MAW games only.

-- Skeleton warriors wait in the lower hall on the first visit (§3.2).
RegisterMapOnLoadEvent(60001, "MAW skeletons", function()
    if evt.GetMapVar("MawSpawned", 0) == 0 then
        evt.SetMapVar("MawSpawned", 1)
        evt.SummonMonstersById{monster = 397, x = -3954, y = 5878, z = -95, count = 3, tiers = {100, 0, 0}, radius = 64,
            group = 1}
        evt.SummonMonstersById{monster = 397, x = -3954, y = 5878, z = -95, count = 1, tiers = {0, 100, 0}, radius = 64,
            group = 1}
    end
end)
