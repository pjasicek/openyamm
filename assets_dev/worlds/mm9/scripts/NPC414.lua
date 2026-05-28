-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC414.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC414.scr
-- timmy
-- handles Nicolai Ironfist voice and quest stuff
-- flag variables
script.labels["OnRude"] = function(ctx)
    -- NPC414.scr:15
    mm9.gosub(script, ctx, "thjorad") -- NPC414.scr:18
    mm9.gosub(script, ctx, "Refinery") -- NPC414.scr:19
    do return ctx:exit("") end -- NPC414.scr:21
end

script.labels["Thjorad"] = function(ctx)
    -- NPC414.scr:25
    -- Thjorad Quest
    -- End thjorad quest
    do return ctx:exit("") end -- NPC414.scr:36
end

script.labels["Refinery"] = function(ctx)
    -- NPC414.scr:40
    -- Refinery Quest
    -- End Refinery Quest
    do return ctx:exit("") end -- NPC414.scr:51
end

script.labels["OnUse"] = function(ctx)
    -- NPC414.scr:57
    ctx:command("playsound", "voices\\NPC\\NPC_414.wav, DoNothing, 100, 240, FALSE, 100") -- NPC414.scr:60
    do return ctx:exit("") end -- NPC414.scr:61
end

script.labels["Init"] = function(ctx)
    -- NPC414.scr:64
    if ctx:hasKey(121) then -- NPC414.scr:68-69
        ctx:command("getmyhandle", "g_hobject") -- NPC414.scr:71
        if ctx:condition("sLocation==Guberland") then -- NPC414.scr:73
            ctx:command("setflag", "g_hobject, visible") -- NPC414.scr:74
            ctx:command("setflag", "g_hobject, solid") -- NPC414.scr:75
            ctx:command("setflag", "g_hobject, gravity") -- NPC414.scr:76
            do return ctx:exit("") end -- NPC414.scr:77
        else -- NPC414.scr:78
            ctx:command("clearflag", "g_hobject, visible") -- NPC414.scr:79
            ctx:command("clearflag", "g_hobject, solid") -- NPC414.scr:80
            ctx:command("clearflag", "g_hobject, gravity") -- NPC414.scr:81
            do return ctx:exit("") end -- NPC414.scr:82
        end -- NPC414.scr:83
    end -- NPC414.scr:84
    do return ctx:exit("") end -- NPC414.scr:86
end

script.labels["Main"] = function(ctx)
    -- NPC414.scr:89
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC414.scr:96
    ctx:getParam(0, "sLocation") -- NPC414.scr:97
    ctx:addTrigger("Use", "OnUse") -- NPC414.scr:98
    ctx:command("onpoststartworld", "Init") -- NPC414.scr:99
    ctx:command("onpostminisaveload", "Init") -- NPC414.scr:100
    ctx:command("onpostsaveload", "Init") -- NPC414.scr:101
    ctx:command("wait", "1 .1 Init") -- NPC414.scr:102
    do return ctx:exit("") end -- NPC414.scr:103
end

return script
