-- MMMerge map supplement: Blackshire local outdoor state.

-- MMMerge Scripts/Maps/outb2.lua: this map's own hostile.txt cells (faction numbers, 0 is the party).
SetLocalFactionRelations({
    {196, 0, 0},
})

RegisterMapOnLoadEvent(65024, "MMMerge outb2 town portal and guards", function()
    SetQBit(QBit(310)) -- Blackshire town portal destination discovered.
    evt.SetMonGroupBit(39, MonsterBits.Hostile, false)
    MM6.ApplyDragonTowerState(1184, 61, 42)
end)

table.insert(evt.meta.map.textureNames, "t1swbu")

ReplaceMapEvent(10, "Blackshire Coach and Buggy", function()
    evt.EnterHouse(478)
end, "Blackshire Coach and Buggy")

ReplaceMapEvent(11, "Blackshire Coach and Buggy", function()
    evt.EnterHouse(478)
end, "Blackshire Coach and Buggy")

AppendMapEvent(68, function()
    if not HasEverOwnedItem(2119) then -- Lord Kilburn's Shield
        MM6.EnsureChestItem(1, 2119, 0, 0)
    end
end)

MM6.RegisterDragonTowerTimer(210, -17921, 9724, 2742, 1184)

ReplaceMapEvent(211, "Dragon Tower", function()
    MM6.TryDisableDragonTower(1184, 61, 42)
end)
