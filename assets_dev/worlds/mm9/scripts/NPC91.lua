-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC91.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 18, path = "globals.inc" }

-- NPC91.scr
-- By Timmy
-- checks to see if player is on the quest
-- and gives the plow key
-- relevant RudeIDs: 89, 91, 92, 93
-- key 128 = player is on crusader promo quest
-- Key 130 = player has the plow
-- Dolly is item 370
-- Herbs is item 372
-- plow is item 371
-- edited by Bones 6/14/02
-- TELP Patch 1.3 -- Removed leftover testing code that automatically gave key for killing Yobboes.
-- flag variables
script.labels["OnRude"] = function(ctx)
    -- NPC91.scr:29
    mm9.gosub(script, ctx, "Plow") -- NPC91.scr:31
    do return ctx:exit("") end -- NPC91.scr:32
end

script.labels["Plow"] = function(ctx)
    -- NPC91.scr:36
    if ctx:hasKey(133) then -- NPC91.scr:41-42
        -- checks to see if player has already done this
        if not ctx:hasKey(200) then -- NPC91.scr:44-45
            ctx:takeItem(371) -- NPC91.scr:46
            ctx:giveExp(2000) -- NPC91.scr:47
            ctx:giveGold(500) -- NPC91.scr:48
            ctx:giveKey(200) -- NPC91.scr:49
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC91.scr:50
            -- givekey 129
            -- remove this....this is for when the player kills the yobboes
            -- OK, Tim.
            do return ctx:exit("") end -- NPC91.scr:55
        end -- NPC91.scr:56
    end -- NPC91.scr:57
    do return ctx:exit("") end -- NPC91.scr:58
end

script.labels["OnUse"] = function(ctx)
    -- NPC91.scr:62
    ctx:playSound("voices\\NPC\\NPC_091.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC91.scr:65
    do return ctx:exit("") end -- NPC91.scr:66
end

script.labels["OnExit"] = function(ctx)
    -- NPC91.scr:69
    do return ctx:exit("") end -- NPC91.scr:72
end

script.labels["Init"] = function(ctx)
    -- NPC91.scr:75
    if ctx:hasKey(128) then -- NPC91.scr:77-78
        ctx:state().g_hobject = ctx:self() -- NPC91.scr:79
        ctx:self():setFlag("visible", true) -- NPC91.scr:80
        ctx:self():setFlag("solid", true) -- NPC91.scr:81
        ctx:self():setFlag("gravity", true) -- NPC91.scr:82
    else -- NPC91.scr:83
        ctx:state().g_hobject = ctx:self() -- NPC91.scr:84
        ctx:self():setFlag("visible", false) -- NPC91.scr:85
        ctx:self():setFlag("solid", false) -- NPC91.scr:86
        ctx:self():setFlag("gravity", false) -- NPC91.scr:87
    end -- NPC91.scr:88
    do return ctx:exit("") end -- NPC91.scr:90
end

script.labels["Main"] = function(ctx)
    -- NPC91.scr:93
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Use", "Onuse") -- NPC91.scr:97
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC91.scr:98
    ctx:onEvent("OnPostStartWorld", "Init") -- NPC91.scr:99
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- NPC91.scr:100
    ctx:onEvent("OnPostSaveLoad", "Init") -- NPC91.scr:101
    ctx:wait(1, .1, "Init") -- NPC91.scr:102
    do return ctx:exit("") end -- NPC91.scr:103
end

return script
