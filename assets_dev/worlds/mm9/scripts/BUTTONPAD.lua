-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BUTTONPAD.scr"
script.includes = {}
script.labels = {}


-- ButtonPad.scr
-- Brett Yagi/Ed Campos/Karl Drown
-- 11/16/2001
-- Script is arranged as the main Trigger that relays
-- activation commands to each individual moveable
-- piece of a 16 piece puzzle door controlled by
-- a script named ButtonPuzzle.scr
-- -DEDIT NOTES-
-- ScriptParams are:
-- p0 = The Base Root name of all the Puzzle Doors
-- p1 = The Name of the ResetSwitch Trigger Object
script.labels["(Note: this is not the ButtonPad Trigger Object)"] = function(ctx)
    -- BUTTONPAD.scr:18
end

script.labels["DoNothing"] = function(ctx)
    -- BUTTONPAD.scr:63
    do return ctx:exit(1) end -- BUTTONPAD.scr:67
end

script.labels["InitalizeArrays"] = function(ctx)
    -- BUTTONPAD.scr:70
    ctx:arrayPut("aButtons", 0, 0) -- BUTTONPAD.scr:73
    ctx:arrayPut("aButtons", 1, 0) -- BUTTONPAD.scr:74
    ctx:arrayPut("aButtons", 2, 0) -- BUTTONPAD.scr:75
    ctx:arrayPut("aButtons", 3, 0) -- BUTTONPAD.scr:76
    ctx:arrayPut("aButtons", 4, 0) -- BUTTONPAD.scr:77
    ctx:arrayPut("aButtons", 5, 0) -- BUTTONPAD.scr:78
    ctx:arrayPut("aButtons", 6, 0) -- BUTTONPAD.scr:79
    ctx:arrayPut("aButtons", 7, 0) -- BUTTONPAD.scr:80
    ctx:arrayPut("aButtons", 8, 0) -- BUTTONPAD.scr:81
    ctx:arrayPut("aButtons", 9, 0) -- BUTTONPAD.scr:82
    ctx:arrayPut("aButtons", 10, 0) -- BUTTONPAD.scr:83
    ctx:arrayPut("aButtons", 11, 0) -- BUTTONPAD.scr:84
    ctx:arrayPut("aButtons", 12, 0) -- BUTTONPAD.scr:85
    ctx:arrayPut("aButtons", 13, 0) -- BUTTONPAD.scr:86
    ctx:arrayPut("aButtons", 14, 0) -- BUTTONPAD.scr:87
    ctx:arrayPut("aButtons", 15, 0) -- BUTTONPAD.scr:88
    ctx:arrayPut("aValid", 0, 1) -- BUTTONPAD.scr:91
    ctx:arrayPut("aValid", 1, 1) -- BUTTONPAD.scr:92
    ctx:arrayPut("aValid", 2, 1) -- BUTTONPAD.scr:93
    ctx:arrayPut("aValid", 3, 1) -- BUTTONPAD.scr:94
    ctx:arrayPut("aValid", 4, 1) -- BUTTONPAD.scr:95
    ctx:arrayPut("aValid", 5, 1) -- BUTTONPAD.scr:96
    ctx:arrayPut("aValid", 6, 1) -- BUTTONPAD.scr:97
    ctx:arrayPut("aValid", 7, 1) -- BUTTONPAD.scr:98
    ctx:arrayPut("aValid", 8, 1) -- BUTTONPAD.scr:99
    ctx:arrayPut("aValid", 9, 1) -- BUTTONPAD.scr:100
    ctx:arrayPut("aValid", 10, 1) -- BUTTONPAD.scr:101
    ctx:arrayPut("aValid", 11, 1) -- BUTTONPAD.scr:102
    ctx:arrayPut("aValid", 12, 1) -- BUTTONPAD.scr:103
    ctx:arrayPut("aValid", 13, 1) -- BUTTONPAD.scr:104
    ctx:arrayPut("aValid", 14, 1) -- BUTTONPAD.scr:105
    ctx:arrayPut("aValid", 15, 1) -- BUTTONPAD.scr:106
    do return ctx:exit(1) end -- BUTTONPAD.scr:109
end

