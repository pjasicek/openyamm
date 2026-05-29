-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC336.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "sixfires.inc" }

-- NPC336.scr
-- timmy
-- handles Skraelos voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC336.scr:23
    if ctx:condition("sLocation==Hall") then -- NPC336.scr:27
        mm9.gosub(script, ctx, "Teleport") -- NPC336.scr:28
        mm9.gosub(script, ctx, "sixfires") -- NPC336.scr:29
    end -- NPC336.scr:30
    if ctx:hasKey(392) then -- NPC336.scr:32-33
        mm9.gosub(script, ctx, "failure") -- NPC336.scr:34
        do return ctx:exit("") end -- NPC336.scr:35
    end -- NPC336.scr:36
    if ctx:hasKey(380) then -- NPC336.scr:39-40
        mm9.gosub(script, ctx, "Guilt") -- NPC336.scr:41
    end -- NPC336.scr:42
    if ctx:hasKey(382) then -- NPC336.scr:44-45
        mm9.gosub(script, ctx, "Confession") -- NPC336.scr:46
    end -- NPC336.scr:47
    if ctx:hasKey(384) then -- NPC336.scr:49-50
        mm9.gosub(script, ctx, "Suffering") -- NPC336.scr:51
    end -- NPC336.scr:52
    if ctx:hasKey(386) then -- NPC336.scr:54-55
        mm9.gosub(script, ctx, "Retribution") -- NPC336.scr:56
    end -- NPC336.scr:57
    if ctx:hasKey(388) then -- NPC336.scr:59-60
        mm9.gosub(script, ctx, "Absolution") -- NPC336.scr:61
    end -- NPC336.scr:62
    if ctx:hasKey(390) then -- NPC336.scr:65-66
        mm9.gosub(script, ctx, "Rebirth") -- NPC336.scr:67
    end -- NPC336.scr:68
    do return ctx:exit("") end -- NPC336.scr:74
end

script.labels["Failure"] = function(ctx)
    -- NPC336.scr:77
    ctx:takeKey(379) -- NPC336.scr:79
    ctx:takeKey(380) -- NPC336.scr:80
    ctx:takeKey(381) -- NPC336.scr:81
    ctx:takeKey(382) -- NPC336.scr:82
    ctx:takeKey(383) -- NPC336.scr:83
    ctx:takeKey(384) -- NPC336.scr:84
    ctx:takeKey(385) -- NPC336.scr:85
    ctx:takeKey(386) -- NPC336.scr:86
    ctx:takeKey(387) -- NPC336.scr:87
    ctx:takeKey(388) -- NPC336.scr:88
    ctx:takeKey(389) -- NPC336.scr:89
    ctx:takeKey(390) -- NPC336.scr:90
    ctx:takeKey(391) -- NPC336.scr:91
    ctx:takeKey(392) -- NPC336.scr:92
    ctx:object("ExitTrigger0"):trigger("trigger") -- NPC336.scr:93-94
    do return ctx:exit("") end -- NPC336.scr:96
end

script.labels["Teleport"] = function(ctx)
    -- NPC336.scr:98
    if ctx:hasKey(102) then -- NPC336.scr:101-102
        do return ctx:exit("") end -- NPC336.scr:103
    end -- NPC336.scr:104
    if ctx:hasKey(101) then -- NPC336.scr:107-108
        ctx:object("exittrigger0"):trigger("trigger") -- NPC336.scr:109-110
        ctx:giveKey(379) -- NPC336.scr:111
        do return ctx:exit("") end -- NPC336.scr:112
    end -- NPC336.scr:113
    do return ctx:exit("") end -- NPC336.scr:114
end

