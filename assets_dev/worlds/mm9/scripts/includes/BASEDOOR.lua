-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BASEDOOR.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 17, path = "AIGlobals.inc" }

-- BaseDoor.inc
-- Jeff Leggett
-- 09/26/2001
-- Basic door handling...
-- if we hit a door that is closed, we stop, trigger it to open,
-- start walking again.... if we have a target, we will head
-- towards that target, otherwise, we'll just go forward...
script.labels["BD_DoorOpen"] = function(ctx)
    -- BASEDOOR.inc:27
    ctx:state().g_bDoorOpening = false -- BASEDOOR.inc:29
    ctx:self():resumeWait(-1) -- BASEDOOR.inc:31
    ctx:state().g_hObject = ctx:self():target() -- BASEDOOR.inc:33
    if ctx:condition("g_hObject==NULL") then -- BASEDOOR.inc:35
        if ctx:condition("g_bWasRunning==TRUE") then -- BASEDOOR.inc:36
            ctx:self():run() -- BASEDOOR.inc:37
        else -- BASEDOOR.inc:38
            ctx:self():walk() -- BASEDOOR.inc:39
        end -- BASEDOOR.inc:40
    else -- BASEDOOR.inc:41
        if ctx:condition("g_bWasRunning==TRUE") then -- BASEDOOR.inc:42
            ctx:self():runTo(ctx:object("g_hObject")) -- BASEDOOR.inc:43
        else -- BASEDOOR.inc:44
            ctx:self():walkTo(ctx:object("g_hObject")) -- BASEDOOR.inc:45
        end -- BASEDOOR.inc:46
    end -- BASEDOOR.inc:47
    ctx:restorePath() -- BASEDOOR.inc:49
    do return ctx:exit("") end -- BASEDOOR.inc:51
end

script.labels["BD_OnDoor"] = function(ctx)
    -- BASEDOOR.inc:54
    -- Params:
    -- p0		- hDoor
    -- p1-3	- Normal
    -- Return Value:
    -- g_bDoorOpening	is set to TRUE if we actually are opening
    -- the door...
    ctx:state().g_bDoorOpening = false -- BASEDOOR.inc:67
    ctx:getParam(0, "g_hDoor") -- BASEDOOR.inc:69
    ctx:state().g_bTemp = ctx:object("g_hDoor"):getStat("IsClosed") -- BASEDOOR.inc:70
    if ctx:condition("g_bTemp==FALSE") then -- BASEDOOR.inc:72
        -- door is not closed, ignore....
        do return ctx:exit("FALSE") end -- BASEDOOR.inc:74
    end -- BASEDOOR.inc:75
    ctx:state().g_bWasWalking = ctx:self():getStat("IsWalking") -- BASEDOOR.inc:77
    ctx:state().g_bWasRunning = ctx:self():getStat("IsRunning") -- BASEDOOR.inc:78
    if ctx:condition("g_bWasRunning==FALSE") then -- BASEDOOR.inc:80
        ctx:state().g_bWasRunning = ctx:self():getStat("IsFlying") -- BASEDOOR.inc:81
    end -- BASEDOOR.inc:82
    -- if we're not walking or running, then the door hit us.
    -- don't care about this...
    if ctx:condition("g_bWasRunning==FALSE") then -- BASEDOOR.inc:86
        if ctx:condition("g_bWasWalking==FALSE") then -- BASEDOOR.inc:87
            do return ctx:exit("FALSE") end -- BASEDOOR.inc:88
        end -- BASEDOOR.inc:89
    end -- BASEDOOR.inc:90
    -- Get the angle between the way we're facing and the door.
    -- Perhaps we aren't going through the door...
    ctx:getParam(1, "g_normalX") -- BASEDOOR.inc:95
    ctx:getParam(2, "g_normalY") -- BASEDOOR.inc:96
    ctx:getParam(3, "g_normalZ") -- BASEDOOR.inc:97
    ctx:state().g_normalX, ctx:state().g_normalY, ctx:state().g_normalZ = ctx:rotateDir("g_normalX", "g_normalY", "g_normalZ", 180) -- BASEDOOR.inc:98
    ctx:state().g_velX, ctx:state().g_velY, ctx:state().g_velZ = ctx:self():rotation() -- BASEDOOR.inc:100
    ctx:state().g_nTemp = ctx:vecAngle("g_normalX", 0, "g_normalZ", "g_velX", 0, "g_velZ") -- BASEDOOR.inc:102
    if ctx:condition("g_nTemp > 45") then -- BASEDOOR.inc:104
        -- we're not really heading toward the door....
        do return ctx:exit("FALSE") end -- BASEDOOR.inc:106
    end -- BASEDOOR.inc:107
    -- OK, we want to go through the door...
    -- Stop and face the door...
    ctx:self():stop() -- BASEDOOR.inc:114
    ctx:self():faceDir("g_normalX", 0, "g_normalZ", 360) -- BASEDOOR.inc:115
    -- Open it...
    ctx:trigger("g_hDoor", "g_sOpenString") -- BASEDOOR.inc:118
    -- Pause all wait timeouts...
    ctx:self():pauseWait(-1) -- BASEDOOR.inc:122
    -- wait for door to open...
    ctx:state().g_nTemp = ctx:object("g_hDoor"):getStat("DoorOpenTime") -- BASEDOOR.inc:127
    ctx:wait(0, "g_nTemp", "BD_DoorOpen") -- BASEDOOR.inc:129
    ctx:savePath() -- BASEDOOR.inc:131
    ctx:state().g_bDoorOpening = true -- BASEDOOR.inc:133
    do return ctx:exit("") end -- BASEDOOR.inc:135
end

script.labels["BaseDoorInit"] = function(ctx)
    -- BASEDOOR.inc:138
    ctx:onEvent("OnDoor", "BD_OnDoor") -- BASEDOOR.inc:142
    do return ctx:exit("") end -- BASEDOOR.inc:144
end

return script
