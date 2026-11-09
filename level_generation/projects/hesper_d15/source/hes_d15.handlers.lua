-- Authored D15 events; the shared build supplies registrations and destination records.
local handlers = {}
SetMapMetadata({onLoad = {}, onLeave = {}, timers = {{eventId = 3, repeating = true, intervalGameMinutes = 0.5}}})
local UNDER = {D15_UNDER, }
local CORE = {D15_CORE, }
local WEST = {D15_WEST, }
local EAST = {D15_EAST, }

local function move(a, map)
    evt.MoveToMap(a.x, a.y, a.z, a.direction, 0, 0, 0, 0, map)
end
local function power()
    local on = IsAtLeast(MapVar(1), 1)
    evt.SetLight(1, on and 1 or 0)
    if on then evt.SetSprite(121, 1, 'hes_d15_tunnel_lamp')
    else evt.SetSprite(121, 1, 'hes_d15_tunnel_lamp_off') end
    evt.SetTexture(210, on and 'htsignon' or 'htsign')
    evt.SetTexture(270, on and 'hcmachon' or 'hcmachine')
    evt.SetSprite(370, 1, on and 'hes_line_lever_thrown' or 'hes_line_lever')
    if on then evt.SetDoorState(7, 0) end
end
local function openLock()
    SetValue(MapVar(5), 1)
    SetValue(MapVar(3), 0)
    evt.SetDoorState(14, 0)
    evt.SetTexture(275, 'htlockon')
    evt.SetLight(2, 1)
end
handlers[2] = function()
    if evt.GetMapVar('visited') ~= 0 then return end
    evt.SetMapVar('visited', 1)
    evt.StatusText('Cold air, the smell of old water, and a darkness the lamps never reached.')
end
handlers[1] = function()
    for group = 1, 9 do evt.SetMonGroupBit(group, MonsterBits.Hostile, 1) end
    evt.SetMonGroupBit(9, MonsterBits.Invisible, evt.GetMapVar('lock_wave') == 1 and 0 or 1)
    power()
    evt.SetLight(2, IsAtLeast(MapVar(3), 1) and 1 or 0)
    if IsAtLeast(MapVar(3), 1) then evt.SetTexture(275, 'htlockon') end
    if IsAtLeast(MapVar(5), 1) then openLock() end
    handlers[2]()
end
handlers[3] = function()
    if not IsAtLeast(MapVar(3), 1) then return end
    AddValue(MapVar(4), 1)
    if IsAtLeast(MapVar(4), 30) then
        openLock()
        evt.StatusText('The ring locks home. The door before you slides up.')
    end
end
handlers[10] = function()
    evt.SimpleMessage(IsAtLeast(MapVar(1), 1) and "East terminus. Translated by the colony's engineers: Freight line, "
        .. 'west platform. The next service goes to the east terminus. One carriage in service.' or 'The board is dark.')
end
handlers[11] = function()
    evt.SimpleMessage("Junction. Translated by the colony's engineers: Crown junction. Core service lift ahead. "
        .. 'Root lock. Guardian access only.')
end
handlers[12] = function()
    evt.SimpleMessage("A digger's sigil: the soft ones' road; ours now.\n\nAster: They found this line long ago. They simply never cared where it went.")
end
handlers[13] = function()
    evt.SimpleMessage("Pale things nest in the dark of the freight line. Don't light the line unless you mean to ride it. - T.")
end
for event = 30, 35 do
    local index = event - 30
    handlers[event] = function()
        evt.ForPlayer(Players.All)
        if index == 2 and not evt.CheckSkill(const.Skills.Hacking, const.SkillCheck.Master, 1) then
            evt.StatusText('The locker wants a master hacker.'); return
        end
        evt.OpenChest(index)
    end
end
handlers[50] = function() move(UNDER, 'hes_undervault.blv') end
handlers[51] = function()
    if not CORE.x then evt.StatusText("The service lift to the Crownspire does not answer."); return end
    move(CORE, 'hes_d12.blv')
end
for event,door in pairs({[60]=4,[63]=4,[61]=6,[62]=11}) do
    handlers[event] = function() evt.SetDoorState(door, 0) end
end
for _,door in ipairs({1,2,3,5,9,10,12,13}) do
    handlers[100+door] = function() evt.SetDoorState(door, 2) end
end
handlers[70] = function()
    if IsAtLeast(MapVar(1), 1) then return end
    SetValue(MapVar(1), 1); power()
    evt.StatusText('The lever drops with a crack. Lamps flicker on along the platform; the route board wakes; '
        .. 'down the line something hums.')
end
for _,event in ipairs({72,73}) do
    handlers[event] = function(step)
        if event == 72 and not IsAtLeast(MapVar(1), 1) then evt.StatusText('LINE POWER: OFF.'); return end
        if step == 2 then return end
        if step ~= 1 then
            AskChoiceWithAnswerSteps(event, 0, 'LINE POWER ON. DESTINATION: '
                .. (event == 72 and 'EAST' or 'WEST') .. ' TERMINUS. DEPART?',
                {{Answer='Yes', Step=1}, {Answer='No', Step=2}})
            return
        end
        evt.SetDoorState(event == 72 and 7 or 8, 1)
        move(event == 72 and EAST or WEST, '0')
        evt.SetDoorState(event == 72 and 8 or 7, 0)
        evt.StatusText(event == 72 and 'The tram lurches into the dark. Lights flicker past in the tunnel walls, '
            .. 'then nothing, for a long time.' or "... and the west platform's lamps swim up out of the dark.")
    end
end
handlers[75] = function()
    if IsAtLeast(MapVar(5), 1) then return end
    if IsAtLeast(MapVar(3), 1) then evt.StatusText('The ring is still turning.'); return end
    evt.ForPlayer(Players.All)
    if not evt.CheckSkill(const.Skills.Hacking, const.SkillCheck.Grandmaster, 1) then
        evt.StatusText('The lock wants the hand that opened the bulkhead.'); return
    end
    SetValue(MapVar(3), 1); SetValue(MapVar(4), 0)
    evt.SetTexture(275, 'htlockon')
    evt.SetMapVar('lock_wave', 1)
    evt.SetMonGroupBit(9, MonsterBits.Invisible, 0)
    evt.SetLight(2, 1)
    evt.StatusText('The root lock wakes. Its glyph ring begins to turn, slowly.')
end
handlers[76] = openLock
for event = 80, 81 do
    handlers[event] = function()
        local key = 'cache' .. event
        if evt.GetMapVar(key) == 1 then evt.StatusText('The shelf is empty.'); return end
        local items = {11300,11300,11302,11302,event == 80 and 11303 or 11301}
        -- Preserve partial collection when every pack is full; a second click resumes without duplicates.
        for index = evt.GetMapVar(key .. '_taken') + 1, #items do
            if not evt.GivePartyMemberItem(0, items[index]) then
                evt.StatusText('Make room in your packs for the remaining supplies.'); return
            end
            evt.SetMapVar(key .. '_taken', index)
        end
        evt.SetMapVar(key, 1)
    end
end
RegisterEvent(3, 'Root lock clock', handlers[3])

HesperPickups.setup{
    treasure=6, -- H3: explicit loot level, as in the pickup test room.
    satchels={751,752,753,754,755,756,757,758,759,760,761,762,763,764,765,766},
    bundles={767,768,769,770},
}
