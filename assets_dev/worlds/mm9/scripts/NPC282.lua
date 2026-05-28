-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC282.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "BaseMelee.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "MonkHostility.inc" }

-- NPC282.scr
-- timmy
-- handles Grehgknak the Right's voice and stuff
-- promo variables
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC282.scr:41
    mm9.gosub(script, ctx, "giveletter") -- NPC282.scr:44
    mm9.gosub(script, ctx, "paladins") -- NPC282.scr:45
    mm9.gosub(script, ctx, "BaseWanderStart") -- NPC282.scr:46
    do return ctx:exit("") end -- NPC282.scr:47
end

script.labels["PromotePaladin"] = function(ctx)
    -- NPC282.scr:53
    -- Player has already completed the quest
    -- just check to see who gets promoted
    ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC282.scr:58
    if ctx:hasKey(421) then -- NPC282.scr:60-61
        ctx:command("givepromo", "Paladin Char1") -- NPC282.scr:62
        ctx:takeKey(421) -- NPC282.scr:63
    end -- NPC282.scr:64
    if ctx:hasKey(422) then -- NPC282.scr:66-67
        ctx:command("givepromo", "Paladin Char2") -- NPC282.scr:68
        ctx:takeKey(422) -- NPC282.scr:69
    end -- NPC282.scr:70
    if ctx:hasKey(423) then -- NPC282.scr:72-73
        ctx:command("givepromo", "Paladin Char3") -- NPC282.scr:74
        ctx:takeKey(423) -- NPC282.scr:75
    end -- NPC282.scr:76
    if ctx:hasKey(424) then -- NPC282.scr:78-79
        ctx:command("givepromo", "Paladin Char4") -- NPC282.scr:80
        ctx:takeKey(424) -- NPC282.scr:81
    end -- NPC282.scr:82
    do return ctx:exit("") end -- NPC282.scr:83
end

script.labels["paladins"] = function(ctx)
    -- NPC282.scr:86
    if not ctx:hasKey(237) then -- NPC282.scr:89-90
        if ctx:hasKey(236) then -- NPC282.scr:91-92
            ctx:giveExp(63000) -- NPC282.scr:93
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC282.scr:94
            mm9.gosub(script, ctx, "PromotePaladin") -- NPC282.scr:95
            ctx:giveGold(5000) -- NPC282.scr:96
            ctx:giveKey(237) -- NPC282.scr:97
            do return ctx:exit("") end -- NPC282.scr:98
        end -- NPC282.scr:99
    end -- NPC282.scr:100
    do return ctx:exit("") end -- NPC282.scr:101
end

script.labels["giveletter"] = function(ctx)
    -- NPC282.scr:104
    if not ctx:hasKey(229) then -- NPC282.scr:107-108
        if ctx:hasKey(228) then -- NPC282.scr:109-110
            ctx:giveKey(229) -- NPC282.scr:111
            ctx:giveItem(419) -- NPC282.scr:112
            do return ctx:exit("") end -- NPC282.scr:113
        end -- NPC282.scr:114
    end -- NPC282.scr:115
    do return ctx:exit("") end -- NPC282.scr:116
end

script.labels["OnUse"] = function(ctx)
    -- NPC282.scr:120
    ctx:command("stop", "") -- NPC282.scr:123
    mm9.gosub(script, ctx, "BaseWanderStop") -- NPC282.scr:124
    ctx:getParam(0, "g_hobject") -- NPC282.scr:125
    ctx:command("faceobject", "g_hobject 240 DoNothing") -- NPC282.scr:126
    ctx:doRude(282) -- NPC282.scr:127
    ctx:command("playsound", "voices\\NPC\\NPC_282.wav, DoNothing, 100, 240, FALSE, 100") -- NPC282.scr:128
    do return ctx:exit("") end -- NPC282.scr:130
end

script.labels["Init"] = function(ctx)
    -- NPC282.scr:134
    mm9.gosub(script, ctx, "BaseWanderInit") -- NPC282.scr:137
    mm9.gosub(script, ctx, "InitMonkHostility") -- NPC282.scr:138
    do return ctx:exit("") end -- NPC282.scr:139
end

script.labels["Main"] = function(ctx)
    -- NPC282.scr:142
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC282.scr:147
    ctx:addTrigger("Use", "OnUse") -- NPC282.scr:148
    ctx:command("onpoststartworld", "Init") -- NPC282.scr:149
    ctx:command("onpostminisaveload", "Init") -- NPC282.scr:150
    ctx:command("onpostsaveload", "Init") -- NPC282.scr:151
    ctx:command("wait", "1 .1 Init") -- NPC282.scr:152
    do return ctx:exit("") end -- NPC282.scr:153
end

return script