script.labels["CheckDone"] = function(ctx)
    -- BUTTONPAD.scr:112
    ctx:state().nLoop = 0 -- BUTTONPAD.scr:115
    ctx:state().nDone = 0 -- BUTTONPAD.scr:116
    ctx:state().nOk = 1 -- BUTTONPAD.scr:117
    while ctx:condition("nDone != 1") do -- BUTTONPAD.scr:119
        ctx:arrayGet("aButtons", "nLoop", "nButton") -- BUTTONPAD.scr:120
        ctx:arrayGet("aValid", "nLoop", "nValidPos") -- BUTTONPAD.scr:121
        if ctx:condition("nButton != nValidPos") then -- BUTTONPAD.scr:122
            ctx:state().nOk = 0 -- BUTTONPAD.scr:123
            ctx:state().nDone = 1 -- BUTTONPAD.scr:124
        else -- BUTTONPAD.scr:125
            ctx:set("nLoop", "nLoop + 1") -- BUTTONPAD.scr:126
            if ctx:condition("nLoop = nNumButtons") then -- BUTTONPAD.scr:127
                ctx:state().nDone = 1 -- BUTTONPAD.scr:128
            end -- BUTTONPAD.scr:129
        end -- BUTTONPAD.scr:130
    end -- BUTTONPAD.scr:131
    if ctx:condition("nOk = 1") then -- BUTTONPAD.scr:133
        ctx:wait(0, .8, "MoveAway") -- BUTTONPAD.scr:134
    end -- BUTTONPAD.scr:135
    do return ctx:exit(1) end -- BUTTONPAD.scr:137
end

script.labels["MoveAway"] = function(ctx)
    -- BUTTONPAD.scr:140
    ctx:self():stop() -- BUTTONPAD.scr:142
    ctx:object("sResetSwitch"):trigger("Lock") -- BUTTONPAD.scr:143-144
    ctx:set("sButtonName", "sButtonNameRoot + nReset") -- BUTTONPAD.scr:146
    ctx:object("sButtonName"):trigger("MoveDoor") -- BUTTONPAD.scr:148-149
    if ctx:condition("nReset == 15") then -- BUTTONPAD.scr:151
        ctx:state().nReset = 0 -- BUTTONPAD.scr:152
        do return ctx:exit(1) end -- BUTTONPAD.scr:153
    else -- BUTTONPAD.scr:155
        ctx:set("nReset", "nReset + 1") -- BUTTONPAD.scr:156
        mm9.gosub(script, ctx, "MoveAway") -- BUTTONPAD.scr:157
    end -- BUTTONPAD.scr:158
    ctx:object("sAIRail"):trigger("On") -- BUTTONPAD.scr:159-160
    mm9.gosub(script, ctx, "EndScript") -- BUTTONPAD.scr:161
    do return ctx:exit(1) end -- BUTTONPAD.scr:163
end

script.labels["EndScript"] = function(ctx)
    -- BUTTONPAD.scr:166
    ctx:setConsoleNumVar("LockButtons", "FALSE") -- BUTTONPAD.scr:169
    do return ctx:exit(1) end -- BUTTONPAD.scr:171
end

script.labels["ToggleButton"] = function(ctx)
    -- BUTTONPAD.scr:174
    ctx:set("sButtonName", "sButtonNameRoot + nTemp") -- BUTTONPAD.scr:177
    local object = ctx:object("sButtonName") -- BUTTONPAD.scr:178
    object:trigger("unlock") -- BUTTONPAD.scr:179
    object:trigger("TriggerMe") -- BUTTONPAD.scr:180
    ctx:arrayGet("aButtons", "nTemp", "nOpen") -- BUTTONPAD.scr:181
    if ctx:condition("nOpen = 0") then -- BUTTONPAD.scr:183
        ctx:arrayPut("aButtons", "nTemp", 1) -- BUTTONPAD.scr:184
    else -- BUTTONPAD.scr:186
        ctx:arrayPut("aButtons", "nTemp", 0) -- BUTTONPAD.scr:187
    end -- BUTTONPAD.scr:189
    do return ctx:exit(1) end -- BUTTONPAD.scr:191
end

script.labels["unlockall"] = function(ctx)
    -- BUTTONPAD.scr:194
    ctx:setConsoleNumVar("LockButtons", "FALSE") -- BUTTONPAD.scr:197
    ctx:state().nLockLoop = 0 -- BUTTONPAD.scr:198
    while ctx:condition("nLockLoop < nNumButtons") do -- BUTTONPAD.scr:199
        ctx:set("sLock", "sButtonNameRoot\t+ nLockLoop") -- BUTTONPAD.scr:200
        ctx:object("sLock"):trigger("unlock") -- BUTTONPAD.scr:201-202
        ctx:set("nLockLoop", "nLockLoop + 1") -- BUTTONPAD.scr:203
    end -- BUTTONPAD.scr:204
    do return ctx:exit(1) end -- BUTTONPAD.scr:206
