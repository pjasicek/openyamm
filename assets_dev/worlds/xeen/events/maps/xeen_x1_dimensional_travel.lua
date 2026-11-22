-- Vertigo's dimensional travel pedestal (../../maps/xeen_x1_dimensional_travel.scene.yml), in every ruleset, as the
-- other continents' start towns have (event 1777; Sturmford City's 250). Hand-written beside the Map Studio project's
-- generated xeen_x1.lua. It opens the continents' portals; the others' pedestals land here
-- (worlds/xeen/data_tables/dimension_doors.yml).
RegisterEvent(1777, "Dimensional Travel", function()
    evt.OpenDimensionDoor()
end, "Dimensional Travel")
