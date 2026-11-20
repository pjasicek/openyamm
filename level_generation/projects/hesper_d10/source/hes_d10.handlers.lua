-- Authored D10 events. Well cogs/light groups 31-34; socket lights 41-44; Founders' Hall light group 2.
local handlers = {}
local order = {2, 4, 1, 3}
local founders = {"Torvan Ek, keeper of the Archive. Year 31.", "Ilen Varo, who brought the ship down. Year 1.",
                  "The engineers who woke the Guardians. Year 40.", "Sesha Mar, who drew the Lattice. Year 12."}
SetMapMetadata({onLoad = {1}, onLeave = {}, timers = {}})

local function progress()
    for count = 4, 1, -1 do
        if IsAtLeast(MapVar(2), count) then return count end
    end
    return 0
end

local function showWells()
    local count = IsAtLeast(MapVar(1), 1) and 4 or progress()
    for i = 1, 4 do
        local on = false
        for step = 1, count do if order[step] == i then on = true end end
        evt.SetTexture(30 + i, on and "hawellon" or "hawelloff")
        evt.SetLight(30 + i, on)
        evt.SetFacetBit(50 + i, FacetBits.Invisible, not on)
    end
    evt.SetLight(2, IsAtLeast(MapVar(1), 1))
end

local function shock(dice)
    local damage = 0
    for i = 1, dice do damage = damage + evt.RandomBetween(1, 8) end
    evt.DamagePlayer(Players.All, const.Damage.Air, damage)
end

handlers[1] = function()
    showWells()
    if IsAtLeast(MapVar(1), 1) then evt.SetDoorState(DOORS.founders, DoorAction.Open) end
    evt.SetMonGroupBit(4, MonsterBits.Hostile, true)
    for i = 1, 4 do evt.SetLight(40 + i, IsQBitSet(QBit(100017 + i))) end
end
handlers[2] = function() evt.MoveToMap(ARCHIVE_RETURN, "hes_out1.odm") end
handlers[3] = function()
    if IsQBitSet(QBit(100034)) then evt.StatusText("The relay is silent.")
    elseif IsQBitSet(QBit(100103)) then evt.SimpleMessage("Thank you for bringing me home from home.")
    elseif IsAtLeast(MapVar(4), 1) then evt.SimpleMessage("The founders' Archive. Be gentle with it.")
    else
        SetValue(MapVar(4), 1)
        evt.SimpleMessage("I remember this place. I was born under this dome.")
    end
end
local plaques = {
    "Ilen Varo, who brought the ship down through fire and set the first stone. Year 1 of Hesper.",
    "Sesha Mar, who drew the Lattice to keep us. Year 12.",
    "Torvan Ek, keeper of this Archive: what we were, kept against what we fear. Year 31.",
    "To the engineers who woke the Guardians, and kept the twin away from the ship as the Ancients' words told. Year 40."
}
for i, text in ipairs(plaques) do handlers[3 + i] = function() evt.SimpleMessage(text) end end
handlers[8] = function() evt.OpenChest(0) end
handlers[9] = function() evt.OpenChest(1) end
handlers[10] = function()
    if IsAtLeast(MapVar(3), 1) then evt.StatusText("The archivist has nothing more.") return end
    if not evt.GivePartyMemberItem(0, 11487) then
        evt.StatusText("Make room for the Archive Armory Key.")
        return
    end
    SetValue(MapVar(3), 1)
    evt.StatusText("The drowned archivist still carries the Archive Armory Key.")
end
handlers[11] = function()
    if IsAtLeast(MapVar(5), 1) then return end
    shock(3)
    SetValue(MapVar(5), 10)
    evt.StatusText("The shorted shelf arcs across the water.")
end
for i = 1, 4 do
    handlers[11 + i] = function()
        if IsAtLeast(MapVar(1), 1) then evt.StatusText(founders[i]) return end
        local count = progress()
        if order[count + 1] ~= i then
            SetValue(MapVar(2), 0)
            showWells()
            shock(2)
            evt.StatusText("Static cracks; all four wells go dark.")
            return
        end
        AddValue(MapVar(2), 1)
        if count == 3 then
            SetValue(MapVar(1), 1)
            evt.SetDoorState(DOORS.founders, DoorAction.Open)
            SetAutonote(10031)
        end
        showWells()
        evt.StatusText(founders[i])
    end
end
handlers[16] = function()
    if HasItem(11487) then evt.SetDoorState(DOORS.armoury, DoorAction.Open)
    else evt.StatusText("Locked. A keyhole, and a console beside it.") end
end
handlers[17] = function()
    evt.ForPlayer(Players.All)
    if evt.CheckSkill(const.Skills.Hacking, const.SkillCheck.Master, 1) then
        evt.SetDoorState(DOORS.armoury, DoorAction.Open)
        evt.SetMonGroupBit(4, MonsterBits.Hostile, false)
        evt.StatusText("The Sentinels accept your command. The Armory opens.")
    else evt.StatusText("Archive turret controls. A Master hacker could turn the Sentinels.") end
end
-- Event 18 is retired: the Repeater and its gold are actual ground items on their shelf.
handlers[19] = function()
    evt.OpenChest(2)
    SetQBit(QBit(100103))
    ClearQBit(QBit(100223))
end
handlers[20] = function()
    SetQBit(QBit(100050))
    SetAutonote(10030)
    evt.SimpleMessage("They came on the comet's tail in the year 212. The Lattice held for nine days. When it fell, it fell to them: the Voice sang their song through our own grid. The Old Line still runs beneath the Crown, sealed with the founders' root lock. The Guardian's twin was housed away from the ship; if she wakes, she will remember the way.")
end
handlers[21] = function() evt.SetDoorState(DOORS.reading, DoorAction.Trigger) end
handlers[22] = function() evt.StatusText("Four dark wells. The founders' years will open this door.") end
handlers[23] = function()
    if IsAtLeast(MapVar(5), 1) then
        AddValue(MapVar(5), -1)
    end
    if not IsAtLeast(MapVar(5), 1) then
        local x, y, z = evt.GetPartyPosition()
        if (x - 6200)^2 + (y - 600)^2 <= 300^2 and math.abs(z) < 128 then handlers[11]() end
    end
end
RegisterEvent(11, "Shorted shelf", handlers[11])
-- Hesper advances 30 game seconds per real second. Recharge takes ten one-second ticks.
RegisterMapTimerEvent(23, 30, handlers[23], "Shelf recharge", "", 30)

-- Shared stat containers and supply satchels; placements are in pickups.json.
-- H3 is level 6; GetCurrentMapName returns the display name, not the shared lookup's filename.
HesperPickups.setup({
    treasure = 6,
    canisters = {700, 701, 702, 703, 704, 705, 706, 707, 708, 709, 710, 711},
    vats = {},
    satchels = {750, 751, 752, 753, 754, 755, 756, 757, 758, 759},
    bundles = {}
})
