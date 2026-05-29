-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC94.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }

-- NPC94.scr
-- By Timmy
-- Handles Lord Kluso voice and stuff
script.labels["OnRude"] = function(ctx)
    -- NPC94.scr:17
    mm9.gosub(script, ctx, "herbs") -- NPC94.scr:19
    do return ctx:exit("") end -- NPC94.scr:20
end

script.labels["Herbs"] = function(ctx)
    -- NPC94.scr:23
    if ctx:hasKey(128) then -- NPC94.scr:27-28
        -- checks to see if player is on the yobboe promo quest
        if not ctx:hasKey(131) then -- NPC94.scr:30-31
            -- checks to see if player has already done this
            ctx:giveKey(131) -- NPC94.scr:33
            -- gives herbs key.
            do return ctx:exit("") end -- NPC94.scr:35
        end -- NPC94.scr:36
    end -- NPC94.scr:37
    do return ctx:exit("") end -- NPC94.scr:38
end

script.labels["OnUse"] = function(ctx)
    -- NPC94.scr:41
    ctx:playSound("voices\\NPC\\NPC_094.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC94.scr:44
    do return ctx:exit("") end -- NPC94.scr:45
end

script.labels["OnExit"] = function(ctx)
    -- NPC94.scr:48
    do return ctx:exit("") end -- NPC94.scr:51
end

script.labels["Main"] = function(ctx)
    -- NPC94.scr:54
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Use", "Onuse") -- NPC94.scr:58
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC94.scr:59
    do return ctx:exit("") end -- NPC94.scr:61
end

return script
