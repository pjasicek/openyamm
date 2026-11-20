-- Authored Seedship events. The build substitutes stable actor indices and the outdoor arrival record.
local handlers = {}
SetMapMetadata({onLoad = {1}, onLeave = {}, timers = {
    {eventId = 3, intervalGameMinutes = 0.5, repeating = true},
    {eventId = 4, intervalGameMinutes = 0.75, repeating = true}}})
local ACTORS = {D11_ACTORS, }
local EXIT = {D11_EXIT, }
local function bit(id) return IsQBitSet(QBit(id)) end
local function attachBehaviors()
    for _, actor in ipairs(ACTORS) do
        -- Hidden actors still receive behaviour updates; arm only the chosen boss form.
        local boss = actor.group == 25 or actor.group == 26
        if not boss or (not bit(100031) and bit(actor.group == 25 and 100029 or 100030)) then
            evt.SetActorBehavior(actor.index, actor.behavior)
        end
    end
end
local function nerve(group, on)
    evt.SetLight(group, on and 1 or 0)
    evt.SetSprite(120 + group, 1, on and 'hes_d11_nerve_node' or 'hes_d11_nerve_node_off')
end
local function brainDead()
    evt.SetTexture(155, 'hsbraind')
    evt.SetLight(5, 0)
    nerve(21, false); nerve(22, false)
    evt.SetDoorState(53, 0); evt.SetDoorState(54, 0)
end
local function rewards()
    evt.SetDoorState(51, 0); evt.SetDoorState(52, 0); evt.SetDoorState(552, 0)
    evt.SetSprite(131, 1, 'hes_kreegan_pod_chest')
end
handlers[2] = function() SetAutonote(10240) end
handlers[1] = function()
    handlers[2]()
    attachBehaviors()
    for k = 1, 4 do
        local cut = bit(100013) or IsAtLeast(MapVar(10 + k), 1)
        evt.SetLight(10 + k, cut and 0 or 1)
        if cut then evt.SetMonGroupBit(5 + k, MonsterBits.Invisible, 1) end
    end
    evt.SetMonGroupBit(25, MonsterBits.Invisible, bit(100029) and not bit(100031) and 0 or 1)
    evt.SetMonGroupBit(26, MonsterBits.Invisible, bit(100030) and not bit(100031) and 0 or 1)
    evt.SetSprite(131, bit(100031) and 1 or 0, 'hes_kreegan_pod_chest')
    if bit(100013) then brainDead() else evt.SetLight(5, 1); nerve(21,true); nerve(22,false) end
    if bit(100031) then rewards() end
end
for k = 1, 4 do
    handlers[150 + k] = function()
        if IsAtLeast(MapVar(10 + k), 1) then return end
        SetValue(MapVar(10 + k), 1)
        evt.SetLight(10 + k, 0)
        evt.PlaySoundName('d11_convulsion')
    end
end
handlers[155] = function()
    if bit(100013) then return end
    SetQBit(QBit(100013)); ClearQBit(QBit(100213)); SetAutonote(10242)
    brainDead()
    evt.StatusText("The last ganglion bursts. The magenta light runs out of the brain's folds like water from a cloth, "
        .. 'and the whole ship shudders. The heartbeat falters, then goes on, slower. The Seedship is blind.')
end
handlers[156] = function()
    if bit(100031) then return end
    SetQBit(QBit(100031)); SetAutonote(10243); rewards()
    -- His voiced death, by the terms (design/kreegan_world/audio/BOSS_LINES.md).
    evt.StatusText(bit(100029) and 'Lord Vhorrax: Take the blade. Tell the Hierarch I kept my word.'
        or 'Lord Vhorrax: Vermin ... win ... by numbers. As we ... did.')
    evt.PlaySoundName(bit(100029) and 'vo_vhorrax_death_terms' or 'vo_vhorrax_death')
end
handlers[3] = function()
    for door = 201, 222 do
        local key = 'd11_close_' .. door
        local seconds = evt.GetMapVar(key)
        if seconds > 0 then
            evt.SetMapVar(key, seconds - 1)
            if seconds == 1 then evt.SetDoorState(door, 1) end
        end
    end
    local living = 0
    for k = 1, 4 do
        if not IsAtLeast(MapVar(10 + k), 1) and not bit(100013) then
            if evt.CheckMonstersKilled(1, 5 + k, 0, 0) then handlers[150 + k]() else living = living + 1 end
        end
    end
    if living == 0 and not bit(100013) then handlers[155]() end
    local tick = evt.GetMapVar('d11_tick') + 1
    evt.SetMapVar('d11_tick', tick % 12)
    if tick % 3 == 0 and living > 0 then
        local x, y, z = evt.GetPartyPosition()
        if x >= 704 and x <= 2896 and y >= 3864 and y <= 7464 then
            for player = 0, evt.GetPartyMemberCount() - 1 do
                if not evt.PartyMemberHasEquippedItem(player, 11106) and not evt.PartyMemberHasEquippedItem(player, 11107) then
                    evt.DamagePlayer(player, Damage.Body, (math.random(1,6) + math.random(1,6)) * living)
                end
            end
            evt.StatusText('The spores burn in your throat.')
        end
    end
    if tick % (bit(100013) and 4 or 2) == 0 then evt.PlaySoundName('d11_heartbeat') end
    if living > 0 and tick % 3 == 0 then evt.PlaySoundName('d11_hum' .. living, 1800, 5600, 1800) end
    if not bit(100031) and ((bit(100029) and evt.CheckMonstersKilled(1,25,0,0))
        or (bit(100030) and evt.CheckMonstersKilled(1,26,0,0))) then handlers[156]() end
