-- MAW content of this map (devdocs/maw/MAPS_CONTENT.md): loaded after the world's events, for MAW games only.

-- The stat shrine prays in any month, while The Seer's Pilgrimage has not been paid out (MAPS_CONTENT.md §3.1).
ReplaceMapEvent(261, "Shrine of Luck", function()
    if not IsQBitSet(QBit(1230)) then -- NPC
        SetQBit(QBit(1230)) -- NPC
        if not IsQBitSet(QBit(1237)) then -- NPC
            SetQBit(QBit(1237)) -- NPC
            evt.ForPlayer(Players.All)
            AddValue(BaseLuck, 10)
            evt.StatusText("+10 Luck permanent")
            return
        end
        evt.ForPlayer(Players.All)
        AddValue(BaseLuck, 3)
        evt.StatusText("+3 Luck permanent")
        return
    end
    evt.StatusText("You pray at the shrine.")
end, "Shrine of Luck")

-- The road to Dragonsand: Doom and the modes after it arrive at the other end of the desert (Maps/oute3.lua:118-125).
ReplaceMapEvent(104, nil, function()
    local mode = evt.RulesetInfo().challengeMode
    if mode == "doom" or mode == "road_to_insanity" or mode == "beyond_madness" then
        evt.MoveToMap(-9477, -13062, 129, 0, 0, 0, 0, 0, "outb3.odm") -- Dragonsand
        return
    end
    evt.MoveToMap(12808, 6832, 64, 512, 0, 0, 0, 0, "outb3.odm") -- Dragonsand
end)
