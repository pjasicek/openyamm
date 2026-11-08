-- MMMerge map supplement: Celeste post-Light hostile guards.

RegisterMapOnLoadEvent(65025, "MMMerge 7d25 post-Light hostility", function()
    if IsQBitSet(QBit(612)) then -- Chose the path of Dark.
        evt.SetMonGroupBit(57, MonsterBits.Hostile, true)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, true)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, true)
    end
end)

-- Falling off Celeste (the "sky floor", event 451): the party drops into the Bracada Desert sky at one of six points
-- at z 3700 and falls, without the leave-the-dungeon question: the original's MoveToMap has neither house nor icon, and
-- the first point picked is the one used (OpenEnroth EvtInterpreter's d25 451 fix; its "0" first point means
-- Bracada too). The generated event ran every later MoveToMap after the picked one and asked to leave.
local CelesteFallPoints = {
    {8146, 4379}, {-2815, 1288}, {-11883, 8667}, {-22231, 13145}, {-12770, 18344}, {9185, 18564},
}

ReplaceMapEvent(451, nil, function()
    local point = CelesteFallPoints[PickRandomOption(451, 1, {1, 2, 3, 4, 5, 6})]
    evt.MoveToMap(point[1], point[2], 3700, 0, 0, 0, 0, 0, "7out06.odm", {direct = true, keepHeight = true})
end)
