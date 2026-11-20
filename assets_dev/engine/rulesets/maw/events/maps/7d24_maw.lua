-- MAW content of this map (devdocs/maw/MAPS_CONTENT.md): loaded after the world's events, for MAW games only.

-- Troglodytes swarm the party in the eastern caves, one more each minute, and after twenty minutes a Manticore
-- spellcaster comes with an Incinerate (or Fireball) scroll (§3.2).
RegisterMapTimerEvent(60001, 60, function()
    local x, y = evt.GetPartyPosition()
    if evt.GetMapVar("MawAmbush", 0) == 0 and x > -8205 and x < -7060 and y > 6216 and y < 7546 then
        evt.SetMapVar("MawAmbush", 1)
        evt.SetMapVar("MawSwarm", 20)
        evt.StatusText("Monsters swarming...")
        evt.SummonMonstersById{monster = 412, x = -7532, y = 7495, z = -1535, count = 4, tiers = {50, 35, 15},
            radius = 256, group = 1}
    end
end, "MAW swarm")

RegisterMapTimerEvent(60002, 60, function()
    local left = evt.GetMapVar("MawSwarm", 0)
    if left <= 0 then
        return
    end
    evt.SetMapVar("MawSwarm", left - 1)
    if left == 1 then
        -- The Manticore comes instead of the last troglodyte (Maps/7d24.lua:20-36).
        evt.SummonMonstersById{monster = 296, x = -7532, y = 7495, z = -1535, count = 1, tiers = {0, 100, 0},
            radius = 256, group = 1, hpScale = 2.5, speed = 400,
            item = evt.RulesetInfo().bolsterLevel > 25 and 410 or 405}
        return
    end
    evt.SummonMonstersById{monster = 412, x = -7532, y = 7495, z = -1535, count = 1, tiers = {50, 35, 15},
        radius = 256, group = 1}
end, "MAW swarm")
