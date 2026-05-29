-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC7.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "basewander.inc" }

-- NPC7.scr
-- timmy
-- handles Hjarrrand Fixer voice and quest stuff
-- flag variables
-- Init all the voice variables
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC7.scr:86
    if ctx:condition("Location==Refinery") then -- NPC7.scr:91
        if not ctx:hasKey(364) then -- NPC7.scr:92-93
            ctx:wait(1, .5, "Refinery2") -- NPC7.scr:94
            do return ctx:exit("") end -- NPC7.scr:95
        end -- NPC7.scr:96
    else -- NPC7.scr:97
        mm9.gosub(script, ctx, "Payment") -- NPC7.scr:98
    end -- NPC7.scr:99
    do return ctx:exit("") end -- NPC7.scr:100
end

script.labels["BD_OnDoor"] = function(ctx)
    -- NPC7.scr:104
    -- overloaded to open the door levers in the refinery
    ctx:set("g_sOpenString", "open") -- NPC7.scr:111
    do return mm9.gotoLabel(script, ctx, "BD_OnDoor") end -- NPC7.scr:113
    do return ctx:exit("") end -- NPC7.scr:114
end

script.labels["BD_DoorOpen"] = function(ctx)
    -- NPC7.scr:118
    mm9.gosub(script, ctx, "Refinery") -- NPC7.scr:121
    do return mm9.gotoLabel(script, ctx, "BD_DoorOpen") end -- NPC7.scr:122
    do return ctx:exit("") end -- NPC7.scr:123
end

script.labels["Payment"] = function(ctx)
    -- NPC7.scr:126
    if not ctx:hasKey(362) then -- NPC7.scr:128-129
        if ctx:hasKey(360) then -- NPC7.scr:131-132
            ctx:hasGold(1000, "g_ntemp") -- NPC7.scr:134
            if ctx:condition("g_ntemp==TRUE") then -- NPC7.scr:135
                ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC7.scr:136
                ctx:takeGold(1000) -- NPC7.scr:137
                ctx:giveKey(362) -- NPC7.scr:138
                ctx:takeKey(363) -- NPC7.scr:139
                do return ctx:exit("") end -- NPC7.scr:140
            else -- NPC7.scr:141
                ctx:giveKey(363) -- NPC7.scr:142
                ctx:randomInt(1, 2, "g_ntemp") -- NPC7.scr:143
                if ctx:condition("g_ntemp==1") then -- NPC7.scr:144
                    ctx:playSound("sVoice1", "DoNothing", 100, 240, "FALSE", 100) -- NPC7.scr:145
                else -- NPC7.scr:146
                    ctx:playSound("sVoice2", "DoNothing", 100, 240, "FALSE", 100) -- NPC7.scr:147
                end -- NPC7.scr:148
                do return ctx:exit("") end -- NPC7.scr:149
            end -- NPC7.scr:150
        end -- NPC7.scr:151
        if ctx:hasKey(361) then -- NPC7.scr:153-154
            ctx:hasGold(2000, "g_ntemp") -- NPC7.scr:156
            if ctx:condition("g_ntemp==TRUE") then -- NPC7.scr:157
                ctx:takeGold(2000) -- NPC7.scr:158
                ctx:giveKey(362) -- NPC7.scr:159
                ctx:takeKey(363) -- NPC7.scr:160
                ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC7.scr:161
                do return ctx:exit("") end -- NPC7.scr:162
            else -- NPC7.scr:163
                ctx:giveKey(363) -- NPC7.scr:164
                ctx:randomInt(1, 2, "g_ntemp") -- NPC7.scr:165
                if ctx:condition("g_ntemp==1") then -- NPC7.scr:166
                    ctx:playSound("sVoice1", "DoNothing", 100, 240, "FALSE", 100) -- NPC7.scr:167
                else -- NPC7.scr:168
                    ctx:playSound("sVoice2", "DoNothing", 100, 240, "FALSE", 100) -- NPC7.scr:169
                end -- NPC7.scr:170
                do return ctx:exit("") end -- NPC7.scr:171
            end -- NPC7.scr:172
        end -- NPC7.scr:173
    end -- NPC7.scr:174
    do return ctx:exit("") end -- NPC7.scr:177
end

script.labels["Refinery2"] = function(ctx)
    -- NPC7.scr:180
    -- starts his walk to the refinery.
    ctx:set("L_Marker", "MMarker1") -- NPC7.scr:185
