-- MMMerge supplement: arena exit returns to the active merged continent.

ReplaceMapEvent(501, "Leave the Arena", function()
    local continent = CurrentContinent()

    if continent == 2 then
        evt.MoveToMap(-5692, 11137, 1, 1024, 0, 0, 0, 8, "7out02.odm")
    elseif continent == 3 then
        evt.MoveToMap(14305, 2696, 96, 1432, 0, 0, 0, 8, "outd3.odm")
    else
        evt.MoveToMap(17091, -12524, 1, 1024, 0, 0, 0, 8, "out02.odm")
    end
end, "Leave the Arena")
SetMapContextAction(501, {kind = "leave_dungeon", source = "authored", targetName = "Leave the Arena"})
