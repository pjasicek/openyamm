-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TELEPORTER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 15, path = "BaseGlobals.inc" }

-- Teleporter.scr
-- by SJR
-- 11-21-01
-- Purpose:teleport creatures or player
-- to some remote spot OnTouch
-- ScriptParams:
-- p0 = name of destination object
-- p1 = activation mode  (1='Use', 0='OnTouch)
-- p2 = what to teleport (0=monsters only, 1=monsters+player, 2=player only)
-- p3 = object to trigger OnTeleport
script.labels["Main"] = function(ctx)
    -- TELEPORTER.scr:31
    ctx:getParam(0, "sDestName") -- TELEPORTER.scr:33
    ctx:getParam(1, "bOnUseOnly") -- TELEPORTER.scr:34
    ctx:getParam(2, "bMonstersOnly") -- TELEPORTER.scr:35
    ctx:getParam(3, "sMessageName") -- TELEPORTER.scr:36
    ctx:wait(0, 2, "InitTeleporter") -- TELEPORTER.scr:38
    do return ctx:exit("TRUE") end -- TELEPORTER.scr:40
end

script.labels["InitTeleporter"] = function(ctx)
    -- TELEPORTER.scr:46
    ctx:addTrigger("Off", "TurnOff") -- TELEPORTER.scr:48
    ctx:addTrigger("On", "TurnOn") -- TELEPORTER.scr:49
    mm9.gosub(script, ctx, "TurnOn") -- TELEPORTER.scr:51
    ctx:state().hTrigger = ctx:objectOrNil("sMessageName") -- TELEPORTER.scr:53
    ctx:state().xDest, ctx:state().yDest, ctx:state().zDest = ctx:object("sDestName"):pos() -- TELEPORTER.scr:54-55
    ctx:addTrigger("Use", "Teleport") -- TELEPORTER.scr:57
    ctx:onEvent("OnTouchNotify", "Teleport") -- TELEPORTER.scr:58
    do return ctx:exit("TRUE") end -- TELEPORTER.scr:60
end

script.labels["Teleport"] = function(ctx)
    -- TELEPORTER.scr:63
    -- whether 'use' or touch, check object
    ctx:cprint("Teleport") -- TELEPORTER.scr:66
    ctx:getParam(0, "hObject") -- TELEPORTER.scr:67
    ctx:cprint("hObject") -- TELEPORTER.scr:68
    -- if 1 or 2, do player
    if ctx:condition("bMonstersOnly>0") then -- TELEPORTER.scr:71
        ctx:state().bIsPlayer = ctx:object("hObject"):isPlayer() -- TELEPORTER.scr:72
        if ctx:condition("bIsPlayer==TRUE") then -- TELEPORTER.scr:73
            ctx:object("hObject"):setPos("xDest", "yDest", "zDest") -- TELEPORTER.scr:74
            ctx:trigger("hTrigger", "trigger") -- TELEPORTER.scr:75
        end -- TELEPORTER.scr:76
    end -- TELEPORTER.scr:77
    -- if 0 or 1, do monster
    if ctx:condition("bMonstersOnly<2") then -- TELEPORTER.scr:80
        ctx:state().bIsMonster = (ctx:object("hObject"):isAi() and 1 or 0) -- TELEPORTER.scr:81
        if ctx:condition("bIsMonster==TRUE") then -- TELEPORTER.scr:82
            ctx:object("hObject"):setPos("xDest", "yDest", "zDest") -- TELEPORTER.scr:83
            ctx:trigger("hTrigger", "trigger") -- TELEPORTER.scr:84
        end -- TELEPORTER.scr:85
    end -- TELEPORTER.scr:86
    do return ctx:exit("TRUE") end -- TELEPORTER.scr:88
end

script.labels["TurnOff"] = function(ctx)
    -- TELEPORTER.scr:91
    -- disable teleporting
    ctx:removeTrigger("Use") -- TELEPORTER.scr:94
    ctx:onEvent("OnTouchNotify", "DoNothing") -- TELEPORTER.scr:95
    do return ctx:exit("TRUE") end -- TELEPORTER.scr:97
end

script.labels["TurnOn"] = function(ctx)
    -- TELEPORTER.scr:100
    -- enable teleporting with current options
    if ctx:condition("bOnUseOnly==TRUE") then -- TELEPORTER.scr:103
        ctx:addTrigger("Use", "Teleport") -- TELEPORTER.scr:104
    else -- TELEPORTER.scr:105
        ctx:onEvent("OnTouchNotify", "Teleport") -- TELEPORTER.scr:106
    end -- TELEPORTER.scr:107
    do return ctx:exit("TRUE") end -- TELEPORTER.scr:109
end

return script
