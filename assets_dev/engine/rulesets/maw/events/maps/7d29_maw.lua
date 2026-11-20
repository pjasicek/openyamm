-- MAW content of this map (devdocs/maw/MAPS_CONTENT.md): loaded after the world's events, for MAW games only.

-- Once the throne room guard (group 56) is slain, the Goblin King comes with his guard, once per game (§3.2).
RegisterMapTimerEvent(60001, 60, function()
    if evt.GetGlobalVar("MawGoblinKing", 0) ~= 0 or not evt.CheckMonstersKilled(ActorKillCheck.Group, 56, 0, false) then
        return
    end
    evt.SetGlobalVar("MawGoblinKing", 1)
    evt.StatusText("Noises from the throne room")
    evt.SummonMonstersById{monster = 271, x = -5110, y = 2852, z = 65, count = 1, tiers = {0, 0, 100}, radius = 64,
        group = 1, name = 300, hpScale = 3, speed = 400}
    evt.SummonMonstersById{monster = 271, x = -5122, y = 2219, z = 1, count = 2, tiers = {0, 100, 0}, radius = 128,
        group = 1, speed = 400}
    evt.SummonMonstersById{monster = 271, x = -4423, y = 1456, z = 1, count = 3, tiers = {100, 0, 0}, radius = 256,
        group = 1, speed = 400}
    evt.SummonMonstersById{monster = 271, x = -5937, y = 1456, z = 1, count = 3, tiers = {100, 0, 0}, radius = 256,
        group = 1, speed = 400}
end, "MAW Goblin King")
