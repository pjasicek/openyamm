-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "THJORGARDGAMESCOMMON.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 12, path = "NoGold.inc" }

-- ThjorgardGamesCommon.inc
-- by SJR
-- 01-04-02
-- Purpose:
-- a.) keep track of games won
-- b.)	sell, redeem, and check ticket
-- c.) give out prizes and assc. keys
-- Thjorgard and Guberlang games should channel
-- everything through this.
-- MISC
-- TEXT
-- KEYS
script.labels["CheckGameTicket"] = function(ctx)
    -- THJORGARDGAMESCOMMON.inc:61
    -- checks for ticket key
    ctx:hasItem("TICKET_ITEM", "THJORGARD_RESULT") -- THJORGARDGAMESCOMMON.inc:64
    if ctx:condition("THJORGARD_RESULT==0") then -- THJORGARDGAMESCOMMON.inc:65
        ctx:rolloverText("TEXT_NEEDTICKET", 1, 3000, 2000) -- THJORGARDGAMESCOMMON.inc:66
    end -- THJORGARDGAMESCOMMON.inc:67
    do return ctx:exit(1) end -- THJORGARDGAMESCOMMON.inc:69
end

script.labels["SellGameTicket"] = function(ctx)
    -- THJORGARDGAMESCOMMON.inc:72
    -- take gold, give ticket and rules
    ctx:hasGold("TICKET_COST", "thjorgard_nTemp") -- THJORGARDGAMESCOMMON.inc:75
    if ctx:condition("thjorgard_nTemp==1") then -- THJORGARDGAMESCOMMON.inc:76
        ctx:playSound("sounds\\events\\gold01.wav", "DoNothing", 1, 500, 0, 100) -- THJORGARDGAMESCOMMON.inc:77
        ctx:rolloverText("TEXT_BOUGHTTICKET", 1, 3000, 2000) -- THJORGARDGAMESCOMMON.inc:78
        ctx:takeGold("TICKET_COST") -- THJORGARDGAMESCOMMON.inc:79
        ctx:giveItem("TICKET_ITEM") -- THJORGARDGAMESCOMMON.inc:80
        -- give them the rules
        ctx:hasItem("RULEBOOK_ITEM", "thjorgard_nTemp") -- THJORGARDGAMESCOMMON.inc:83
        if ctx:condition("thjorgard_nTemp==0") then -- THJORGARDGAMESCOMMON.inc:84
            ctx:giveItem("RULEBOOK_ITEM") -- THJORGARDGAMESCOMMON.inc:85
        end -- THJORGARDGAMESCOMMON.inc:86
    else -- THJORGARDGAMESCOMMON.inc:87
        mm9.gosub(script, ctx, "NoGold") -- THJORGARDGAMESCOMMON.inc:88
    end -- THJORGARDGAMESCOMMON.inc:89
    do return ctx:exit(1) end -- THJORGARDGAMESCOMMON.inc:91
end

script.labels["SellBatchTickets"] = function(ctx)
    -- THJORGARDGAMESCOMMON.inc:94
    -- take gold, give 10 tickets and rules
    ctx:hasGold("TICKET_BATCH_COST", "thjorgard_nTemp") -- THJORGARDGAMESCOMMON.inc:97
    if ctx:condition("thjorgard_nTemp==1") then -- THJORGARDGAMESCOMMON.inc:98
        ctx:playSound("sounds\\events\\gold01.wav", "DoNothing", 1, 500, 0, 100) -- THJORGARDGAMESCOMMON.inc:99
        ctx:rolloverText("TEXT_BOUGHTBATCH", 1, 3000, 2000) -- THJORGARDGAMESCOMMON.inc:100
        ctx:hasItem("RULEBOOK_ITEM", "thjorgard_nTemp") -- THJORGARDGAMESCOMMON.inc:101
        if ctx:condition("thjorgard_nTemp==0") then -- THJORGARDGAMESCOMMON.inc:102
            ctx:giveItem("RULEBOOK_ITEM") -- THJORGARDGAMESCOMMON.inc:103
        end -- THJORGARDGAMESCOMMON.inc:104
        ctx:takeGold("TICKET_BATCH_COST") -- THJORGARDGAMESCOMMON.inc:105
        ctx:giveItem("TICKET_ITEM") -- THJORGARDGAMESCOMMON.inc:107
        ctx:giveItem("TICKET_ITEM") -- THJORGARDGAMESCOMMON.inc:108
        ctx:giveItem("TICKET_ITEM") -- THJORGARDGAMESCOMMON.inc:109
        ctx:giveItem("TICKET_ITEM") -- THJORGARDGAMESCOMMON.inc:110
        ctx:giveItem("TICKET_ITEM") -- THJORGARDGAMESCOMMON.inc:111
        ctx:giveItem("TICKET_ITEM") -- THJORGARDGAMESCOMMON.inc:113
        ctx:giveItem("TICKET_ITEM") -- THJORGARDGAMESCOMMON.inc:114
        ctx:giveItem("TICKET_ITEM") -- THJORGARDGAMESCOMMON.inc:115
        ctx:giveItem("TICKET_ITEM") -- THJORGARDGAMESCOMMON.inc:116
        ctx:giveItem("TICKET_ITEM") -- THJORGARDGAMESCOMMON.inc:117
    else -- THJORGARDGAMESCOMMON.inc:118
        mm9.gosub(script, ctx, "NoGold") -- THJORGARDGAMESCOMMON.inc:119
    end -- THJORGARDGAMESCOMMON.inc:120
    do return ctx:exit(1) end -- THJORGARDGAMESCOMMON.inc:122
