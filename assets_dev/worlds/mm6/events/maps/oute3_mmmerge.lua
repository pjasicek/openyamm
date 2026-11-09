-- MMMerge map supplement: New Sorpigal local outdoor state.

-- MMMerge Scripts/Maps/oute3.lua: this map's own hostile.txt cells (faction numbers, 0 is the party).
SetLocalFactionRelations({
    {185, 0, 0},
})

RegisterMapOnLoadEvent(65029, "MMMerge oute3 town portal", function()
    SetQBit(QBit(313)) -- New Sorpigal town portal destination discovered.
    MM6.ApplyDragonTowerState(1180, 84, 42)
end)

table.insert(evt.meta.map.textureNames, "t1swbu")

ReplaceMapEvent(15, "New Sorpigal Coach Company", function()
    evt.EnterHouse(470)
end, "New Sorpigal Coach Company")

ReplaceMapEvent(16, "New Sorpigal Coach Company", function()
    evt.EnterHouse(470)
end, "New Sorpigal Coach Company")

-- The northwest fountain also opens the dimensional travel, as in MMerge (without its Verdant quest gate; the user,
-- 2026-11-09), besides the town's pedestal (event 1777).
AppendMapEvent(140, function()
    evt.OpenDimensionDoor()
end)

ReplaceMapEvent(220, "Volcano", function()
    MM6.RunNewSorpigalVolcanoSequence()
end, "Volcano")

MM6.RegisterDragonTowerTimer(230, -6152, -9208, 2700, 1180)

ReplaceMapEvent(231, "Dragon Tower", function()
    MM6.TryDisableDragonTower(1180, 84, 42)
end)

-- The dimensional travel pedestal and its orb (../../maps/oute3_dimensional_travel.scene.yml): the four continents'
-- portals.
RegisterEvent(1777, "Dimensional Travel", function()
    evt.OpenDimensionDoor()
end, "Dimensional Travel")
