-- MAW content of this map (devdocs/maw/MAPS_CONTENT.md): loaded after the world's events, for MAW games only.

-- A necromancer guards the crypt on the first visit, carrying a charged wand (§3.2).
RegisterMapOnLoadEvent(60001, "MAW necromancer", function()
    if evt.GetMapVar("MawSpawned", 0) == 0 then
        evt.SetMapVar("MawSpawned", 1)
        evt.SummonMonstersById{monster = 307, x = -25, y = 1312, z = -31, count = 1, tiers = {100, 0, 0}, radius = 0,
            group = 1, hpScale = 2.5, item = evt.RulesetInfo().bolsterLevel > 25 and 174 or 171}
    end
end)