end

script.labels["TakeGameTicket"] = function(ctx)
    -- THJORGARDGAMESCOMMON.inc:125
    -- take ticket item, and key if last one
    ctx:hasItem("TICKET_ITEM", "thjorgard_nTemp") -- THJORGARDGAMESCOMMON.inc:128
    if ctx:condition("thjorgard_nTemp==1") then -- THJORGARDGAMESCOMMON.inc:129
        ctx:takeItem("TICKET_ITEM") -- THJORGARDGAMESCOMMON.inc:130
        ctx:rolloverText("TEXT_USEDTICKET", 1, 3000, 2000) -- THJORGARDGAMESCOMMON.inc:131
    end -- THJORGARDGAMESCOMMON.inc:132
    do return ctx:exit(1) end -- THJORGARDGAMESCOMMON.inc:134
end

script.labels["GiveThjorgardPrize"] = function(ctx)
    -- THJORGARDGAMESCOMMON.inc:137
    -- completed quest- give prize, key, exp
    ctx:giveKey("THJORGARD_ALL") -- THJORGARDGAMESCOMMON.inc:140
    ctx:rolloverText("TEXT_STUFFEDDRAGON", 1, 3000, 2000) -- THJORGARDGAMESCOMMON.inc:142
    ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 1, 1000, 0, 100) -- THJORGARDGAMESCOMMON.inc:143
    ctx:giveExp("PRIZE_THJORGARD_EXP") -- THJORGARDGAMESCOMMON.inc:145
    ctx:giveItem("PRIZE_STUFFED_DRAGON") -- THJORGARDGAMESCOMMON.inc:146
    ctx:giveKey("YRSAS_QUEST_COMPLETED") -- THJORGARDGAMESCOMMON.inc:147
    do return ctx:exit(1) end -- THJORGARDGAMESCOMMON.inc:149
end

script.labels["GiveGuberlandPrize"] = function(ctx)
    -- THJORGARDGAMESCOMMON.inc:152
    -- just give random prize each time
    ctx:giveKey("GUBERLAND_ALL") -- THJORGARDGAMESCOMMON.inc:155
    ctx:randomInt("PRIZE_GUBER_MIN", "PRIZE_GUBER_MAX", "thjorgard_nTemp") -- THJORGARDGAMESCOMMON.inc:157
    ctx:giveItem("thjorgard_nTemp") -- THJORGARDGAMESCOMMON.inc:158
    do return ctx:exit(1) end -- THJORGARDGAMESCOMMON.inc:160
end

