-- MMMerge supplement: Strange Temple returns to the location where Temple in a Bottle was used.

ReplaceMapEvent(501, "Leave The Strange Temple", function()
    if evt.MoveToSavedLocation("TempleInABottleReturn", true) then
        return
    end

    evt.MoveToMap(-177331, 12547, 465, 0, 0, 0, 0, 8, "out02.odm")
end, "Leave The Strange Temple")
SetMapContextAction(501, {kind = "leave_dungeon", source = "authored", targetName = "Leave The Strange Temple"})