end

script.labels["Lockdown"] = function(ctx)
    -- BUTTONPAD.scr:209
    ctx:setConsoleNumVar("LockButtons", "TRUE") -- BUTTONPAD.scr:212
    ctx:state().nLockLoop = 0 -- BUTTONPAD.scr:214
    while ctx:condition("nLockLoop < nNumButtons") do -- BUTTONPAD.scr:215
        ctx:set("sLock", "sButtonNameRoot\t+ nLockLoop") -- BUTTONPAD.scr:216
        ctx:object("sLock"):trigger("Lock") -- BUTTONPAD.scr:217-218
        ctx:set("nLockLoop", "nLockLoop + 1") -- BUTTONPAD.scr:219
    end -- BUTTONPAD.scr:220
    do return ctx:exit(1) end -- BUTTONPAD.scr:222
end

script.labels["ButtonPushed"] = function(ctx)
    -- BUTTONPAD.scr:225
    ctx:set("nCol", "nButtonPushed") -- BUTTONPAD.scr:228
    ctx:set("nTemp", "nButtonPushed") -- BUTTONPAD.scr:229
    mm9.gosub(script, ctx, "Lockdown") -- BUTTONPAD.scr:230
    ctx:arrayGet("aButtons", "nTemp", "nOpen") -- BUTTONPAD.scr:231
    if ctx:condition("nOpen = 0") then -- BUTTONPAD.scr:232
        ctx:arrayPut("aButtons", "nTemp", 1) -- BUTTONPAD.scr:233
    else -- BUTTONPAD.scr:234
        ctx:arrayPut("aButtons", "nTemp", 0) -- BUTTONPAD.scr:235
    end -- BUTTONPAD.scr:236
    ctx:mod("nCol", "nNumCol") -- BUTTONPAD.scr:238
    ctx:set("nRow", "nButtonPushed - nCol / nNumCol") -- BUTTONPAD.scr:239
    if ctx:condition("nCol > 0") then -- BUTTONPAD.scr:241
        ctx:set("nTemp", "nRow * nNumCol + nCol - 1") -- BUTTONPAD.scr:242
        mm9.gosub(script, ctx, "ToggleButton") -- BUTTONPAD.scr:243
    end -- BUTTONPAD.scr:244
    ctx:set("nWrapStop", "nNumCol - 1") -- BUTTONPAD.scr:245
    if ctx:condition("nCol < nWrapStop") then -- BUTTONPAD.scr:246
        ctx:set("nTemp", "nRow * nNumCol + nCol + 1") -- BUTTONPAD.scr:247
        mm9.gosub(script, ctx, "ToggleButton") -- BUTTONPAD.scr:248
    end -- BUTTONPAD.scr:249
    if ctx:condition("nRow > 0") then -- BUTTONPAD.scr:251
        ctx:set("nTemp", "nRow - 1 * nNumCol + nCol") -- BUTTONPAD.scr:252
        mm9.gosub(script, ctx, "ToggleButton") -- BUTTONPAD.scr:253
    end -- BUTTONPAD.scr:254
    if ctx:condition("nRow < nWrapStop") then -- BUTTONPAD.scr:256
        ctx:set("nTemp", "nRow + 1 * nNumCol + nCol") -- BUTTONPAD.scr:257
        mm9.gosub(script, ctx, "ToggleButton") -- BUTTONPAD.scr:258
    end -- BUTTONPAD.scr:259
    ctx:wait(1, .5, "Unlockall") -- BUTTONPAD.scr:262
    mm9.gosub(script, ctx, "CheckDone") -- BUTTONPAD.scr:263
    do return ctx:exit(1) end -- BUTTONPAD.scr:265
end

script.labels["Button0"] = function(ctx)
    -- BUTTONPAD.scr:268
    ctx:state().nButtonPushed = 0 -- BUTTONPAD.scr:271
    mm9.gosub(script, ctx, "ButtonPushed") -- BUTTONPAD.scr:272
    do return ctx:exit(1) end -- BUTTONPAD.scr:274
end

