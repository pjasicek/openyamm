-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SIXFIRES.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "Svenshowtake.inc" }

-- SixFires.inc
-- timmy
-- handles the Six Fires of Penance stuff
-- flag variables
script.labels["Guilt"] = function(ctx)
    -- SIXFIRES.inc:51
    if ctx:hasKey(381) then -- SIXFIRES.inc:54-55
        do return ctx:exit("") end -- SIXFIRES.inc:56
    end -- SIXFIRES.inc:57
    ctx:screenFadeOut(1) -- SIXFIRES.inc:58
    ctx:wait(1, 1, "FadeIn") -- SIXFIRES.inc:59
    do return ctx:exit("") end -- SIXFIRES.inc:61
end

script.labels["Spawn"] = function(ctx)
    -- SIXFIRES.inc:67
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("sBadGuys"):pos() -- SIXFIRES.inc:76-77
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterB") -- SIXFIRES.inc:78
    ctx:state().hMonsterB = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterB") -- SIXFIRES.inc:79
    ctx:state().hMonsterC = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterC") -- SIXFIRES.inc:80
    ctx:state().hMonsterD = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterC") -- SIXFIRES.inc:81
    -- Spawn hMonsterB Xpos YPos ZPos sMonsterB
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("sGoodGuys"):pos() -- SIXFIRES.inc:85-86
    ctx:state().hGoodGuyA = ctx:spawn("Xpos", "YPos", "ZPos", "sGoodGuyA") -- SIXFIRES.inc:89
    ctx:state().hGoodGuyB = ctx:spawn("Xpos", "YPos", "ZPos", "sGoodGuya") -- SIXFIRES.inc:90
    do return ctx:exit("") end -- SIXFIRES.inc:93
end

script.labels["FadeIn"] = function(ctx)
    -- SIXFIRES.inc:98
    ctx:letterBox("true") -- SIXFIRES.inc:101
    local object = ctx:object("Camera9") -- SIXFIRES.inc:102
    object:trigger("On") -- SIXFIRES.inc:103
    object:trigger("play") -- SIXFIRES.inc:104
    ctx:screenFadeIn(1) -- SIXFIRES.inc:105
    do return ctx:exit("") end -- SIXFIRES.inc:107
end

script.labels["GoodGuys"] = function(ctx)
    -- SIXFIRES.inc:110
    ctx:state().SCRIPT = " ScriptName Hate.scr" -- SIXFIRES.inc:113
    ctx:set("sGoodGuyA", "sGoodGuyA + Script") -- SIXFIRES.inc:115
    ctx:set("sGoodGuyB", "sGoodGuyB + Script") -- SIXFIRES.inc:116
    ctx:set("sGoodGuyC", "sGoodGuyc + Script") -- SIXFIRES.inc:117
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("sGoodGuys"):pos() -- SIXFIRES.inc:121-122
    -- Spawn hMonsterC Xpos YPos ZPos sKira
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sGoodGuyA") -- SIXFIRES.inc:125
    ctx:state().hMonsterB = ctx:spawn("Xpos", "YPos", "ZPos", "sGoodGuyB") -- SIXFIRES.inc:126
    ctx:state().hMonsterB = ctx:spawn("Xpos", "YPos", "ZPos", "sGoodGuyB") -- SIXFIRES.inc:127
    ctx:state().hMonsterB = ctx:spawn("Xpos", "YPos", "ZPos", "sGoodGuyC") -- SIXFIRES.inc:128
    ctx:wait(1, 5, "End") -- SIXFIRES.inc:130
    do return ctx:exit("") end -- SIXFIRES.inc:131
end

script.labels["End"] = function(ctx)
    -- SIXFIRES.inc:134
    ctx:screenFadeOut(2) -- SIXFIRES.inc:139
    ctx:wait(1, 2, "FadeIn2") -- SIXFIRES.inc:140
    do return ctx:exit("") end -- SIXFIRES.inc:141
end

script.labels["FadeIn2"] = function(ctx)
    -- SIXFIRES.inc:144
    ctx:letterBox("false") -- SIXFIRES.inc:147
    ctx:object("Camera9"):trigger("Off") -- SIXFIRES.inc:148-149
    ctx:screenFadeIn(1) -- SIXFIRES.inc:150
    ctx:onEvent("OnFoundPlayer", "DoRude") -- SIXFIRES.inc:151
    do return ctx:exit("") end -- SIXFIRES.inc:152
