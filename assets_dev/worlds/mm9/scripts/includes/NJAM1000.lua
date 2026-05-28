-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NJAM1000.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- Njam1000.inc
-- By Timmy
-- 11/16
-- Makes Njam disappear after he's hit a lot
-- flag variables
script.labels["ShouldRunAway"] = function(ctx)
    -- NJAM1000.inc:23
    ctx:command("getmyhandle", "g_hmyobject") -- NJAM1000.inc:26
    ctx:command("getstat", "g_hmyobject HitPoints g_ntemp") -- NJAM1000.inc:27
    if ctx:condition("g_ntemp<nHPRange") then -- NJAM1000.inc:28
        mm9.gosub(script, ctx, "Vanish") -- NJAM1000.inc:29
        do return ctx:exit("") end -- NJAM1000.inc:30
    end -- NJAM1000.inc:31
    mm9.gosub(script, ctx, "ShouldRunAway") -- NJAM1000.inc:33
    do return ctx:exit("") end -- NJAM1000.inc:34
end

script.labels["Vanish"] = function(ctx)
    -- NJAM1000.inc:39
    ctx:command("getmyhandle", "g_hmyobject") -- NJAM1000.inc:41
    -- play vanish effect here
    ctx:command("doclientfx", "g_hmyObject,GreaterDemon") -- NJAM1000.inc:44
    ctx:command("playsound", "\\Sounds\\magic\\Windup10.wav, DoNothing, 100, 24000, FALSE, 100") -- NJAM1000.inc:45
    ctx:command("wait", "1 1 Vanish2b") -- NJAM1000.inc:46
    do return ctx:exit("") end -- NJAM1000.inc:47
end

script.labels["Vanish2b"] = function(ctx)
    -- NJAM1000.inc:50
    ctx:command("clearflag", "g_hmyobject visible") -- NJAM1000.inc:53
    ctx:command("playsound", "\\Sounds\\magic\\teleport.wav, DoNothing, 100, 24000, FALSE, 100") -- NJAM1000.inc:54
    ctx:command("wait", "1 1 Vanish2c") -- NJAM1000.inc:55
    do return ctx:exit("") end -- NJAM1000.inc:56
end

script.labels["Vanish2c"] = function(ctx)
    -- NJAM1000.inc:60
    ctx:command("removeobject", "g_hmyobject") -- NJAM1000.inc:62
    do return ctx:exit("") end -- NJAM1000.inc:63
end

script.labels["Init"] = function(ctx)
    -- NJAM1000.inc:67
    ctx:setPropNumber("CanDamage", "FALSE") -- NJAM1000.inc:70
    ctx:command("getrandomint", "1500, 4500 nHPRange") -- NJAM1000.inc:72
    do return ctx:exit("") end -- NJAM1000.inc:73
end

return script