script.labels["Button1"] = function(ctx)
    -- BUTTONPAD.scr:277
    ctx:state().nButtonPushed = 1 -- BUTTONPAD.scr:280
    mm9.gosub(script, ctx, "ButtonPushed") -- BUTTONPAD.scr:281
    do return ctx:exit(1) end -- BUTTONPAD.scr:283
end

script.labels["Button2"] = function(ctx)
    -- BUTTONPAD.scr:286
    ctx:state().nButtonPushed = 2 -- BUTTONPAD.scr:289
    mm9.gosub(script, ctx, "ButtonPushed") -- BUTTONPAD.scr:290
    do return ctx:exit(1) end -- BUTTONPAD.scr:292
end

script.labels["Button3"] = function(ctx)
    -- BUTTONPAD.scr:295
    ctx:state().nButtonPushed = 3 -- BUTTONPAD.scr:298
    mm9.gosub(script, ctx, "ButtonPushed") -- BUTTONPAD.scr:299
    do return ctx:exit(1) end -- BUTTONPAD.scr:301
end

script.labels["Button4"] = function(ctx)
    -- BUTTONPAD.scr:304
    ctx:state().nButtonPushed = 4 -- BUTTONPAD.scr:307
    mm9.gosub(script, ctx, "ButtonPushed") -- BUTTONPAD.scr:308
    do return ctx:exit(1) end -- BUTTONPAD.scr:310
end

script.labels["Button5"] = function(ctx)
    -- BUTTONPAD.scr:313
    ctx:state().nButtonPushed = 5 -- BUTTONPAD.scr:316
    mm9.gosub(script, ctx, "ButtonPushed") -- BUTTONPAD.scr:317
    do return ctx:exit(1) end -- BUTTONPAD.scr:319
end

script.labels["Button6"] = function(ctx)
    -- BUTTONPAD.scr:322
    ctx:state().nButtonPushed = 6 -- BUTTONPAD.scr:325
    mm9.gosub(script, ctx, "ButtonPushed") -- BUTTONPAD.scr:326
    do return ctx:exit(1) end -- BUTTONPAD.scr:328
end

script.labels["Button7"] = function(ctx)
    -- BUTTONPAD.scr:331
    ctx:state().nButtonPushed = 7 -- BUTTONPAD.scr:334
    mm9.gosub(script, ctx, "ButtonPushed") -- BUTTONPAD.scr:335
    do return ctx:exit(1) end -- BUTTONPAD.scr:337
end

script.labels["Button8"] = function(ctx)
    -- BUTTONPAD.scr:340
    ctx:state().nButtonPushed = 8 -- BUTTONPAD.scr:343
    mm9.gosub(script, ctx, "ButtonPushed") -- BUTTONPAD.scr:344
    do return ctx:exit(1) end -- BUTTONPAD.scr:346
end

script.labels["Button9"] = function(ctx)
    -- BUTTONPAD.scr:349
    ctx:state().nButtonPushed = 9 -- BUTTONPAD.scr:352
    mm9.gosub(script, ctx, "ButtonPushed") -- BUTTONPAD.scr:353
    do return ctx:exit(1) end -- BUTTONPAD.scr:355
end

script.labels["Button10"] = function(ctx)
    -- BUTTONPAD.scr:358
    ctx:state().nButtonPushed = 10 -- BUTTONPAD.scr:361
    mm9.gosub(script, ctx, "ButtonPushed") -- BUTTONPAD.scr:362
    do return ctx:exit(1) end -- BUTTONPAD.scr:364
end

script.labels["Button11"] = function(ctx)
    -- BUTTONPAD.scr:367
    ctx:state().nButtonPushed = 11 -- BUTTONPAD.scr:370
    mm9.gosub(script, ctx, "ButtonPushed") -- BUTTONPAD.scr:371
    do return ctx:exit(1) end -- BUTTONPAD.scr:373
end

script.labels["Button12"] = function(ctx)
    -- BUTTONPAD.scr:376
    ctx:state().nButtonPushed = 12 -- BUTTONPAD.scr:379
    mm9.gosub(script, ctx, "ButtonPushed") -- BUTTONPAD.scr:380
    do return ctx:exit(1) end -- BUTTONPAD.scr:382
end

