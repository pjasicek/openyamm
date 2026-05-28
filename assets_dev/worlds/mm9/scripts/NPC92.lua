-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC92.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 16, path = "globals.inc" }

-- NPC92.scr
-- By Timmy
-- checks to see if player is on the quest
-- and gives the herbs key
-- relevant RudeIDs: 89, 91, 92, 93
-- key 128 = player is on yobboe promo quest
-- Key 131 = player has the herbs
-- Dolly is item 370
-- Herbs is item 372
-- plow is item 371
-- flag variables
script.labels["OnRude"] = function(ctx)
    -- NPC92.scr:27
    mm9.gosub(script, ctx, "herbs") -- NPC92.scr:29
    do return ctx:exit("") end -- NPC92.scr:30
end

script.labels["Herbs"] = function(ctx)
    -- NPC92.scr:33
    if ctx:hasKey(134) then -- NPC92.scr:37-38
        -- checks to see if player has already done this
        if not ctx:hasKey(198) then -- NPC92.scr:40-41
            ctx:takeItem(372) -- NPC92.scr:42
            ctx:giveExp(2000) -- NPC92.scr:43
            ctx:giveGold(500) -- NPC92.scr:44
            ctx:giveKey(198) -- NPC92.scr:45
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC92.scr:46
            do return ctx:exit("") end -- NPC92.scr:47
        end -- NPC92.scr:48
    end -- NPC92.scr:49
    do return ctx:exit("") end -- NPC92.scr:50
end

script.labels["OnUse"] = function(ctx)
    -- NPC92.scr:53
    ctx:command("playsound", "voices\\NPC\\NPC_092.wav, Onexit, 100, 240, FALSE, 100") -- NPC92.scr:56
    do return ctx:exit("") end -- NPC92.scr:57
end

script.labels["OnExit"] = function(ctx)
    -- NPC92.scr:60
    do return ctx:exit("") end -- NPC92.scr:63
end

script.labels["Init"] = function(ctx)
    -- NPC92.scr:65
    if ctx:hasKey(128) then -- NPC92.scr:67-68
        ctx:command("getmyhandle", "g_hobject") -- NPC92.scr:69
        ctx:command("setflag", "g_hobject, visible") -- NPC92.scr:70
        ctx:command("setflag", "g_hobject, solid") -- NPC92.scr:71
        ctx:command("setflag", "g_hobject, gravity") -- NPC92.scr:72
    else -- NPC92.scr:73
        ctx:command("getmyhandle", "g_hobject") -- NPC92.scr:74
        ctx:command("clearflag", "g_hobject, visible") -- NPC92.scr:75
        ctx:command("clearflag", "g_hobject, solid") -- NPC92.scr:76
        ctx:command("clearflag", "g_hobject, gravity") -- NPC92.scr:77
    end -- NPC92.scr:78
    do return ctx:exit("") end -- NPC92.scr:80
end

script.labels["Main"] = function(ctx)
    -- NPC92.scr:84
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Use", "Onuse") -- NPC92.scr:88
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC92.scr:89
    ctx:command("onpoststartworld", "Init") -- NPC92.scr:90
    ctx:command("onpostminisaveload", "Init") -- NPC92.scr:91
    ctx:command("onpostsaveload", "Init") -- NPC92.scr:92
    ctx:command("wait", "1 .1 Init") -- NPC92.scr:93
    do return ctx:exit("") end -- NPC92.scr:94
end

return script
