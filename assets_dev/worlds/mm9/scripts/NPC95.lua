-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC95.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "Basemelee.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "Basewander.inc" }

-- NPC95.scr
-- timmy
-- handles Guaire A'velsi voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
-- flag variables
script.labels["OnDeath"] = function(ctx)
    -- NPC95.scr:28
    if not ctx:hasKey(225) then -- NPC95.scr:31-32
        ctx:giveKey(225) -- NPC95.scr:33
    end -- NPC95.scr:34
    mm9.gosub(script, ctx, "OnDeath") -- NPC95.scr:36
    do return ctx:exit("") end -- NPC95.scr:39
end

script.labels["OnRude"] = function(ctx)
    -- NPC95.scr:42
    mm9.gosub(script, ctx, "Basewanderstart") -- NPC95.scr:45
    do return ctx:exit("") end -- NPC95.scr:46
end

script.labels["OnUse"] = function(ctx)
    -- NPC95.scr:48
    ctx:command("stop", "") -- NPC95.scr:52
    mm9.gosub(script, ctx, "BasewanderStop") -- NPC95.scr:53
    ctx:getParam(0, "g_hobject") -- NPC95.scr:54
    ctx:command("faceobject", "g_hobject 200 DoNothing") -- NPC95.scr:55
    ctx:command("playsound", "voices\\NPC\\NPC_095.wav, DoNothing, 100, 240, FALSE, 100") -- NPC95.scr:56
    ctx:doRude(95) -- NPC95.scr:57
    do return ctx:exit("") end -- NPC95.scr:58
end

script.labels["Init"] = function(ctx)
    -- NPC95.scr:61
    if ctx:hasKey(225) then -- NPC95.scr:64-65
        ctx:command("getmyhandle", "g_hmyobject") -- NPC95.scr:66
        ctx:command("removeobject", "g_hmyobject") -- NPC95.scr:67
        do return ctx:exit("") end -- NPC95.scr:68
    end -- NPC95.scr:69
    ctx:command("getmyhandle", "g_hobject") -- NPC95.scr:71
    if ctx:hasKey(222) then -- NPC95.scr:73-74
        ctx:command("setstat", "g_hobject Hitpoints 300") -- NPC95.scr:75
        ctx:command("setstat", "g_hobject AC 50") -- NPC95.scr:76
        ctx:command("setflag", "g_hobject, visible") -- NPC95.scr:77
        ctx:command("setflag", "g_hobject, solid") -- NPC95.scr:78
        ctx:command("setflag", "g_hobject, gravity") -- NPC95.scr:79
        mm9.gosub(script, ctx, "basewanderinit") -- NPC95.scr:80
        do return ctx:exit("") end -- NPC95.scr:81
    else -- NPC95.scr:82
        ctx:command("clearflag", "g_hobject, visible") -- NPC95.scr:83
        ctx:command("clearflag", "g_hobject, solid") -- NPC95.scr:84
        ctx:command("clearflag", "g_hobject, gravity") -- NPC95.scr:85
        do return ctx:exit("") end -- NPC95.scr:86
    end -- NPC95.scr:87
    do return ctx:exit("") end -- NPC95.scr:90
end

script.labels["OnDamage"] = function(ctx)
    -- NPC95.scr:93
    mm9.gosub(script, ctx, "BaseInit") -- NPC95.scr:96
    do return ctx:exit("") end -- NPC95.scr:97
end

script.labels["Main"] = function(ctx)
    -- NPC95.scr:100
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC95.scr:107
    ctx:addTrigger("Use", "OnUse") -- NPC95.scr:108
    -- OnDeath Death
    ctx:command("ondamage", "OnDamage") -- NPC95.scr:110
    mm9.gosub(script, ctx, "basewanderinit") -- NPC95.scr:111
    ctx:command("onpoststartworld", "Init") -- NPC95.scr:112
    ctx:command("onpostminisaveload", "Init") -- NPC95.scr:113
    ctx:command("onpostsaveload", "Init") -- NPC95.scr:114
    ctx:command("wait", "1 .1 Init") -- NPC95.scr:115
    do return ctx:exit("") end -- NPC95.scr:116
end

return script
