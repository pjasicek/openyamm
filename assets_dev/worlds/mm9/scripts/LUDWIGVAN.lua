-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LUDWIGVAN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- LudwigVan.scr
-- By Timmy
-- gives the player reward for finding Ludwig's mauscript
-- and the related key
-- Ludwig's RudeID is 47
script.labels["OnRude"] = function(ctx)
    -- LUDWIGVAN.scr:15
    mm9.gosub(script, ctx, "Init") -- LUDWIGVAN.scr:18
    ctx:hasKey(116, "keycheck") -- LUDWIGVAN.scr:20
    if ctx:condition("keycheck==0") then -- LUDWIGVAN.scr:21
        -- checks to see if they already have got the reward.
        if ctx:hasKey(19) then -- LUDWIGVAN.scr:23-24
            -- checks to see if they've got the mauscript
            ctx:giveKey(116) -- LUDWIGVAN.scr:26
            ctx:giveExp(12000) -- LUDWIGVAN.scr:27
            ctx:giveGold(2000) -- LUDWIGVAN.scr:28
            ctx:takeItem(248) -- LUDWIGVAN.scr:29
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- LUDWIGVAN.scr:30
            -- gives reward
            -- *** this is where the manuscript should be removed from inventory***
            do return ctx:exit("") end -- LUDWIGVAN.scr:33
        end -- LUDWIGVAN.scr:34
    end -- LUDWIGVAN.scr:35
    do return ctx:exit("") end -- LUDWIGVAN.scr:36
end

script.labels["OnUse"] = function(ctx)
    -- LUDWIGVAN.scr:40
    ctx:command("stop", "") -- LUDWIGVAN.scr:43
    ctx:command("playsound", "voices\\NPC\\NPC_047.wav, DoNothing, 100, 240, FALSE, 100") -- LUDWIGVAN.scr:44
    ctx:command("playanim", "Ludwig_Lookup Donothing") -- LUDWIGVAN.scr:45
    do return ctx:exit("") end -- LUDWIGVAN.scr:46
end

script.labels["Init"] = function(ctx)
    -- LUDWIGVAN.scr:49
    ctx:command("loopanim", "Ludwig_writting 0 DoNothing") -- LUDWIGVAN.scr:52
    do return ctx:exit("") end -- LUDWIGVAN.scr:54
end

script.labels["Main"] = function(ctx)
    -- LUDWIGVAN.scr:58
    -- TraceOn ;DELETE ME!!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- LUDWIGVAN.scr:62
    ctx:addTrigger("Use", "OnUse") -- LUDWIGVAN.scr:63
    ctx:command("onpoststartworld", "Init") -- LUDWIGVAN.scr:64
    ctx:command("onpostminisaveload", "Init") -- LUDWIGVAN.scr:65
    ctx:command("onpostsaveload", "Init") -- LUDWIGVAN.scr:66
    ctx:command("wait", "1 .1 Init") -- LUDWIGVAN.scr:67
    do return ctx:exit("") end -- LUDWIGVAN.scr:68
end

return script
