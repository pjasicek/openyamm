-- MAW content of this map (devdocs/maw/MAPS_CONTENT.md): loaded after the world's events, for MAW games only.

-- The secret button and door 452 to the Nightshade Brazier need the Brazier quest (QBit 28), not Dyson Leyland in the
-- party; during a dimension-map run they need neither, and the clerics fight (Maps/d22.lua:11-45, §3.3).
ReplaceMapEvent(5, nil, function()
    local dimensionRun = evt.RulesetInfo().dimensionRun

    if dimensionRun or IsQBitSet(QBit(19)) then -- Allied with Necromancers Guild. Steal Nightshade Brazier done.
        evt.SetMonGroupBit(39, MonsterBits.Hostile, 1) -- actor group 39: spawn Cleric (human male) A
        evt.SetMonGroupBit(40, MonsterBits.Hostile, 1) -- actor group 40: spawn Cleric (human male) A
    elseif IsQBitSet(QBit(230)) then -- You have Pissed off the clerics
        if IsAtLeast(Counter(8), 1344) then
            evt.SetMonGroupBit(39, MonsterBits.Hostile, 0) -- actor group 39: spawn Cleric (human male) A
            evt.SetMonGroupBit(40, MonsterBits.Hostile, 0) -- actor group 40: spawn Cleric (human male) A
            ClearQBit(QBit(230)) -- You have Pissed off the clerics
        else
            evt.SetMonGroupBit(39, MonsterBits.Hostile, 1) -- actor group 39: spawn Cleric (human male) A
            evt.SetMonGroupBit(40, MonsterBits.Hostile, 1) -- actor group 40: spawn Cleric (human male) A
        end
    end

    -- QBit 28: Bring the Nightshade Brazier to the Necromancers' Guild leader, Sandro.
    evt.SetFacetBit(5, FacetBits.IsSecret, (dimensionRun or IsQBitSet(QBit(28))) and 1 or 0)
end)
-- Replacing an event drops it from the load list; 5 is d22's load event.
AppendMapOnLoadEvent(5)

ReplaceMapEvent(452, nil, function()
    if evt.RulesetInfo().dimensionRun or IsQBitSet(QBit(28)) then
        evt.SetDoorState(1, DoorAction.Open)
    end
end)
