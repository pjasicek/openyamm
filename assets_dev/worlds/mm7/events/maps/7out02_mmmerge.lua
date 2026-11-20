-- MMMerge supplement: Harmondale outdoor castle, judge, invasion, and scavenger repairs.

AppendMapEvent(37, function()
    MM7.RemoveJudgeFollowers()
end)

ReplaceMapEvent(301, "Enter Castle Harmondale", function()
    MM7.EnterCastleHarmondaleOutdoor()
end, "Enter Castle Harmondale")

RegisterMapOnLoadEvent(65002, "MMMerge Harmondale judge and invasion state", function()
    MM7.UpdateHarmondaleInvasion()
    MM7.UpdateJudgeGreyDeath()
end)

RegisterMapTimerEvent(65003, 180, function()
    MM7.GiveScavengerAdvertisementIfNear(-13115, 12497, true)
end, "MMMerge Harmondale scavenger advertisement")

-- The dimensional travel pedestal and its orb (../../maps/7out02_dimensional_travel.scene.yml): the four continents'
-- portals.
RegisterEvent(1777, "Dimensional Travel", function()
    evt.OpenDimensionDoor()
end, "Dimensional Travel")