end

-- getobjecthandle MMarker4 g_hobject
-- walkto g_hobject 8 Refinery
-- exit
script.labels["Refinery"] = function(ctx)
    -- NPC7.scr:191
    -- starts his walk to the refinery.
    ctx:state().g_hobject = ctx:objectOrNil("L_Marker") -- NPC7.scr:197
    ctx:self():walkTo(ctx:object("g_hobject"), 0, "OnArrive") -- NPC7.scr:198
    do return ctx:exit("") end -- NPC7.scr:199
end

script.labels["OnUse"] = function(ctx)
    -- NPC7.scr:205
    ctx:playSound("voices\\NPC\\NPC_007.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC7.scr:208
    do return ctx:exit("") end -- NPC7.scr:209
end

script.labels["OnArrive"] = function(ctx)
    -- NPC7.scr:212
    ctx:self():playAnimation("Rub_Beard", "OnArrive2") -- NPC7.scr:215
    do return ctx:exit("") end -- NPC7.scr:216
end

script.labels["OnArrive2"] = function(ctx)
    -- NPC7.scr:220
    if ctx:condition("counter!=3") then -- NPC7.scr:223
        if ctx:condition("L_Marker!=MMarker2") then -- NPC7.scr:224
            ctx:set("L_Marker", "MMarker2") -- NPC7.scr:225
            ctx:state().counter = (tonumber(ctx:state().counter) or 0) + 1 -- NPC7.scr:226
            ctx:wait(1, .5, "Refinery") -- NPC7.scr:227
            do return ctx:exit("") end -- NPC7.scr:228
        else -- NPC7.scr:229
            ctx:set("L_Marker", "MMarker1") -- NPC7.scr:230
            ctx:state().counter = (tonumber(ctx:state().counter) or 0) + 1 -- NPC7.scr:231
            ctx:wait(1, .5, "Refinery") -- NPC7.scr:232
            do return ctx:exit("") end -- NPC7.scr:233
        end -- NPC7.scr:234
    else -- NPC7.scr:235
        ctx:set("L_Marker", "Machine") -- NPC7.scr:236
        ctx:wait(1, .5, "OnMark") -- NPC7.scr:237
    end -- NPC7.scr:238
    do return ctx:exit("") end -- NPC7.scr:239
end

script.labels["OnMark"] = function(ctx)
    -- NPC7.scr:244
    ctx:state().g_hobject = ctx:objectOrNil("L_Marker") -- NPC7.scr:247
    ctx:self():walkTo(ctx:object("g_hobject"), 0, "OnMarkMachine") -- NPC7.scr:248
    do return ctx:exit("") end -- NPC7.scr:249
end

script.labels["OnMarkMachine"] = function(ctx)
    -- NPC7.scr:254
    ctx:giveKey(364) -- NPC7.scr:257
    ctx:state().g_hobject = ctx:objectOrNil("Slag") -- NPC7.scr:258
    ctx:self():faceObject(ctx:object("g_hobject"), 200, "DoNothing") -- NPC7.scr:259
    ctx:self():playAnimation("x", "DoNothing") -- NPC7.scr:260
    ctx:wait(1, 2, "WalkAway") -- NPC7.scr:261
    do return ctx:exit("") end -- NPC7.scr:262
end

script.labels["WalkAway"] = function(ctx)
    -- NPC7.scr:265
    ctx:set("L_marker", "MMarker3") -- NPC7.scr:268
    ctx:state().g_hobject = ctx:objectOrNil("L_Marker") -- NPC7.scr:269
    ctx:self():walkTo(ctx:object("g_hobject"), 0, "OnExit") -- NPC7.scr:270
    do return ctx:exit("") end -- NPC7.scr:271
end

script.labels["OnExit"] = function(ctx)
    -- NPC7.scr:274
    do return ctx:exit("") end -- NPC7.scr:277
end

script.labels["Init"] = function(ctx)
    -- NPC7.scr:280
    -- Checks to see where Hjarrand is and if
    -- he's supposed to be fixing the machine
    -- then deletes/undeletes him.
    mm9.gosub(script, ctx, "VoiceInit") -- NPC7.scr:289
    if ctx:condition("Location==Refinery") then -- NPC7.scr:291
        if ctx:hasKey(362) then -- NPC7.scr:292-293
            ctx:state().g_hobject = ctx:self() -- NPC7.scr:294
            ctx:self():setFlag("visible", true) -- NPC7.scr:295
            ctx:self():setFlag("solid", true) -- NPC7.scr:296
            ctx:self():setFlag("gravity", true) -- NPC7.scr:297
        else -- NPC7.scr:298
            ctx:state().g_hobject = ctx:self() -- NPC7.scr:299
            ctx:self():setFlag("visible", false) -- NPC7.scr:300
            ctx:self():setFlag("solid", false) -- NPC7.scr:301
            ctx:self():setFlag("gravity", false) -- NPC7.scr:302
        end -- NPC7.scr:303
    else -- NPC7.scr:304
        if not ctx:hasKey(362) then -- NPC7.scr:305-306
            ctx:state().g_hobject = ctx:self() -- NPC7.scr:307
            ctx:self():setFlag("visible", true) -- NPC7.scr:308
            ctx:self():setFlag("solid", true) -- NPC7.scr:309
            ctx:self():setFlag("gravity", true) -- NPC7.scr:310
        else -- NPC7.scr:311
            ctx:state().g_hobject = ctx:self() -- NPC7.scr:312
            ctx:self():setFlag("visible", false) -- NPC7.scr:313
            ctx:self():setFlag("solid", false) -- NPC7.scr:314
            ctx:self():setFlag("gravity", false) -- NPC7.scr:315
        end -- NPC7.scr:316
    end -- NPC7.scr:317
    do return ctx:exit("") end -- NPC7.scr:318
end

script.labels["VoiceInit"] = function(ctx)
    -- NPC7.scr:322
    ctx:getPcVoice("g_ntemp") -- NPC7.scr:327
    if ctx:condition("g_ntemp==0") then -- NPC7.scr:330
        ctx:set("sVoice1", "sAngryFa") -- NPC7.scr:331
        ctx:set("sVoice2", "sAngryFb") -- NPC7.scr:332
        do return ctx:exit("") end -- NPC7.scr:333
    end -- NPC7.scr:334
    if ctx:condition("g_ntemp==1") then -- NPC7.scr:336
        ctx:set("sVoice1", "sArrogantFa") -- NPC7.scr:337
        ctx:set("sVoice2", "sArrogantFb") -- NPC7.scr:338
        do return ctx:exit("") end -- NPC7.scr:339
    end -- NPC7.scr:340
    if ctx:condition("g_ntemp==2") then -- NPC7.scr:342
        ctx:set("sVoice1", "sAssertiveFa") -- NPC7.scr:343
        ctx:set("sVoice2", "sAssertiveFb") -- NPC7.scr:344
        do return ctx:exit("") end -- NPC7.scr:345
    end -- NPC7.scr:346
    if ctx:condition("g_ntemp==3") then -- NPC7.scr:348
        ctx:set("sVoice1", "sCowardlyFa") -- NPC7.scr:349
        ctx:set("sVoice2", "sCowardlyFb") -- NPC7.scr:350
        do return ctx:exit("") end -- NPC7.scr:351
    end -- NPC7.scr:352
    if ctx:condition("g_ntemp==4") then -- NPC7.scr:354
        ctx:set("sVoice1", "sDimFa") -- NPC7.scr:355
        ctx:set("sVoice2", "sDimFb") -- NPC7.scr:356
        do return ctx:exit("") end -- NPC7.scr:357
    end -- NPC7.scr:358
    if ctx:condition("g_ntemp==5") then -- NPC7.scr:360
        ctx:set("sVoice1", "sHappyFa") -- NPC7.scr:361
        ctx:set("sVoice2", "sHappyFb") -- NPC7.scr:362
        do return ctx:exit("") end -- NPC7.scr:363
    end -- NPC7.scr:364
    if ctx:condition("g_ntemp==6") then -- NPC7.scr:366
        ctx:set("sVoice1", "sSarcasticFa") -- NPC7.scr:367
        ctx:set("sVoice2", "sSarcasticFb") -- NPC7.scr:368
        do return ctx:exit("") end -- NPC7.scr:369
    end -- NPC7.scr:370
    if ctx:condition("g_ntemp==7") then -- NPC7.scr:372
        ctx:set("sVoice1", "sLichFa") -- NPC7.scr:373
        ctx:set("sVoice2", "sLichFb") -- NPC7.scr:374
        do return ctx:exit("") end -- NPC7.scr:375
    end -- NPC7.scr:376
    if ctx:condition("g_ntemp==8") then -- NPC7.scr:378
        ctx:set("sVoice1", "sHalfOrcLichFa") -- NPC7.scr:379
        ctx:set("sVoice2", "sHalfOrcLichFb") -- NPC7.scr:380
        do return ctx:exit("") end -- NPC7.scr:381
    end -- NPC7.scr:382
    if ctx:condition("g_ntemp==9") then -- NPC7.scr:384
        ctx:set("sVoice1", "sAngryMa") -- NPC7.scr:385
        ctx:set("sVoice2", "sAngryMb") -- NPC7.scr:386
        do return ctx:exit("") end -- NPC7.scr:387
    end -- NPC7.scr:388
    if ctx:condition("g_ntemp==10") then -- NPC7.scr:390
        ctx:set("sVoice1", "sArrogantMa") -- NPC7.scr:391
        ctx:set("sVoice2", "sArrogantMb") -- NPC7.scr:392
        do return ctx:exit("") end -- NPC7.scr:393
    end -- NPC7.scr:394
    if ctx:condition("g_ntemp==11") then -- NPC7.scr:396
        ctx:set("sVoice1", "sAssertiveMa") -- NPC7.scr:397
        ctx:set("sVoice2", "sAssertiveMb") -- NPC7.scr:398
    end -- NPC7.scr:399
    if ctx:condition("g_ntemp==12") then -- NPC7.scr:401
        ctx:set("sVoice1", "sCowardlyMa") -- NPC7.scr:402
        ctx:set("sVoice2", "sCowardlyMb") -- NPC7.scr:403
        do return ctx:exit("") end -- NPC7.scr:404
    end -- NPC7.scr:405
    if ctx:condition("g_ntemp==13") then -- NPC7.scr:407
        ctx:set("sVoice1", "sDimMa") -- NPC7.scr:408
        ctx:set("sVoice2", "sDimMb") -- NPC7.scr:409
        do return ctx:exit("") end -- NPC7.scr:410
    end -- NPC7.scr:411
    if ctx:condition("g_ntemp==14") then -- NPC7.scr:413
        ctx:set("sVoice1", "sHappyMa") -- NPC7.scr:414
        ctx:set("sVoice2", "sHappyMb") -- NPC7.scr:415
        do return ctx:exit("") end -- NPC7.scr:416
    end -- NPC7.scr:417
    if ctx:condition("g_ntemp==15") then -- NPC7.scr:419
        ctx:set("sVoice1", "sSarcasticMa") -- NPC7.scr:420
        ctx:set("sVoice2", "sSarcasticMb") -- NPC7.scr:421
        do return ctx:exit("") end -- NPC7.scr:422
    end -- NPC7.scr:423
    if ctx:condition("g_ntemp==16") then -- NPC7.scr:425
        ctx:set("sVoice1", "sLichMa") -- NPC7.scr:426
        ctx:set("sVoice2", "sLichMb") -- NPC7.scr:427
        do return ctx:exit("") end -- NPC7.scr:428
    end -- NPC7.scr:429
    if ctx:condition("g_ntemp==17") then -- NPC7.scr:431
        ctx:set("sVoice1", "sHalfOrcLichMa") -- NPC7.scr:432
        ctx:set("sVoice2", "sHalfOrcLichMb") -- NPC7.scr:433
        do return ctx:exit("") end -- NPC7.scr:434
    end -- NPC7.scr:435
    do return ctx:exit("") end -- NPC7.scr:437
end

script.labels["Main"] = function(ctx)
    -- NPC7.scr:440
    -- traceon
    -- Don't Forget to Delete this!
    ctx:getParam(0, "Location") -- NPC7.scr:446
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC7.scr:447
    mm9.gosub(script, ctx, "BaseDoorInit") -- NPC7.scr:448
    ctx:addTrigger("Use", "OnUse") -- NPC7.scr:450
    ctx:onEvent("OnPostStartWorld", "Init") -- NPC7.scr:451
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- NPC7.scr:452
    ctx:onEvent("OnPostSaveLoad", "Init") -- NPC7.scr:453
    ctx:wait(1, .1, "Init") -- NPC7.scr:454
    do return ctx:exit("") end -- NPC7.scr:457
end

return script