end
handlers[4] = function()
    if bit(100013) then return end
    local port = evt.GetMapVar('d11_breath') == 0
    evt.SetMapVar('d11_breath', port and 1 or 0)
    nerve(21,port); nerve(22,not port)
end
handlers[10] = function()
    if evt.GetMapVar('d11_relay') == 1 then return end
    evt.SetMapVar('d11_relay', 1)
    evt.StatusText("The relay crackles once; the bone swallows Aster's voice.")
end
handlers[11] = function()
    evt.SimpleMessage("A Noble's sigil, gilded, with a line beneath: the ship will carry my house to the world that killed "
        .. "the Comet's brood. A comet and a blade.")
end
handlers[12] = function()
    evt.SimpleMessage(bit(100013) and 'The eye-stalks hang slack. Whatever they were looking for, the ship cannot see it now.'
        or "Through the membrane the storm, the spires, and above them the sky. The eye-stalks turn, all together, "
        .. 'to one point of the sky, and hold.')
end
local function grant(ids)
    for _, id in ipairs(ids) do evt.GiveItem(id) end
end
handlers[30] = function()
    if not bit(100031) then evt.StatusText('Its owner still lives.'); return end
    if IsAtLeast(MapVar(15),1) then evt.StatusText('Empty.'); return end
    grant({bit(100029) and 11421 or 11332,11331,11331,11377}); SetValue(MapVar(15),1)
end
handlers[31] = function()
    if not bit(100031) then return end
    if IsAtLeast(MapVar(16),1) then evt.StatusText('Empty.'); return end
    grant({11480,11332,11482})
    if bit(100029) then AddValue(VarTag.Gold,50000) end
    SetValue(MapVar(16),1)
end
for event = 32, 38 do
    local chest = event - 32
    handlers[event] = function() evt.OpenChest(chest) end
end
handlers[50] = function()
    if not EXIT.x then evt.StatusText('The hull breach: the way is not yet open.'); return end
    evt.MoveToMap(EXIT.x,EXIT.y,EXIT.z,EXIT.direction,0,0,0,0,'hes_out3.odm')
end
for event = 51, 54 do
    local door = event
    handlers[event] = function()
        if bit(door <= 52 and 100031 or 100013) then
            evt.SetDoorState(door,0)
            if door == 52 then evt.SetDoorState(552,0) end
        else evt.StatusText(door <= 52 and "Sealed with a Noble's sigil. Its owner still lives."
            or 'The nerve membrane is taut and throbbing. Something in this ship still commands it.') end
    end
end
handlers[160] = function(step)
    if bit(100029) or bit(100030) or bit(100031) then return end
    if step == 1 or step == 2 then
        local honour = step == 1
        SetQBit(QBit(honour and 100029 or 100030))
        evt.SetMonGroupBit(honour and 25 or 26, MonsterBits.Invisible, 0)
        attachBehaviors()
        evt.StatusText(honour and 'Then we are civilized, you and I. Begin.'
            or 'Pity. Then you are vermin, and vermin are swarmed. Overseers!')
        return
    end
    if step == 3 then evt.StatusText('Go, then. The terms keep. I do not.'); return end
    -- His voiced first sight, if D5 did not play it (QBit 100540, shared with hes_d05.handlers.lua).
    if not bit(100540) then
        SetQBit(QBit(100540))
        evt.StatusText('Lord Vhorrax: You are far from your dirt, little colonists.')
        evt.PlaySoundName('vo_vhorrax_sight')
    end
    local greeting = bit(100028) and 'Colonists. You came. Good: I hate to be disappointed. '
        or 'You are far from your dirt, little colonists. Further than you know. I am Vhorrax, and this is my gallery. '
    AskChoiceWithAnswerSteps(160,3,greeting .. 'Hear my terms. You and I, and no one else: no Overseer will come, '
        .. 'no hatchling will wake. If you win, my blade is yours and my purse with it. If I win, I take your heads '
        .. 'to the Hierarch and he gives me a world. Do you accept?',{{Answer='Accept',Step=1},{Answer='Refuse',Step=2}})
end
for event = 201, 222 do
    local door = event
    handlers[event] = function()
        evt.SetDoorState(door,2); evt.SetMapVar('d11_close_' .. door,10); evt.PlaySoundName('d03_membrane')
    end
end
handlers[223] = function()
    if not bit(100031) then handlers[52](); return end
    evt.MoveToMap(600,600,0,512,0,0,0,0,'hes_d11.blv')
end
RegisterMapTimerEvent(3,30,handlers[3],'Seedship state','',30)
RegisterMapTimerEvent(4,45,handlers[4],'Nerve breathing','',45)

HesperPickups.setup{
    treasure=6, -- H3: explicit loot level, as in the pickup test room.
    vats={701,702,703,704,705,706,707,708,709,710,711,712,713,714,715,716,717,718,719,720,721,722,723,724,725,726,727,728},
    bundles={751,752,753,754,755,756,757,758,759,760,761,762,763,764,765,766,767,768,769,770},
}
