-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC3.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "United.inc" }

-- NPC3.scr
-- timmy
-- handles Sven Forkbeard voice and quest stuff
-- edited by Bones 03/25/03, 05/15/03
-- Patch 1.3 -- delays Sven's return
-- Moves him south
-- flag variables
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC3.scr:33
    mm9.gosub(script, ctx, "GoGetEm") -- NPC3.scr:37
    mm9.gosub(script, ctx, "thjorad") -- NPC3.scr:38
    mm9.gosub(script, ctx, "Refinery") -- NPC3.scr:39
    mm9.gosub(script, ctx, "united") -- NPC3.scr:40
    mm9.gosub(script, ctx, "lifesaver") -- NPC3.scr:41
    do return ctx:exit("") end -- NPC3.scr:42
end

script.labels["GoGetEm"] = function(ctx)
    -- NPC3.scr:46
    -- just plays Bling after player gets key 104 to get the Battle
    if ctx:hasKey(104) then -- NPC3.scr:50-51
        if ctx:hasKey(486) then -- NPC3.scr:53-54
            do return ctx:exit("") end -- NPC3.scr:55
        end -- NPC3.scr:56
        ctx:giveKey(486) -- NPC3.scr:58
        ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC3.scr:59
    end -- NPC3.scr:60
    do return ctx:exit("") end -- NPC3.scr:61
end

script.labels["Lifesaver"] = function(ctx)
    -- NPC3.scr:65
    if not ctx:hasKey(235) then -- NPC3.scr:68-69
        if ctx:hasKey(234) then -- NPC3.scr:70-71
            ctx:giveExp(5000) -- NPC3.scr:72
            if ctx:hasKey(233) then -- NPC3.scr:73-74
                ctx:giveGold(10000) -- NPC3.scr:75
                ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC3.scr:76
                ctx:giveKey(235) -- NPC3.scr:77
                do return ctx:exit("") end -- NPC3.scr:78
            else -- NPC3.scr:79
                ctx:giveGold(10000) -- NPC3.scr:80
                ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC3.scr:81
                ctx:giveKey(235) -- NPC3.scr:82
                do return ctx:exit("") end -- NPC3.scr:83
            end -- NPC3.scr:84
        end -- NPC3.scr:85
    end -- NPC3.scr:86
    do return ctx:exit("") end -- NPC3.scr:87
end

script.labels["Thjorad"] = function(ctx)
    -- NPC3.scr:90
    -- Thjorad Quest
    ctx:hasKey(163, "keycheck") -- NPC3.scr:96
    if ctx:condition("keycheck==0") then -- NPC3.scr:97
        -- checks to see if they already have got the reward.
        if ctx:hasKey(32) then -- NPC3.scr:99-100
            -- checks to see if they've got thjorad
            ctx:giveKey(163) -- NPC3.scr:102
            ctx:giveExp(12000) -- NPC3.scr:103
            ctx:giveGold(6000) -- NPC3.scr:104
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC3.scr:105
            ctx:takeItem(197) -- NPC3.scr:106
            -- gives reward
            do return ctx:exit("") end -- NPC3.scr:109
        end -- NPC3.scr:110
    end -- NPC3.scr:111
    do return ctx:exit("") end -- NPC3.scr:113
    -- End thjorad quest
    do return ctx:exit("") end -- NPC3.scr:118
end

script.labels["Refinery"] = function(ctx)
    -- NPC3.scr:122
    -- Refinery Quest
    ctx:hasKey(177, "keycheck") -- NPC3.scr:129
    if ctx:condition("keycheck==0") then -- NPC3.scr:130
        -- checks to see if they already have got the reward.
        if ctx:hasKey(33) then -- NPC3.scr:132-133
            -- checks to see if they've got the mines working
            ctx:giveKey(177) -- NPC3.scr:135
            ctx:giveExp(68004) -- NPC3.scr:136
            ctx:giveGold(3000) -- NPC3.scr:137
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC3.scr:138
            -- gives reward
            do return ctx:exit("") end -- NPC3.scr:141
        end -- NPC3.scr:142
    end -- NPC3.scr:143
    do return ctx:exit("") end -- NPC3.scr:145
    -- End Refinery Quest
    do return ctx:exit("") end -- NPC3.scr:150
