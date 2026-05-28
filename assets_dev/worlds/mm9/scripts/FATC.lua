-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "FATC.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "basemelee.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "range.inc" }

-- Fatc.scr
-- By L. Dean Gibson II
-- Ebora's Fat Collodial Warrior Bathmate script in the bathhouse
script.labels["OnMoveIt"] = function(ctx)
    -- FATC.scr:14
    ctx:command("getmyhandle", "g_hMyObject") -- FATC.scr:17
    ctx:command("getstat", "g_hMyObject RunVel g_velX") -- FATC.scr:18
    ctx:command("getpos", "g_hMyObject g_posX g_posY g_posZ") -- FATC.scr:19
    ctx:command("movetopos", "1808, 44, g_posZ, g_velX, Arrived") -- FATC.scr:20
    do return ctx:exit("") end -- FATC.scr:22
end

script.labels["Arrived"] = function(ctx)
    -- FATC.scr:25
    ctx:command("setidle", "") -- FATC.scr:28
    do return ctx:exit("") end -- FATC.scr:30
end

script.labels["OnEboraArrive"] = function(ctx)
    -- FATC.scr:33
    mm9.gosub(script, ctx, "BaseInit") -- FATC.scr:35
    mm9.gosub(script, ctx, "RangeInit") -- FATC.scr:36
    do return ctx:exit("") end -- FATC.scr:37
end

script.labels["OnDeath"] = function(ctx)
    -- FATC.scr:40
    -- GetObjectHandle Ebora g_hObject
    -- Trigger g_hObject DeadPal
    do return ctx:exit("") end -- FATC.scr:44
end

script.labels["OnDie"] = function(ctx)
    -- FATC.scr:48
    ctx:command("stop", "") -- FATC.scr:50
    ctx:command("die", "") -- FATC.scr:51
    do return ctx:exit("") end -- FATC.scr:52
end

script.labels["Main"] = function(ctx)
    -- FATC.scr:56
    ctx:addTrigger("Die", "OnDie") -- FATC.scr:60
    ctx:addTrigger("MoveIt", "OnMoveIt") -- FATC.scr:61
    ctx:addTrigger("EboraArrive", "OnEboraArrive") -- FATC.scr:62
    mm9.gosub(script, ctx, "BaseInit") -- FATC.scr:64
    mm9.gosub(script, ctx, "RangeInit") -- FATC.scr:65
    ctx:command("ondeath", "OnDeath") -- FATC.scr:67
    do return ctx:exit("") end -- FATC.scr:68
end

return script