script.labels["Button13"] = function(ctx)
    -- BUTTONPAD.scr:385
    ctx:state().nButtonPushed = 13 -- BUTTONPAD.scr:388
    mm9.gosub(script, ctx, "ButtonPushed") -- BUTTONPAD.scr:389
    do return ctx:exit(1) end -- BUTTONPAD.scr:391
end

script.labels["Button14"] = function(ctx)
    -- BUTTONPAD.scr:394
    ctx:state().nButtonPushed = 14 -- BUTTONPAD.scr:397
    mm9.gosub(script, ctx, "ButtonPushed") -- BUTTONPAD.scr:398
    do return ctx:exit(1) end -- BUTTONPAD.scr:400
end

script.labels["Button15"] = function(ctx)
    -- BUTTONPAD.scr:403
    ctx:state().nButtonPushed = 15 -- BUTTONPAD.scr:406
    mm9.gosub(script, ctx, "ButtonPushed") -- BUTTONPAD.scr:407
    do return ctx:exit(1) end -- BUTTONPAD.scr:409
end

script.labels["SetTrap"] = function(ctx)
    -- BUTTONPAD.scr:412
    ctx:set("sButtonName", "sButtonNameRoot + nReset") -- BUTTONPAD.scr:415
    ctx:object("sButtonName"):trigger("TriggerTrap") -- BUTTONPAD.scr:416-417
    ctx:wait(2, .6, "SlamSound") -- BUTTONPAD.scr:418
    if ctx:condition("nReset == 15") then -- BUTTONPAD.scr:420
        ctx:state().nReset = 0 -- BUTTONPAD.scr:421
        ctx:wait(3, .5, "SetTrap2") -- BUTTONPAD.scr:423
        do return ctx:exit(1) end -- BUTTONPAD.scr:424
    else -- BUTTONPAD.scr:426
        ctx:set("nReset", "nReset + 1") -- BUTTONPAD.scr:427
        mm9.gosub(script, ctx, "SetTrap") -- BUTTONPAD.scr:428
    end -- BUTTONPAD.scr:430
    do return ctx:exit(1) end -- BUTTONPAD.scr:432
end

script.labels["SlamSound"] = function(ctx)
    -- BUTTONPAD.scr:435
    ctx:playSound("sounds\\Door\\stonedoorslam.wav", "DoNothing", 0, 1000, 0, 100) -- BUTTONPAD.scr:438
    ctx:wait(4, .3, "LockSound") -- BUTTONPAD.scr:439
    do return ctx:exit(1) end -- BUTTONPAD.scr:441
end

script.labels["LockSound"] = function(ctx)
    -- BUTTONPAD.scr:444
    ctx:playSound("sounds\\Door\\doorlatch02.wav", "DoNothing", 0, 1000, 0, 100) -- BUTTONPAD.scr:447
    do return ctx:exit(1) end -- BUTTONPAD.scr:449
end

script.labels["SetTrap2"] = function(ctx)
    -- BUTTONPAD.scr:452
    ctx:set("sButtonName", "sButtonNameRoot + nReset") -- BUTTONPAD.scr:455
    ctx:object("sButtonName"):trigger("UseStart") -- BUTTONPAD.scr:456-457
    if ctx:condition("nReset == 15") then -- BUTTONPAD.scr:459
        ctx:state().nReset = 0 -- BUTTONPAD.scr:460
        ctx:wait(5, .5, "SetTrap3") -- BUTTONPAD.scr:461
        do return ctx:exit(1) end -- BUTTONPAD.scr:462
    else -- BUTTONPAD.scr:464
        ctx:set("nReset", "nReset + 1") -- BUTTONPAD.scr:465
        mm9.gosub(script, ctx, "SetTrap2") -- BUTTONPAD.scr:467
    end -- BUTTONPAD.scr:468
    do return ctx:exit(1) end -- BUTTONPAD.scr:472
end

script.labels["SetTrap3"] = function(ctx)
    -- BUTTONPAD.scr:475
    mm9.gosub(script, ctx, "Reset2") -- BUTTONPAD.scr:478
    do return ctx:exit(1) end -- BUTTONPAD.scr:480
end