end

script.labels["OnUse"] = function(ctx)
    -- NPC3.scr:156
    -- Playsound voices\NPC\NPC_003.wav, Onexit, 100, 240, FALSE, 100
    mm9.gosub(script, ctx, "Oncheck") -- NPC3.scr:162
    do return ctx:exit("") end -- NPC3.scr:163
end

script.labels["Init"] = function(ctx)
    -- NPC3.scr:166
    if ctx:condition("sLocation==Arslegard") then -- NPC3.scr:169
        -- Cprint INArslegard
        if ctx:hasKey(102) then -- NPC3.scr:173-174
            ctx:state().bVanish = false -- NPC3.scr:175
            mm9.gosub(script, ctx, "Vanish") -- NPC3.scr:176
        else -- NPC3.scr:177
            ctx:state().bVanish = true -- NPC3.scr:178
            mm9.gosub(script, ctx, "Vanish") -- NPC3.scr:179
        end -- NPC3.scr:180
        if ctx:hasKey(104) then -- NPC3.scr:183-184
            ctx:state().bVanish = true -- NPC3.scr:185
            mm9.gosub(script, ctx, "Vanish") -- NPC3.scr:186
            do return ctx:exit("") end -- NPC3.scr:187
        end -- NPC3.scr:188
        do return ctx:exit("") end -- NPC3.scr:189
    end -- NPC3.scr:190
    if ctx:hasKey(40) then -- NPC3.scr:192-193
        ctx:state().bVanish = true -- NPC3.scr:194
        mm9.gosub(script, ctx, "vanish") -- NPC3.scr:195
    end -- NPC3.scr:196
    ctx:self():moveToPos(32, 1438, 8100) -- NPC3.scr:198
    if ctx:hasKey(108) then -- NPC3.scr:200-201
        ctx:state().bVanish = false -- NPC3.scr:202
        mm9.gosub(script, ctx, "Vanish") -- NPC3.scr:203
        -- loopanim Sit 0 DoNothing
    end -- NPC3.scr:205
    do return ctx:exit("") end -- NPC3.scr:206
end

script.labels["Vanish"] = function(ctx)
    -- NPC3.scr:211
    ctx:state().g_hobject = ctx:self() -- NPC3.scr:214
    if ctx:condition("bVanish==TRUE") then -- NPC3.scr:216
        ctx:self():setFlag("visible", false) -- NPC3.scr:217
        ctx:self():setFlag("solid", false) -- NPC3.scr:218
        ctx:self():setFlag("gravity", false) -- NPC3.scr:219
        do return ctx:exit("") end -- NPC3.scr:220
    else -- NPC3.scr:221
        ctx:self():setFlag("visible", true) -- NPC3.scr:222
        ctx:self():setFlag("solid", true) -- NPC3.scr:223
        ctx:self():setFlag("gravity", true) -- NPC3.scr:224
        do return ctx:exit("") end -- NPC3.scr:225
    end -- NPC3.scr:226
    do return ctx:exit("") end -- NPC3.scr:228
end

script.labels["Main"] = function(ctx)
    -- NPC3.scr:230
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC3.scr:236
    ctx:addTrigger("Use", "OnUse") -- NPC3.scr:237
    ctx:getParam(0, "sLocation") -- NPC3.scr:238
    ctx:set("Jarl", "Sven") -- NPC3.scr:239
    mm9.gosub(script, ctx, "UnitedInit") -- NPC3.scr:240
    ctx:onEvent("OnPostStartWorld", "Init") -- NPC3.scr:241
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- NPC3.scr:242
    ctx:onEvent("OnPostSaveLoad", "Init") -- NPC3.scr:243
    ctx:wait(1, .1, "Init") -- NPC3.scr:244
    do return ctx:exit("") end -- NPC3.scr:245
end

return script
