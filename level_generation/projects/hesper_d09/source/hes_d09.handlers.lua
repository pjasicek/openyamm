-- Authored D9 events; the shared builder supplies DOORS and the registrations.
local handlers = {}
SetMapMetadata({onLoad = {}, onLeave = {5}, timers = {{eventId = 3, repeating = true, intervalGameMinutes = 0.5}}})
local DONE, GIVEN, NULL_MET = 100011, 100211, 100530
local INVISIBLE = MonsterBits.Invisible
local ACTORS = {D9_ACTORS, }
local EXIT = {D9_EXIT, }
local closing = {}

local function spellPoints()
    -- EVT exposes comparison, not a per-character getter: reconstruct the exact nonnegative 32-bit value.
    local value = 0
    for bit = 30, 0, -1 do
        local candidate = value + 2 ^ bit
        if evt.Cmp(VarTag.CurrentSpellPoints, candidate) then value = candidate end
    end
    return value
end

local function drain(store)
    for player = 0, evt.GetPartyMemberCount() - 1 do
        evt.ForPlayer(player)
        if store then evt.SetMapVar('sp' .. (player + 1), spellPoints()) end
        evt.Set(VarTag.CurrentSpellPoints, 0)
    end
    evt.ForPlayer(PartySelector.Current)
end

local function hideVat(index)
    evt.SetFacetBit(169 + index, FacetBits.Invisible + FacetBits.Untouchable, 1)
end

handlers[2] = function()
    if not IsQBitSet(QBit(NULL_MET)) then
        SetQBit(QBit(NULL_MET))
        SetAutonote(10230)
        SetAutonote(10231)
    end
end

handlers[1] = function()
    drain(evt.GetMapVar('null_on') == 0)
    evt.SetMapVar('null_on', 1)
    handlers[2]()
    for index = 1, 3 do
        if IsAtLeast(MapVar(index + 1), 1) then hideVat(index) end
        local revealed = evt.GetMapVar('wave' .. index) == 1
        evt.SetMonGroupBit(27 + index, INVISIBLE, revealed and 0 or 1)
        if revealed then evt.SetDoorState(index == 3 and 67 or 66, 0) end
    end
    for _, actor in ipairs(ACTORS) do evt.SetActorBehavior(actor.index, actor.behavior) end
    if IsQBitSet(QBit(DONE)) then
        evt.SetLight(3, 0)
        evt.SetDoorState(51, 0)
        for group = 24, 30 do evt.SetMonGroupBit(group, INVISIBLE, 1) end
    end
end

handlers[5] = function()
    if evt.GetMapVar('null_on') == 0 then return end
    for player = 0, evt.GetPartyMemberCount() - 1 do
        evt.ForPlayer(player)
        evt.Set(VarTag.CurrentSpellPoints, evt.GetMapVar('sp' .. (player + 1)))
    end
    evt.ForPlayer(PartySelector.Current)
    evt.SetMapVar('null_on', 0)
end

handlers[3] = function()
    drain(false)
    for door, seconds in pairs(closing) do
        closing[door] = seconds - 1
        if seconds <= 1 then evt.SetDoorState(door, 1); closing[door] = nil end
    end
    if not IsQBitSet(QBit(DONE)) then
        for index = 1, 3 do
            if evt.GetMapVar('wave' .. index) == 0 and evt.CheckMonstersKilled(1, 24 + index, 0, 0) then
                handlers[151 + index]()
            end
        end
        if evt.CheckMonstersKilled(1, 24, 0, 0) then handlers[151]() end
    end
end

handlers[10] = function()
    evt.SimpleMessage("Scratched on the crate lid. 'Magic does not work down here. Do not bother. We left what we "
        .. "couldn't carry: Stims, cells, one grenade, the burst cell. Kill the egg clusters before they open. "
        .. "Hale went back up to the farm for help. We wait here for him. - Marek's third party.'")