script.labels["CheckThjorgardWins"] = function(ctx)
    -- THJORGARDGAMESCOMMON.inc:163
    -- checks to see if all games won
    ctx:rolloverText("TEXT_VICTORY", 1, 3000, 2000) -- THJORGARDGAMESCOMMON.inc:166
    ctx:hasKey("THJORGARD_ALL", "thjorgard_nTemp") -- THJORGARDGAMESCOMMON.inc:168
    if ctx:condition("thjorgard_nTemp==1") then -- THJORGARDGAMESCOMMON.inc:169
        do return ctx:exit(1) end -- THJORGARDGAMESCOMMON.inc:170
    end -- THJORGARDGAMESCOMMON.inc:171
    ctx:hasKey("THJORGARD_STONES", "thjorgard_nTemp") -- THJORGARDGAMESCOMMON.inc:173
    if ctx:condition("thjorgard_nTemp==1") then -- THJORGARDGAMESCOMMON.inc:174
        ctx:hasKey("THJORGARD_BOAT", "thjorgard_nTemp") -- THJORGARDGAMESCOMMON.inc:175
        if ctx:condition("thjorgard_nTemp==1") then -- THJORGARDGAMESCOMMON.inc:176
            ctx:hasKey("THJORGARD_RUNES", "thjorgard_nTemp") -- THJORGARDGAMESCOMMON.inc:177
            if ctx:condition("thjorgard_nTemp==1") then -- THJORGARDGAMESCOMMON.inc:178
                ctx:hasKey("THJORGARD_HONKY", "thjorgard_nTemp") -- THJORGARDGAMESCOMMON.inc:179
                if ctx:condition("thjorgard_nTemp==1") then -- THJORGARDGAMESCOMMON.inc:180
                    ctx:hasKey("THJORGARD_BELL", "thjorgard_nTemp") -- THJORGARDGAMESCOMMON.inc:181
                    if ctx:condition("thjorgard_nTemp==1") then -- THJORGARDGAMESCOMMON.inc:182
                        ctx:hasKey("THJORGARD_MIGHT", "thjorgard_nTemp") -- THJORGARDGAMESCOMMON.inc:183
                        if ctx:condition("thjorgard_nTemp==1") then -- THJORGARDGAMESCOMMON.inc:184
                            -- if player won all games AND on Yrsa's quest
                            ctx:hasKey("YRSAS_QUEST_PENDING", "thjorgard_nTemp") -- THJORGARDGAMESCOMMON.inc:187
                            if ctx:condition("thjorgard_nTemp==1") then -- THJORGARDGAMESCOMMON.inc:188
                                ctx:wait(17, 2, "GiveThjorgardPrize") -- THJORGARDGAMESCOMMON.inc:189
                            end -- THJORGARDGAMESCOMMON.inc:190
                        end -- THJORGARDGAMESCOMMON.inc:192
                    end -- THJORGARDGAMESCOMMON.inc:193
                end -- THJORGARDGAMESCOMMON.inc:194
            end -- THJORGARDGAMESCOMMON.inc:195
        end -- THJORGARDGAMESCOMMON.inc:196
    end -- THJORGARDGAMESCOMMON.inc:197
    do return ctx:exit(1) end -- THJORGARDGAMESCOMMON.inc:199
end

script.labels["CheckGuberlandWins"] = function(ctx)
    -- THJORGARDGAMESCOMMON.inc:202
    ctx:rolloverText("TEXT_VICTORY", 1, 3000, 2000) -- THJORGARDGAMESCOMMON.inc:204
    ctx:hasKey("GUBERLAND_ALL", "thjorgard_nTemp") -- THJORGARDGAMESCOMMON.inc:206
    if ctx:condition("thjorgard_nTemp==1") then -- THJORGARDGAMESCOMMON.inc:207
        -- dont exit, no quest prize given
    end -- THJORGARDGAMESCOMMON.inc:209
    mm9.gosub(script, ctx, "GiveGuberlandPrize") -- THJORGARDGAMESCOMMON.inc:211
    do return ctx:exit(1) end -- THJORGARDGAMESCOMMON.inc:213
end

script.labels["RecordStonesWin"] = function(ctx)
    -- THJORGARDGAMESCOMMON.inc:216
    ctx:getConsoleNumVar("GUBERLAND_WIN_TYPE", "thjorgard_nTemp") -- THJORGARDGAMESCOMMON.inc:218
    if ctx:condition("thjorgard_nTemp==1") then -- THJORGARDGAMESCOMMON.inc:219
        ctx:giveKey("GUBERLAND_STONES") -- THJORGARDGAMESCOMMON.inc:220
        mm9.gosub(script, ctx, "CheckGuberlandWins") -- THJORGARDGAMESCOMMON.inc:221
    else -- THJORGARDGAMESCOMMON.inc:222
        ctx:giveKey("THJORGARD_STONES") -- THJORGARDGAMESCOMMON.inc:223
        mm9.gosub(script, ctx, "CheckThjorgardWins") -- THJORGARDGAMESCOMMON.inc:224
    end -- THJORGARDGAMESCOMMON.inc:225
    do return ctx:exit(1) end -- THJORGARDGAMESCOMMON.inc:227
end

