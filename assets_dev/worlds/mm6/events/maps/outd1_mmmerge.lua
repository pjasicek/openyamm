-- MMMerge map supplement: Mire of the Damned local outdoor state.

-- MMMerge Scripts/Maps/outd1.lua: this map's own hostile.txt cells (faction numbers, 0 is the party).
SetLocalFactionRelations({
    {211, 0, 0},
    {211, 173, 2},
    {211, 181, 2},
    {173, 211, 1},
    {181, 211, 1},
})

RegisterMapOnLoadEvent(65027, "MMMerge outd1 town portal", function()
    SetQBit(QBit(314)) -- Silver Cove town portal destination discovered.
    MM6.ApplyDragonTowerState(1182, 117, 42)
end)

table.insert(evt.meta.map.textureNames, "t1swbu")

ReplaceMapEvent(10, "Abdul's Discount Travel", function()
    evt.EnterHouse(475)
end, "Abdul's Discount Travel")

ReplaceMapEvent(11, "Abdul's Discount Travel", function()
    evt.EnterHouse(475)
end, "Abdul's Discount Travel")

MM6.RegisterDragonTowerTimer(209, 11032, -8940, 2830, 1182)

ReplaceMapEvent(210, "Dragon Tower", function()
    MM6.TryDisableDragonTower(1182, 117, 42)
end)