end

script.labels["Confession"] = function(ctx)
    -- SIXFIRES.inc:155
    if ctx:hasKey(383) then -- SIXFIRES.inc:158-159
        ctx:object("BjarniThorvaldssen0"):setFlag("visible", false) -- SIXFIRES.inc:160-161
        ctx:object("KiratheCold0"):setFlag("visible", false) -- SIXFIRES.inc:162-163
        ctx:object("MarkeltheGreat0"):setFlag("visible", false) -- SIXFIRES.inc:164-165
        ctx:object("SigmundtheStressed0"):setFlag("visible", false) -- SIXFIRES.inc:166-167
        ctx:object("SvenSvenssen0"):setFlag("visible", false) -- SIXFIRES.inc:168-169
        ctx:object("TryggvaRavenlocks0"):setFlag("visible", false) -- SIXFIRES.inc:170-171
        do return ctx:exit("") end -- SIXFIRES.inc:172
        do return ctx:exit("") end -- SIXFIRES.inc:173
    end -- SIXFIRES.inc:174
    ctx:object("BjarniThorvaldssen0"):setFlag("visible", true) -- SIXFIRES.inc:176-177
    ctx:object("KiratheCold0"):setFlag("visible", true) -- SIXFIRES.inc:178-179
    ctx:object("MarkeltheGreat0"):setFlag("visible", true) -- SIXFIRES.inc:180-181
    ctx:object("SigmundtheStressed0"):setFlag("visible", true) -- SIXFIRES.inc:182-183
    ctx:object("SvenSvenssen0"):setFlag("visible", true) -- SIXFIRES.inc:184-185
    ctx:object("TryggvaRavenlocks0"):setFlag("visible", true) -- SIXFIRES.inc:186-187
    do return ctx:exit("") end -- SIXFIRES.inc:188
end

script.labels["Suffering"] = function(ctx)
    -- SIXFIRES.inc:191
    if ctx:hasKey(491) then -- SIXFIRES.inc:194-195
        do return ctx:exit("") end -- SIXFIRES.inc:196
    end -- SIXFIRES.inc:197
    if ctx:hasKey(385) then -- SIXFIRES.inc:200-201
        if not ctx:hasKey(491) then -- SIXFIRES.inc:202-203
            ctx:giveExp(52000) -- SIXFIRES.inc:204
        end -- SIXFIRES.inc:205
        ctx:giveKey(491) -- SIXFIRES.inc:206
        -- take poisoning and disease away
        ctx:clearCondition(13) -- SIXFIRES.inc:208
        ctx:object("sufferingFire"):trigger("On") -- SIXFIRES.inc:209-210
        ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- SIXFIRES.inc:212
        do return ctx:exit("") end -- SIXFIRES.inc:213
    end -- SIXFIRES.inc:214
    ctx:wait(1, 5, "Questioner") -- SIXFIRES.inc:216
    do return ctx:exit("") end -- SIXFIRES.inc:218
end

script.labels["Questioner"] = function(ctx)
    -- SIXFIRES.inc:221
    -- poison and disease player
    ctx:setCondition(13) -- SIXFIRES.inc:226
    ctx:doRude(432) -- SIXFIRES.inc:227
    do return ctx:exit("") end -- SIXFIRES.inc:228
end