script.labels["RecordBoatWin"] = function(ctx)
    -- THJORGARDGAMESCOMMON.inc:230
    ctx:getConsoleNumVar("GUBERLAND_WIN_TYPE", "thjorgard_nTemp") -- THJORGARDGAMESCOMMON.inc:232
    if ctx:condition("thjorgard_nTemp==1") then -- THJORGARDGAMESCOMMON.inc:233
        ctx:giveKey("GUBERLAND_BOAT") -- THJORGARDGAMESCOMMON.inc:234
        mm9.gosub(script, ctx, "CheckGuberlandWins") -- THJORGARDGAMESCOMMON.inc:235
    else -- THJORGARDGAMESCOMMON.inc:236
        ctx:giveKey("THJORGARD_BOAT") -- THJORGARDGAMESCOMMON.inc:237
        mm9.gosub(script, ctx, "CheckThjorgardWins") -- THJORGARDGAMESCOMMON.inc:238
    end -- THJORGARDGAMESCOMMON.inc:239
    do return ctx:exit(1) end -- THJORGARDGAMESCOMMON.inc:241
end

script.labels["RecordHonkyWin"] = function(ctx)
    -- THJORGARDGAMESCOMMON.inc:244
    ctx:getConsoleNumVar("GUBERLAND_WIN_TYPE", "thjorgard_nTemp") -- THJORGARDGAMESCOMMON.inc:246
    if ctx:condition("thjorgard_nTemp==1") then -- THJORGARDGAMESCOMMON.inc:247
        ctx:giveKey("GUBERLAND_HONKY") -- THJORGARDGAMESCOMMON.inc:248
        mm9.gosub(script, ctx, "CheckGuberlandWins") -- THJORGARDGAMESCOMMON.inc:249
    else -- THJORGARDGAMESCOMMON.inc:250
        ctx:giveKey("THJORGARD_HONKY") -- THJORGARDGAMESCOMMON.inc:251
        mm9.gosub(script, ctx, "CheckThjorgardWins") -- THJORGARDGAMESCOMMON.inc:252
    end -- THJORGARDGAMESCOMMON.inc:253
    do return ctx:exit(1) end -- THJORGARDGAMESCOMMON.inc:255
end

script.labels["RecordRunesWin"] = function(ctx)
    -- THJORGARDGAMESCOMMON.inc:258
    ctx:getConsoleNumVar("GUBERLAND_WIN_TYPE", "thjorgard_nTemp") -- THJORGARDGAMESCOMMON.inc:260
    if ctx:condition("thjorgard_nTemp==1") then -- THJORGARDGAMESCOMMON.inc:261
        ctx:giveKey("GUBERLAND_RUNES") -- THJORGARDGAMESCOMMON.inc:262
        mm9.gosub(script, ctx, "CheckGuberlandWins") -- THJORGARDGAMESCOMMON.inc:263
    else -- THJORGARDGAMESCOMMON.inc:264
        ctx:giveKey("THJORGARD_RUNES") -- THJORGARDGAMESCOMMON.inc:265
        mm9.gosub(script, ctx, "CheckThjorgardWins") -- THJORGARDGAMESCOMMON.inc:266
    end -- THJORGARDGAMESCOMMON.inc:267
    do return ctx:exit(1) end -- THJORGARDGAMESCOMMON.inc:269
end

script.labels["RecordBellWin"] = function(ctx)
    -- THJORGARDGAMESCOMMON.inc:272
    ctx:getConsoleNumVar("GUBERLAND_WIN_TYPE", "thjorgard_nTemp") -- THJORGARDGAMESCOMMON.inc:274
    if ctx:condition("thjorgard_nTemp==1") then -- THJORGARDGAMESCOMMON.inc:275
        ctx:giveKey("GUBERLAND_BELL") -- THJORGARDGAMESCOMMON.inc:276
        mm9.gosub(script, ctx, "CheckGuberlandWins") -- THJORGARDGAMESCOMMON.inc:277
    else -- THJORGARDGAMESCOMMON.inc:278
        ctx:giveKey("THJORGARD_BELL") -- THJORGARDGAMESCOMMON.inc:279
        mm9.gosub(script, ctx, "CheckThjorgardWins") -- THJORGARDGAMESCOMMON.inc:280
    end -- THJORGARDGAMESCOMMON.inc:281
    do return ctx:exit(1) end -- THJORGARDGAMESCOMMON.inc:283
end

