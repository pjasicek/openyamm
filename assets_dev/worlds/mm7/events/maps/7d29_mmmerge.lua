-- MMMerge supplement: Castle Harmondale local quest state.

-- The courtyard water (../../maps/7d29_dimension_travel.scene.yml) opens the dimensional travel, as in MMerge (without
-- its Verdant quest gate; the user, 2026-11-09).
RegisterEvent(65031, "Dimensional travel", function()
    evt.OpenDimensionDoor()
end, "Dimensional travel")
evt.meta.map.contextActions[65031] = {kind = "teleport", targetName = "Dimensional travel"}

RegisterMapOnLoadEvent(65032, "Castle Harmondale dimensional travel water", function()
    -- Saved face attributes also need the courtyard water's new click binding.
    evt.SetFacetBit(65031, FaceAttribute.Clickable, true)
end)

AppendMapEvent(376, function()
    MM7.RemoveGolemFollowerIfConstructed()
end)

RemoveMapEvent(377)
RegisterMapOnLoadEvent(377, "MMMerge Harmondale mercenary invasion state", function()
    MM7.HideCastleHarmondaleGoblinsIfRebuilt()
    MM7.UpdateCastleHarmondaleMercenariesOnLoad()
end)

RegisterMapOnLeaveEvent(65029, "MMMerge Harmondale mercenary completion", function()
    MM7.MarkCastleHarmondaleMercenariesKilledIfClear()
end)

RegisterRestFoodCostHook(65030, "MMMerge Castle Harmondale free rest", function(context)
    MM7.MakeCastleHarmondaleRestFreeIfRebuilt(context)
end)
