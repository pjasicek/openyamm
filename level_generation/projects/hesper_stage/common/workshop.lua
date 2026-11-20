-- The Workshop (design/kreegan_world/ITEMS.md "Workshop mods"; the world's workshop_mods table): Orrin's topics fit a
-- mod to the first item the active character wears that it suits (evt.FitWorkshopMod: weapons first, then body
-- pieces), for gold and salvage, known in advance; another fit replaces the old mod. Two mods are there from the start,
-- two after three of the world's major objectives (QBITS.md "Derived values").

HesperWorkshop = HesperWorkshop or {}

local OBJECTIVES = {100040, 100041, 100042, 100043, 100009, 100010, 100014, 100018, 100019, 100020, 100021, 100011}

local function objectivesDone()
    local done = 0
    for _, qbit in ipairs(OBJECTIVES) do
        if IsQBitSet(QBit(qbit)) then
            done = done + 1
        end
    end
    return done
end

-- mod: {id, name, gold, salvage = item id, count, objectives = needed, what = the piece's kind for the message}.
function HesperWorkshop.fit(mod)
    if objectivesDone() < mod.objectives then
        evt.SetMessage("Not yet. I need parts the devils still guard: come back when they've lost a few more fights.")
        return
    end
    local player = evt.GetCurrentPlayerIndex()
    if evt.CanFitWorkshopMod(player, mod.id) == 0 then
        evt.SetMessage("Nothing you're wearing takes " .. mod.name .. ". It goes on " .. mod.what .. ".")
        return
    end
    if not IsAtLeast(Gold, mod.gold) then
        evt.SetMessage(mod.name .. " is " .. mod.gold .. " gold and " .. mod.count .. " " .. mod.salvageName
            .. ". You're short of gold.")
        return
    end
    local carried = 0
    for member = 0, evt.GetPartyMemberCount() - 1 do
        carried = carried + evt.PartyMemberItemCount(member, mod.salvage)
    end
    if carried < mod.count then
        evt.SetMessage(mod.name .. " is " .. mod.gold .. " gold and " .. mod.count .. " " .. mod.salvageName
            .. ". You're short of salvage.")
        return
    end
    SubtractValue(Gold, mod.gold)
    for _ = 1, mod.count do
        evt.RemoveItems(mod.salvage)
    end
    evt.FitWorkshopMod(player, mod.id)
    evt.PlaySoundName("cell_charger")
    evt.SetMessage("The fabricator hums, and it's done: " .. mod.name .. ". If it had another mod, that one's gone.")
end

-- The Workshop buys salvage at full value (ITEMS "The economy check"): every Kreegan Alloy (11350, 400) and Ion Cell
-- (11351, 600) the party carries.
function HesperWorkshop.buySalvage()
    local total = 0
    for _, salvage in ipairs({{11350, 400}, {11351, 600}}) do
        for member = 0, evt.GetPartyMemberCount() - 1 do
            for _ = 1, evt.PartyMemberItemCount(member, salvage[1]) do
                evt.RemoveItems(salvage[1])
                total = total + salvage[2]
            end
        end
    end
    if total == 0 then
        evt.SetMessage("No alloy, no cells. Bring me what you cut off them and I pay full weight.")
        return
    end
    AddValue(Gold, total)
    evt.SetMessage("Full weight, as promised: " .. total .. " gold.")
end
