-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC93.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 16, path = "globals.inc" }

-- NPC93.scr
-- By Timmy
-- checks to see if player is on the quest
-- and gives the dolly key
-- relevant RudeIDs: 89, 91, 92, 93
-- key 128 = player is on yobboe promo quest
-- Key 132 = player has the plow
-- Dolly is item 370
-- Herbs is item 372
-- plow is item 371
-- flag variables
script.labels["OnRude"] = function(ctx)
    -- NPC93.scr:27
    mm9.gosub(script, ctx, "dolly") -- NPC93.scr:29
    do return ctx:exit("") end -- NPC93.scr:30
end

script.labels["dolly"] = function(ctx)
    -- NPC93.scr:35
    if ctx:hasKey(135) then -- NPC93.scr:39-40
        -- checks to see if player has already done this
        if not ctx:hasKey(199) then -- NPC93.scr:42-43
            ctx:takeItem(370) -- NPC93.scr:44
            ctx:giveExp(2000) -- NPC93.scr:45
            ctx:giveGold(500) -- NPC93.scr:46
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC93.scr:47
            ctx:giveKey(199) -- NPC93.scr:48
            do return ctx:exit("") end -- NPC93.scr:49
        end -- NPC93.scr:50
    end -- NPC93.scr:51
    do return ctx:exit("") end -- NPC93.scr:52
end

script.labels["OnUse"] = function(ctx)
    -- NPC93.scr:55
    ctx:playSound("voices\\NPC\\NPC_093.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC93.scr:58
    do return ctx:exit("") end -- NPC93.scr:59
end

script.labels["Init"] = function(ctx)
    -- NPC93.scr:62
    if ctx:hasKey(128) then -- NPC93.scr:64-65
        ctx:state().g_hobject = ctx:self() -- NPC93.scr:66
        ctx:self():setFlag("visible", true) -- NPC93.scr:67
        ctx:self():setFlag("solid", true) -- NPC93.scr:68
        ctx:self():setFlag("gravity", true) -- NPC93.scr:69
    else -- NPC93.scr:70
        ctx:state().g_hobject = ctx:self() -- NPC93.scr:71
        ctx:self():setFlag("visible", false) -- NPC93.scr:72
        ctx:self():setFlag("solid", false) -- NPC93.scr:73
        ctx:self():setFlag("gravity", false) -- NPC93.scr:74
    end -- NPC93.scr:75
    do return ctx:exit("") end -- NPC93.scr:77
end

script.labels["Main"] = function(ctx)
    -- NPC93.scr:83
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Use", "Onuse") -- NPC93.scr:87
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC93.scr:88
    ctx:onEvent("OnPostStartWorld", "Init") -- NPC93.scr:89
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- NPC93.scr:90
    ctx:onEvent("OnPostSaveLoad", "Init") -- NPC93.scr:91
    ctx:wait(1, .1, "Init") -- NPC93.scr:92
    do return ctx:exit("") end -- NPC93.scr:93
end

return script
