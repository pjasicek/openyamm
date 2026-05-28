-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DUMBGOOSE2.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "HonkHostility.inc" }

-- DumbGoose2.scr
-- by SJR
-- 10-08-01
-- Foyer Goose stuff
script.labels["TurnHostilityOn"] = function(ctx)
    -- DUMBGOOSE2.scr:12
    -- overloaded so dumb goose death
    -- won't set of Hostility
    ctx:command("getmyhandle", "g_hmyobject") -- DUMBGOOSE2.scr:18
    ctx:command("g_ntemp", "= 10") -- DUMBGOOSE2.scr:19
    ctx:command("setstat", "g_hmyobject HitPoints g_ntemp") -- DUMBGOOSE2.scr:20
    ctx:command("g_ntemp", "= 1") -- DUMBGOOSE2.scr:21
    ctx:command("getstat", "g_hmyobject AC g_ntemp") -- DUMBGOOSE2.scr:22
    mm9.gosub(script, ctx, "BecomeHostile") -- DUMBGOOSE2.scr:24
    do return ctx:exit("") end -- DUMBGOOSE2.scr:26
end

script.labels["Main"] = function(ctx)
    -- DUMBGOOSE2.scr:29
    -- OnPostStartWorld InitDumbGoose
    ctx:command("wait", "0, 5, InitDumbGoose") -- DUMBGOOSE2.scr:32
    do return ctx:exit(1) end -- DUMBGOOSE2.scr:34
end

script.labels["InitDumbGoose"] = function(ctx)
    -- DUMBGOOSE2.scr:37
    ctx:command("getmyhandle", "g_hMyObject") -- DUMBGOOSE2.scr:42
    ctx:command("getstat", "g_hMyObject, RunVel, g_nTemp") -- DUMBGOOSE2.scr:43
    ctx:command("setstat", "g_hMyObject, RunVel, g_nTemp") -- DUMBGOOSE2.scr:44
    ctx:command("setstat", "g_hMyObject, WalkVel, g_nTemp") -- DUMBGOOSE2.scr:45
    mm9.gosub(script, ctx, "InitHonkHostility") -- DUMBGOOSE2.scr:47
    mm9.gosub(script, ctx, "RunLoop") -- DUMBGOOSE2.scr:49
    do return ctx:exit(1) end -- DUMBGOOSE2.scr:51
end

script.labels["RunLoop"] = function(ctx)
    -- DUMBGOOSE2.scr:57
    ctx:command("getrandomint", "-5000, 5000, g_nTemp") -- DUMBGOOSE2.scr:59
    ctx:command("runtopos", "g_nTemp, g_nTemp, g_nTemp") -- DUMBGOOSE2.scr:61
    ctx:command("wait", "0, 2, RunLoop") -- DUMBGOOSE2.scr:65
    do return ctx:exit("TRUE") end -- DUMBGOOSE2.scr:67
end

return script
