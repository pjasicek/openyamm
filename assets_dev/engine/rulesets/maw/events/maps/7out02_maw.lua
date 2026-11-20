-- MAW content of this map (devdocs/maw/MAPS_CONTENT.md): loaded after the world's events, for MAW games only.

-- A goblin ambush on the southern pass, and the Goblin's Lieutenant holding the fort north of town, who calls
-- reinforcements while the party is near, at most ten times (§3.2).
RegisterMapTimerEvent(60001, 30, function()
    local x, y, z = evt.GetPartyPosition()
    if evt.GetMapVar("MawAmbush", 0) == 0 and x > 17390 and x < 19429 and y > -20015 and y < -19454 and z < 800 then
        evt.SetMapVar("MawAmbush", 1)
        evt.StatusText("It's an ambush!")
        evt.SummonMonstersById{monster = 271, x = 19613, y = -17760, z = 1595, count = 2, tiers = {60, 30, 10},
            radius = 64, group = 1}
        evt.SummonMonstersById{monster = 271, x = 19307, y = -18344, z = 1568, count = 2, tiers = {60, 30, 10},
            radius = 64, group = 1}
        evt.SummonMonstersById{monster = 271, x = 18344, y = -18861, z = 1666, count = 2, tiers = {60, 30, 10},
            radius = 64, group = 1}
        evt.SummonMonstersById{monster = 271, x = 16201, y = -21635, z = 3022, count = 8, tiers = {60, 30, 10},
            radius = 1400, group = 1}
    end
end, "MAW ambush")

RegisterMapOnLoadEvent(60002, "MAW lieutenant", function()
    if evt.GetMapVar("MawLieutenant", 0) == 0 then
        evt.SetMapVar("MawLieutenant", 1)
        evt.SummonMonstersById{monster = 106, x = 8200, y = 4098, z = 385, count = 1, tiers = {100, 0, 0}, radius = 0,
            group = 1, name = 301, hpScale = 3, speed = 0}
    end
end)

RegisterMapTimerEvent(60003, 300, function()
    local x, y, z = evt.GetPartyPosition()
    local waves = evt.GetMapVar("MawReinforcements", 0)
    if waves >= 10 or evt.CheckMonstersKilled(ActorKillCheck.UniqueNameId, 301, 0, false)
        or (x - 8200) ^ 2 + (y - 4098) ^ 2 + (z - 385) ^ 2 >= 2000 ^ 2 then
        return
    end
    evt.SetMapVar("MawReinforcements", waves + 1)
    evt.StatusText("Goblin Reinforcements")
    evt.SummonMonstersById{monster = 271, x = 6613, y = 2546, z = 122, count = 1, tiers = {60, 30, 10}, radius = 64,
        group = 1}
    evt.SummonMonstersById{monster = 271, x = 6601, y = 5690, z = 122, count = 1, tiers = {60, 30, 10}, radius = 64,
        group = 1}
    evt.SummonMonstersById{monster = 271, x = 9765, y = 2500, z = 122, count = 2, tiers = {60, 30, 10}, radius = 64,
        group = 1}
end, "MAW reinforcements")