script.labels["Retribution"] = function(ctx)
    -- SIXFIRES.inc:232
    if ctx:hasKey(387) then -- SIXFIRES.inc:235-236
        do return ctx:exit("") end -- SIXFIRES.inc:237
    end -- SIXFIRES.inc:238
    if ctx:hasKey(5021) then -- SIXFIRES.inc:240-241
        do return ctx:exit("") end -- SIXFIRES.inc:242
    end -- SIXFIRES.inc:243
    ctx:giveKey(5021) -- SIXFIRES.inc:245
    ctx:object("ForadDarre0"):setFlag("visible", true) -- SIXFIRES.inc:247-248
    ctx:set("sBadGuys", "BadGuys0") -- SIXFIRES.inc:250
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("sBadGuys"):pos() -- SIXFIRES.inc:252-253
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterB") -- SIXFIRES.inc:254
    ctx:state().hMonsterB = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterB") -- SIXFIRES.inc:255
    ctx:state().hMonsterC = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterC") -- SIXFIRES.inc:256
    ctx:state().hMonsterD = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterC") -- SIXFIRES.inc:257
    ctx:state().hMonsterB = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterB") -- SIXFIRES.inc:258
    ctx:set("sBadGuys", "BadGuys1") -- SIXFIRES.inc:260
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("sBadGuys"):pos() -- SIXFIRES.inc:262-263
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterB") -- SIXFIRES.inc:264
    ctx:state().hMonsterB = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterB") -- SIXFIRES.inc:265
    ctx:state().hMonsterC = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterC") -- SIXFIRES.inc:266
    ctx:state().hMonsterD = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterC") -- SIXFIRES.inc:267
    ctx:state().hMonsterB = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterB") -- SIXFIRES.inc:268
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterB") -- SIXFIRES.inc:269
    ctx:state().hMonsterB = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterB") -- SIXFIRES.inc:270
    do return ctx:exit("") end -- SIXFIRES.inc:271
end

script.labels["Absolution"] = function(ctx)
    -- SIXFIRES.inc:274
    ctx:object("retributionFire"):trigger("On") -- SIXFIRES.inc:277-278
    if ctx:hasKey(492) then -- SIXFIRES.inc:281-282
        do return ctx:exit("") end -- SIXFIRES.inc:283
    end -- SIXFIRES.inc:284
    ctx:giveExp(52000) -- SIXFIRES.inc:286
    ctx:giveKey(492) -- SIXFIRES.inc:287
    ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- SIXFIRES.inc:289
    ctx:state().ShowAll = true -- SIXFIRES.inc:291
    mm9.gosub(script, ctx, "removeall") -- SIXFIRES.inc:292
    ctx:object("svensword"):setFlag("visible", true) -- SIXFIRES.inc:294-295
    ctx:object("Bjarnisword"):setFlag("visible", true) -- SIXFIRES.inc:297-298
    ctx:object("Sigmundsword"):setFlag("visible", true) -- SIXFIRES.inc:300-301
    ctx:object("TryygvaSword"):setFlag("visible", true) -- SIXFIRES.inc:303-304
    ctx:object("Kirasword"):setFlag("visible", true) -- SIXFIRES.inc:306-307
    ctx:set("sMonsterA", "Zombie") -- SIXFIRES.inc:309
    ctx:set("sMonsterB", "Ghast") -- SIXFIRES.inc:310
    ctx:set("sMonsterC", "Fright") -- SIXFIRES.inc:311
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("Badguys0"):pos() -- SIXFIRES.inc:313-314
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterA") -- SIXFIRES.inc:315
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("BadGuys1"):pos() -- SIXFIRES.inc:318-319
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterB") -- SIXFIRES.inc:320
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("GoodGuys0"):pos() -- SIXFIRES.inc:323-324
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterC") -- SIXFIRES.inc:325
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterC") -- SIXFIRES.inc:326
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterC") -- SIXFIRES.inc:327
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterC") -- SIXFIRES.inc:328
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterC") -- SIXFIRES.inc:329
    do return ctx:exit("") end -- SIXFIRES.inc:331
end

script.labels["Rebirth"] = function(ctx)
    -- SIXFIRES.inc:333
    ctx:object("ExitTrigger1"):trigger("On") -- SIXFIRES.inc:336-337
    ctx:set("sMonsterA", "Zombie") -- SIXFIRES.inc:339
    ctx:set("sMonsterB", "Ghast") -- SIXFIRES.inc:340
    ctx:set("sMonsterC", "Fright") -- SIXFIRES.inc:341
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("Badguys0"):pos() -- SIXFIRES.inc:343-344
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterA") -- SIXFIRES.inc:345
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("BadGuys1"):pos() -- SIXFIRES.inc:348-349
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterB") -- SIXFIRES.inc:350
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("GoodGuys0"):pos() -- SIXFIRES.inc:353-354
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterC") -- SIXFIRES.inc:355
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterC") -- SIXFIRES.inc:356
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterC") -- SIXFIRES.inc:357
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterC") -- SIXFIRES.inc:358
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterC") -- SIXFIRES.inc:359
    do return ctx:exit("") end -- SIXFIRES.inc:361
end

return script
