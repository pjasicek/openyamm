-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DUMBGOOSE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "HonkHostility.inc" }

-- DumbGoose.scr
-- by SJR
-- 10-08-01
-- Purpose:run around like an idiot
script.labels["Main"] = function(ctx)
    -- DUMBGOOSE.scr:10
    -- OnPostStartWorld InitDumbGoose
    ctx:command("wait", "0, 5, InitDumbGoose") -- DUMBGOOSE.scr:13
    do return ctx:exit(1) end -- DUMBGOOSE.scr:15
end

script.labels["InitDumbGoose"] = function(ctx)
    -- DUMBGOOSE.scr:18
    ctx:command("getmyhandle", "g_hMyObject") -- DUMBGOOSE.scr:20
    ctx:command("getstat", "g_hMyObject, RunVel, g_nTemp") -- DUMBGOOSE.scr:21
    ctx:command("setstat", "g_hMyObject, RunVel, g_nTemp") -- DUMBGOOSE.scr:22
    ctx:command("setstat", "g_hMyObject, WalkVel, g_nTemp") -- DUMBGOOSE.scr:23
    mm9.gosub(script, ctx, "InitHonkHostility") -- DUMBGOOSE.scr:25
    mm9.gosub(script, ctx, "RunLoop") -- DUMBGOOSE.scr:27
    do return ctx:exit(1) end -- DUMBGOOSE.scr:29
end

script.labels["RunLoop"] = function(ctx)
    -- DUMBGOOSE.scr:34
    ctx:command("getrandomint", "-5000, 5000, g_nTemp") -- DUMBGOOSE.scr:36
    ctx:command("runtopos", "g_nTemp, g_nTemp, g_nTemp") -- DUMBGOOSE.scr:38
    ctx:command("wait", "0, 2, RunLoop") -- DUMBGOOSE.scr:41
    do return ctx:exit("TRUE") end -- DUMBGOOSE.scr:43
end

return script
