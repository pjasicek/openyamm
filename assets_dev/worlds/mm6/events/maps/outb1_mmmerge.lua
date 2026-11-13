-- MMMerge map supplement: Kriegspire local outdoor state.

SetMapContextAction(90, {
    kind = "enter_house",
    source = "override",
    targetMap = "6t7.blv",
    targetName = "Superior Temple of Baa",
})

ReplaceMapEvent(8, "King's Highway", function()
    evt.EnterHouse(477)
end, "King's Highway")

ReplaceMapEvent(9, "King's Highway", function()
    evt.EnterHouse(477)
end, "King's Highway")

-- The western well's dragonflies appear at fixed points in the frozen waste north of town (the original's script), so
-- the well now also moves the party into the middle of them (OY-516, the user's decision of 2026-11-13).
ReplaceMapEvent(102, "Drink from Well.", function()
    if not IsAtLeast(LevelBonus, 30) then
        SetValue(LevelBonus, 30)
        evt.StatusText("+30 Level temporary.  Look Out!")
        SetAutonote(435) -- 30 Temporary levels from the western well in the town of Kriegspire.
        evt.MoveToMap(-11900, 18750, 288, 1536, 0, 0, 0, 0)
        evt.SummonMonsters(3, 3, 2, -13280, 19696, 160, 0, 0)
        evt.SummonMonsters(3, 3, 2, -13368, 18096, 160, 0, 0)
        evt.SummonMonsters(3, 3, 2, -10976, 18152, 160, 0, 0)
        evt.SummonMonsters(3, 3, 2, -9992, 19056, 160, 0, 0)
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Well.")