script.labels["sixfires"] = function(ctx)
    -- NPC336.scr:117
    -- six fires Quest
    if not ctx:hasKey(189) then -- NPC336.scr:124-125
        -- checks to see if they already have got the reward.
        if ctx:hasKey(103) then -- NPC336.scr:127-128
            -- checks to see if they've On the six fires
            ctx:giveKey(189) -- NPC336.scr:130
            ctx:giveExp(52000) -- NPC336.scr:131
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC336.scr:132
            -- gives reward
            do return ctx:exit("") end -- NPC336.scr:136
        end -- NPC336.scr:137
    end -- NPC336.scr:138
    do return ctx:exit("") end -- NPC336.scr:140
    -- End six fires quest
    do return ctx:exit("") end -- NPC336.scr:145
end

script.labels["DoRude"] = function(ctx)
    -- NPC336.scr:148
    ctx:giveKey(379) -- NPC336.scr:151
    ctx:onEvent("OnFoundPlayer") -- NPC336.scr:153
    ctx:doRude(336) -- NPC336.scr:154
    ctx:playSound("\\voices\\npc\\NPC_336.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC336.scr:155
    do return ctx:exit("") end -- NPC336.scr:156
end

script.labels["OnUse"] = function(ctx)
    -- NPC336.scr:160
    if ctx:condition("sLocation!=Afterworld") then -- NPC336.scr:163
        if not ctx:hasKey(391) then -- NPC336.scr:164-165
            if ctx:hasKey(390) then -- NPC336.scr:166-167
                mm9.gosub(script, ctx, "OnReborn") -- NPC336.scr:168
            end -- NPC336.scr:169
        end -- NPC336.scr:170
    end -- NPC336.scr:171
    if ctx:hasKey(382) then -- NPC336.scr:174-175
        ctx:state().nConfession = 0 -- NPC336.scr:176
        if ctx:hasKey(501) then -- NPC336.scr:177-178
            ctx:state().nConfession = (tonumber(ctx:state().nConfession) or 0) + 1 -- NPC336.scr:179
        end -- NPC336.scr:180
        if ctx:hasKey(502) then -- NPC336.scr:182-183
            ctx:state().nConfession = (tonumber(ctx:state().nConfession) or 0) + 1 -- NPC336.scr:184
        end -- NPC336.scr:185
        if ctx:hasKey(503) then -- NPC336.scr:187-188
            ctx:state().nConfession = (tonumber(ctx:state().nConfession) or 0) + 1 -- NPC336.scr:189
        end -- NPC336.scr:190
        if ctx:hasKey(504) then -- NPC336.scr:192-193
            ctx:state().nConfession = (tonumber(ctx:state().nConfession) or 0) + 1 -- NPC336.scr:194
        end -- NPC336.scr:195
        if ctx:hasKey(505) then -- NPC336.scr:197-198
            ctx:state().nConfession = (tonumber(ctx:state().nConfession) or 0) + 1 -- NPC336.scr:199
        end -- NPC336.scr:200
        if ctx:hasKey(506) then -- NPC336.scr:202-203
            ctx:state().nConfession = (tonumber(ctx:state().nConfession) or 0) + 1 -- NPC336.scr:204
        end -- NPC336.scr:205
        if ctx:condition("nConfession==6") then -- NPC336.scr:207
            if not ctx:hasKey(383) then -- NPC336.scr:209-210
                ctx:giveKey(383) -- NPC336.scr:211
                ctx:object("confessionFire"):trigger("On") -- NPC336.scr:212-213
                ctx:giveExp(52000) -- NPC336.scr:214
                ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC336.scr:215
            end -- NPC336.scr:216
        end -- NPC336.scr:217
    end -- NPC336.scr:218
    if ctx:hasKey(388) then -- NPC336.scr:220-221
        ctx:state().nAbsolution = 0 -- NPC336.scr:222
        if ctx:hasItem(563) then -- NPC336.scr:224-225
            ctx:state().nAbsolution = (tonumber(ctx:state().nAbsolution) or 0) + 1 -- NPC336.scr:226
        end -- NPC336.scr:227
        if ctx:hasItem(564) then -- NPC336.scr:229-230
            ctx:state().nAbsolution = (tonumber(ctx:state().nAbsolution) or 0) + 1 -- NPC336.scr:231
        end -- NPC336.scr:232
        if ctx:hasItem(565) then -- NPC336.scr:234-235
            ctx:state().nAbsolution = (tonumber(ctx:state().nAbsolution) or 0) + 1 -- NPC336.scr:236
        end -- NPC336.scr:237
        if ctx:hasItem(566) then -- NPC336.scr:239-240
            ctx:state().nAbsolution = (tonumber(ctx:state().nAbsolution) or 0) + 1 -- NPC336.scr:241
        end -- NPC336.scr:242
        if ctx:hasItem(567) then -- NPC336.scr:244-245
            ctx:state().nAbsolution = (tonumber(ctx:state().nAbsolution) or 0) + 1 -- NPC336.scr:246
        end -- NPC336.scr:247
        if ctx:condition("nAbsolution==5") then -- NPC336.scr:249
            if ctx:hasKey(389) then -- NPC336.scr:251-252
                do return ctx:exit("") end -- NPC336.scr:253
            end -- NPC336.scr:254
            ctx:takeItem(563) -- NPC336.scr:257
            ctx:takeItem(564) -- NPC336.scr:258
            ctx:takeItem(565) -- NPC336.scr:259
            ctx:takeItem(566) -- NPC336.scr:260
            ctx:takeItem(567) -- NPC336.scr:261
            ctx:giveKey(389) -- NPC336.scr:263
            ctx:object("AbsolutionFire"):trigger("On") -- NPC336.scr:264-265
            ctx:giveExp(52000) -- NPC336.scr:266
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC336.scr:267
        end -- NPC336.scr:268
    end -- NPC336.scr:269
    do return ctx:exit("") end -- NPC336.scr:270
end

script.labels["Init"] = function(ctx)
    -- NPC336.scr:275
    if ctx:condition("sLocation==Afterworld") then -- NPC336.scr:280
        ctx:onEvent("OnFoundPlayer", "DoRude") -- NPC336.scr:281
        do return ctx:exit("") end -- NPC336.scr:282
    end -- NPC336.scr:283
    do return ctx:exit("") end -- NPC336.scr:285
end

script.labels["OnDone"] = function(ctx)
    -- NPC336.scr:288
    ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC336.scr:291
    ctx:giveKey(381) -- NPC336.scr:292
    mm9.gosub(script, ctx, "end") -- NPC336.scr:293
    do return ctx:exit("") end -- NPC336.scr:294
end

script.labels["OnReborn"] = function(ctx)
    -- NPC336.scr:298
    ctx:object("RebirthFire"):trigger("On") -- NPC336.scr:301-302
    if not ctx:hasKey(391) then -- NPC336.scr:303-304
        ctx:giveExp(52000) -- NPC336.scr:305
    end -- NPC336.scr:306
    ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC336.scr:307
    ctx:giveKey(391) -- NPC336.scr:308
    ctx:giveKey(102) -- NPC336.scr:309
    do return ctx:exit("") end -- NPC336.scr:310
end

script.labels["Main"] = function(ctx)
    -- NPC336.scr:313
    -- traceon
    -- Don't Forget to Delete this!
    ctx:getParam(0, "sLocation") -- NPC336.scr:319
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC336.scr:320
    ctx:addTrigger("use", "OnUse") -- NPC336.scr:321
    ctx:onEvent("OnPostStartWorld", "Init") -- NPC336.scr:322
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- NPC336.scr:323
    ctx:onEvent("OnPostSaveLoad", "Init") -- NPC336.scr:324
    ctx:wait(1, .1, "Init") -- NPC336.scr:325
    ctx:addTrigger("Reborn", "OnReborn") -- NPC336.scr:326
    ctx:addTrigger("Done", "OnDone") -- NPC336.scr:327
    do return ctx:exit("") end -- NPC336.scr:328
end

return script