script.labels["RecordMightWin"] = function(ctx)
    -- THJORGARDGAMESCOMMON.inc:286
    ctx:getConsoleNumVar("GUBERLAND_WIN_TYPE", "thjorgard_nTemp") -- THJORGARDGAMESCOMMON.inc:288
    if ctx:condition("thjorgard_nTemp==1") then -- THJORGARDGAMESCOMMON.inc:289
        ctx:giveKey("GUBERLAND_MIGHT") -- THJORGARDGAMESCOMMON.inc:290
        mm9.gosub(script, ctx, "CheckGuberlandWins") -- THJORGARDGAMESCOMMON.inc:291
    else -- THJORGARDGAMESCOMMON.inc:292
        ctx:giveKey("THJORGARD_MIGHT") -- THJORGARDGAMESCOMMON.inc:293
        mm9.gosub(script, ctx, "CheckThjorgardWins") -- THJORGARDGAMESCOMMON.inc:294
    end -- THJORGARDGAMESCOMMON.inc:295
    do return ctx:exit(1) end -- THJORGARDGAMESCOMMON.inc:297
end

script.labels["Countdown5"] = function(ctx)
    -- THJORGARDGAMESCOMMON.inc:300
    ctx:playSound("sounds\\door\\doorlock01.wav", "DoNothing", 1, 500, 0, 100) -- THJORGARDGAMESCOMMON.inc:302
    ctx:rolloverText(235, 1, 2000, 1000) -- THJORGARDGAMESCOMMON.inc:303
    ctx:wait(5, 1, "Countdown4") -- THJORGARDGAMESCOMMON.inc:304
    do return ctx:exit(1) end -- THJORGARDGAMESCOMMON.inc:306
end

script.labels["Countdown4"] = function(ctx)
    -- THJORGARDGAMESCOMMON.inc:308
    ctx:playSound("sounds\\door\\doorlock01.wav", "DoNothing", 1, 5000, 0, 100) -- THJORGARDGAMESCOMMON.inc:310
    ctx:rolloverText(236, 1, 2000, 1000) -- THJORGARDGAMESCOMMON.inc:311
    ctx:wait(4, 1, "Countdown3") -- THJORGARDGAMESCOMMON.inc:312
    do return ctx:exit(1) end -- THJORGARDGAMESCOMMON.inc:314
end

script.labels["Countdown3"] = function(ctx)
    -- THJORGARDGAMESCOMMON.inc:316
    ctx:playSound("sounds\\door\\doorlock01.wav", "DoNothing", 1, 5000, 0, 100) -- THJORGARDGAMESCOMMON.inc:318
    ctx:rolloverText(237, 1, 2000, 1000) -- THJORGARDGAMESCOMMON.inc:319
    ctx:wait(3, 1, "Countdown2") -- THJORGARDGAMESCOMMON.inc:320
    do return ctx:exit(1) end -- THJORGARDGAMESCOMMON.inc:322
end

script.labels["Countdown2"] = function(ctx)
    -- THJORGARDGAMESCOMMON.inc:324
    ctx:playSound("sounds\\door\\doorlock01.wav", "DoNothing", 1, 5000, 0, 100) -- THJORGARDGAMESCOMMON.inc:326
    ctx:rolloverText(238, 1, 2000, 1000) -- THJORGARDGAMESCOMMON.inc:327
    ctx:wait(2, 1, "Countdown1") -- THJORGARDGAMESCOMMON.inc:328
    do return ctx:exit(1) end -- THJORGARDGAMESCOMMON.inc:330
end

script.labels["Countdown1"] = function(ctx)
    -- THJORGARDGAMESCOMMON.inc:332
    ctx:playSound("sounds\\door\\doorlock01.wav", "DoNothing", 1, 5000, 0, 100) -- THJORGARDGAMESCOMMON.inc:334
    ctx:rolloverText(239, 1, 2000, 1000) -- THJORGARDGAMESCOMMON.inc:335
    ctx:wait(1, 1, "Countdown0") -- THJORGARDGAMESCOMMON.inc:336
    do return ctx:exit(1) end -- THJORGARDGAMESCOMMON.inc:338
end

script.labels["Countdown0"] = function(ctx)
    -- THJORGARDGAMESCOMMON.inc:340
    ctx:playSound("sounds\\events\\dingbell.wav", "DoNothing", 1, 5000, 0, 100) -- THJORGARDGAMESCOMMON.inc:342
    do return ctx:exit(1) end -- THJORGARDGAMESCOMMON.inc:344
end

return script