script.labels["Reset"] = function(ctx)
    -- BUTTONPAD.scr:483
    ctx:set("sButtonName", "sButtonNameRoot + nReset") -- BUTTONPAD.scr:486
    ctx:object("sButtonName"):trigger("close") -- BUTTONPAD.scr:487-488
    ctx:arrayPut("aButtons", "nReset", 0) -- BUTTONPAD.scr:489
    if ctx:condition("nReset == 15") then -- BUTTONPAD.scr:491
        ctx:state().nReset = 0 -- BUTTONPAD.scr:492
        do return ctx:exit(1) end -- BUTTONPAD.scr:493
    else -- BUTTONPAD.scr:495
        ctx:set("nReset", "nReset + 1") -- BUTTONPAD.scr:496
        mm9.gosub(script, ctx, "Reset") -- BUTTONPAD.scr:497
    end -- BUTTONPAD.scr:498
    do return ctx:exit(1) end -- BUTTONPAD.scr:501
end

script.labels["Reset2"] = function(ctx)
    -- BUTTONPAD.scr:504
    ctx:set("sButtonName", "sButtonNameRoot + nReset") -- BUTTONPAD.scr:509
    local object = ctx:object("sButtonName") -- BUTTONPAD.scr:510
    object:trigger("Unlock") -- BUTTONPAD.scr:511
    object:trigger("close") -- BUTTONPAD.scr:512
    ctx:arrayPut("aButtons", "nReset", 0) -- BUTTONPAD.scr:513
    if ctx:condition("nReset == 15") then -- BUTTONPAD.scr:515
        ctx:state().nReset = 0 -- BUTTONPAD.scr:516
        do return ctx:exit(1) end -- BUTTONPAD.scr:517
    else -- BUTTONPAD.scr:519
        ctx:set("nReset", "nReset + 1") -- BUTTONPAD.scr:520
        mm9.gosub(script, ctx, "Reset2") -- BUTTONPAD.scr:521
    end -- BUTTONPAD.scr:523
    do return ctx:exit(1) end -- BUTTONPAD.scr:527
end

script.labels["Main2"] = function(ctx)
    -- BUTTONPAD.scr:530
    ctx:setConsoleNumVar("LockButtons", "FALSE") -- BUTTONPAD.scr:533
    mm9.gosub(script, ctx, "InitalizeArrays") -- BUTTONPAD.scr:534
    ctx:state().sLockButtons = "LockButtons" -- BUTTONPAD.scr:535
    do return ctx:exit(1) end -- BUTTONPAD.scr:537
end

script.labels["Main"] = function(ctx)
    -- BUTTONPAD.scr:539
    ctx:getParam(0, "sButtonNameRoot") -- BUTTONPAD.scr:544
    ctx:getParam(1, "sResetSwitch") -- BUTTONPAD.scr:545
    ctx:getParam(2, "sAIRail") -- BUTTONPAD.scr:546
    ctx:addTrigger("Button0", "Button0") -- BUTTONPAD.scr:548
    ctx:addTrigger("Button1", "Button1") -- BUTTONPAD.scr:549
    ctx:addTrigger("Button2", "Button2") -- BUTTONPAD.scr:550
    ctx:addTrigger("Button3", "Button3") -- BUTTONPAD.scr:551
    ctx:addTrigger("Button4", "Button4") -- BUTTONPAD.scr:552
    ctx:addTrigger("Button5", "Button5") -- BUTTONPAD.scr:553
    ctx:addTrigger("Button6", "Button6") -- BUTTONPAD.scr:554
    ctx:addTrigger("Button7", "Button7") -- BUTTONPAD.scr:555
    ctx:addTrigger("Button8", "Button8") -- BUTTONPAD.scr:556
    ctx:addTrigger("Button9", "Button9") -- BUTTONPAD.scr:557
    ctx:addTrigger("Button10", "Button10") -- BUTTONPAD.scr:558
    ctx:addTrigger("Button11", "Button11") -- BUTTONPAD.scr:559
    ctx:addTrigger("Button12", "Button12") -- BUTTONPAD.scr:560
    ctx:addTrigger("Button13", "Button13") -- BUTTONPAD.scr:561
    ctx:addTrigger("Button14", "Button14") -- BUTTONPAD.scr:562
    ctx:addTrigger("Button15", "Button15") -- BUTTONPAD.scr:563
    ctx:addTrigger("Reset", "Reset") -- BUTTONPAD.scr:564
    ctx:addTrigger("SetTrap", "SetTrap") -- BUTTONPAD.scr:565
    -- AddTrigger MoveAway MoveAway
    ctx:wait(0, 1, "Main2") -- BUTTONPAD.scr:568
    do return ctx:exit(1) end -- BUTTONPAD.scr:570
end

return script