end
handlers[11] = function()
    if evt.GetMapVar('null_text') ~= 0 then return end
    evt.SetMapVar('null_text', 1)
    evt.StatusText("The relay hisses and goes dead. A pressure settles behind your eyes; reaching for a spell "
        .. "is like reaching for a word you have forgotten. Nothing comes.")
end

for event = 30, 37 do
    local chest = event - 30
    handlers[event] = function()
        if chest == 0 and not IsAtLeast(MapVar(3), 1) then
            evt.StatusText('The pod is sealed in the middle vat.')
        elseif chest == 1 and not IsQBitSet(QBit(DONE)) then
            evt.StatusText("The cradle's bone is shut tight round something that glows.")
        else
            evt.OpenChest(chest)
        end
    end
end

handlers[50] = function()
    if not EXIT.x then
        evt.StatusText('The membrane mouth: the way is not yet open.')
        return
    end
    evt.MoveToMap(EXIT.x, EXIT.y, EXIT.z, EXIT.direction, 0, 0, 0, 0, 'hes_out3.odm')
end
handlers[51] = function()
    if IsQBitSet(QBit(DONE)) then evt.SetDoorState(51, 0)
    else evt.StatusText('The membrane pulses with her heartbeat. It will not part while she lives.') end
end
for event = 53, 65 do
    local door = event
    handlers[event] = function()
        evt.SetDoorState(door, 2)
        closing[door] = 10
        if door == 65 and evt.GetMapVar('mother_entered') == 0 then
            evt.SetMapVar('mother_entered', 1)
            evt.StatusText('The chamber shudders. Something vast stirs in the resin cradle, and three swollen sacs '
                .. 'on its flanks pulse with light.')
        end
    end
end

local vats = {{6600, 3300}, {7000, 4200}, {6300, 4200}}
for index = 1, 3 do
    handlers[69 + index] = function()
        if IsAtLeast(MapVar(index + 1), 1) then return end
        SetValue(MapVar(index + 1), 1)
        hideVat(index)
        if index == 2 then
            evt.StatusText('The sac splits. Something dark and heavy slides out with the sediment: a gland, '
                .. 'still warm, in a resin pod.')
        else
            local x, y, z = evt.GetPartyPosition()
            if (x - vats[index][1]) ^ 2 + (y - vats[index][2]) ^ 2 <= 200 ^ 2 and math.abs(z) < 200 then
                evt.DamagePlayer(PartySelector.All, Damage.Body, math.random(1, 6) + math.random(1, 6))
            end
            evt.StatusText('The sac splits. Acid spills across the floor, and nothing else.')
        end
    end
end

handlers[73] = function() evt.SetDoorState(52, 2) end
handlers[74] = function() evt.SetDoorState(52, 2) end
handlers[151] = function()
    if IsQBitSet(QBit(DONE)) then return end
    SetQBit(QBit(DONE))
    ClearQBit(QBit(GIVEN))
    SetAutonote(10232)
    evt.SetLight(3, 0)
    evt.SetDoorState(51, 0)
    evt.StatusText('The Mother sags in her cradle, and the pulsing in the walls slows, and stops. Among the spilled '
        .. 'eggs something glints: a shard of white and gold.')
end
for index = 1, 3 do
    handlers[151 + index] = function()
        if evt.GetMapVar('wave' .. index) ~= 0 then return end
        evt.SetMapVar('wave' .. index, 1)
        evt.SetMonGroupBit(27 + index, INVISIBLE, 0)
        evt.SetDoorState(index == 3 and 67 or 66, 0)
        evt.StatusText('The Mother shrieks. Somewhere above, eggs answer.')
    end
end

RegisterEvent(3, "Brood heartbeat", handlers[3])
RegisterEvent(5, "Leave null field", handlers[5])

-- GetCurrentMapName returns the display title; use this dungeon's H3 treasure level explicitly.
HesperPickups.setup({treasure = 6,
    canisters = {}, vats = {701, 702, 703, 704, 705, 706, 707, 708},
    satchels = {}, bundles = {751, 752, 753, 754, 755, 756, 757, 758, 759, 760, 761, 762, 763, 764, 765, 766, 767, 768, 769, 770},
})
