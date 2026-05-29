-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "FOREMANMINER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 22, path = "globals.inc" }

-- ForemanMiner.scr
-- by Sean Rostami/Ed Campos
-- 10-04-01
-- Script Sets up a Leading Dwarf that
-- Initiates the movement of group Miners
-- ScriptParams are:
-- p0 = Name of WorkArea0
-- p1 = Name of WorkArea1
-- p2 = Name of WorkArea2
-- p3 = Name of WorkArea3
-- p4 = Name of place to run to during "panic"
-- Miners will "panic" and run around
-- and start their emergency routine
-- when "FreakOut" is triggered
script.labels["InitForemanMiner"] = function(ctx)
    -- FOREMANMINER.scr:51
    -- Get Handles on all Markers within
    -- the world. Set Triggers
    ctx:onEvent("OnAlert", "OnPanic") -- FOREMANMINER.scr:58
    ctx:onEvent("OnDamage", "OnDamage") -- FOREMANMINER.scr:59
    ctx:addTrigger("FreakOut", "FreakOut") -- FOREMANMINER.scr:61
    ctx:state().hBunker = ctx:objectOrNil("sBunkerName") -- FOREMANMINER.scr:64
    ctx:state().hTarget0 = ctx:objectOrNil("DwarvenMinion0") -- FOREMANMINER.scr:66
    ctx:state().hTarget1 = ctx:objectOrNil("DwarvenMinion1") -- FOREMANMINER.scr:67
    ctx:state().hTarget2 = ctx:objectOrNil("DwarvenMinion2") -- FOREMANMINER.scr:68
    mm9.gosub(script, ctx, "StartPositionA") -- FOREMANMINER.scr:70
    do return ctx:exit("TRUE") end -- FOREMANMINER.scr:71
end

script.labels["StartPositionA"] = function(ctx)
    -- FOREMANMINER.scr:74
    ctx:state().NewArea = 1 -- FOREMANMINER.scr:77
    ctx:state().hOrderSpot0 = ctx:objectOrNil("sWorkArea0Name") -- FOREMANMINER.scr:78
    ctx:state().hOrderSpot1 = ctx:objectOrNil("sWorkArea1Name") -- FOREMANMINER.scr:79
    ctx:self():walkTo(ctx:object("hOrderSpot0"), 10, "Arrived1stSpot") -- FOREMANMINER.scr:80
    do return ctx:exit("TRUE") end -- FOREMANMINER.scr:83
end

script.labels["StartPositionB"] = function(ctx)
    -- FOREMANMINER.scr:86
    ctx:state().NewArea = 0 -- FOREMANMINER.scr:89
    ctx:state().hOrderSpot0 = ctx:objectOrNil("sWorkArea2Name") -- FOREMANMINER.scr:90
    ctx:state().hOrderSpot1 = ctx:objectOrNil("sWorkArea3Name") -- FOREMANMINER.scr:91
    ctx:self():walkTo(ctx:object("hOrderSpot0"), 10, "Arrived1stSpot") -- FOREMANMINER.scr:92
    do return ctx:exit("TRUE") end -- FOREMANMINER.scr:95
end

script.labels["Arrived1stSpot"] = function(ctx)
    -- FOREMANMINER.scr:98
    ctx:self():stop() -- FOREMANMINER.scr:101
    ctx:wait(0, 5, "Threat1A") -- FOREMANMINER.scr:102
    ctx:self():setTarget(ctx:object("hTarget0")) -- FOREMANMINER.scr:103
    do return ctx:exit("TRUE") end -- FOREMANMINER.scr:105
end

script.labels["Threat1A"] = function(ctx)
    -- FOREMANMINER.scr:108
    ctx:self():stop() -- FOREMANMINER.scr:111
    ctx:self():playAnimation("HAttack1", "DoNothing") -- FOREMANMINER.scr:113
    ctx:wait(0, 5, "DoNothing") -- FOREMANMINER.scr:114
    ctx:self():playAnimation("Taunt", "DoNothing") -- FOREMANMINER.scr:115
    ctx:wait(0, 20, "MicroManage1A") -- FOREMANMINER.scr:116
    do return ctx:exit("TRUE") end -- FOREMANMINER.scr:118
end

script.labels["MicroManage1A"] = function(ctx)
    -- FOREMANMINER.scr:121
    ctx:self():stop() -- FOREMANMINER.scr:124
    ctx:wait(0, 20, "DoNothing") -- FOREMANMINER.scr:125
    ctx:self():walkTo(ctx:object("hOrderSpot1"), 10, "ChooseVictim1") -- FOREMANMINER.scr:126
    do return ctx:exit("TRUE") end -- FOREMANMINER.scr:128
end

script.labels["ChooseVictim1"] = function(ctx)
    -- FOREMANMINER.scr:131
    ctx:self():stop() -- FOREMANMINER.scr:134
    ctx:self():setTarget(nil) -- FOREMANMINER.scr:135
    ctx:self():setTarget(ctx:object("hTarget0")) -- FOREMANMINER.scr:136
    ctx:self():playAnimation("Figet2", "DoNothing") -- FOREMANMINER.scr:137
    do return ctx:exit("TRUE") end -- FOREMANMINER.scr:141
end

script.labels["DoWait1A"] = function(ctx)
    -- FOREMANMINER.scr:143
    ctx:wait(0, 20, "DoWait1B") -- FOREMANMINER.scr:146
    ctx:self():setTarget(nil) -- FOREMANMINER.scr:147
    ctx:self():setTarget(ctx:object("hTarget2")) -- FOREMANMINER.scr:148
    ctx:self():playAnimation("HAttack1", "DoNothing") -- FOREMANMINER.scr:149
    ctx:self():playAnimation("WAttack2", "DoNothing") -- FOREMANMINER.scr:150
    ctx:self():playAnimation("Taunt", "DoNothing") -- FOREMANMINER.scr:151
    do return ctx:exit("TRUE") end -- FOREMANMINER.scr:154
end

script.labels["DoWait1B"] = function(ctx)
    -- FOREMANMINER.scr:157
    ctx:wait(0, 20, "MicroManage1B") -- FOREMANMINER.scr:160
    ctx:self():setTarget(nil) -- FOREMANMINER.scr:161
    ctx:self():setTarget(ctx:object("hTarget1")) -- FOREMANMINER.scr:162
    ctx:self():playAnimation("Taunt", "DoNothing") -- FOREMANMINER.scr:163
    do return ctx:exit("TRUE") end -- FOREMANMINER.scr:165
end

script.labels["MicroManage1B"] = function(ctx)
    -- FOREMANMINER.scr:167
    ctx:wait(0, 20, "DoNothing") -- FOREMANMINER.scr:170
    ctx:self():walkTo(ctx:object("hOrderSpot0"), 10, "ChooseVictim2") -- FOREMANMINER.scr:171
    do return ctx:exit("TRUE") end -- FOREMANMINER.scr:173
end

script.labels["ChooseVictim2"] = function(ctx)
    -- FOREMANMINER.scr:176
    ctx:self():stop() -- FOREMANMINER.scr:179
    ctx:self():setTarget(nil) -- FOREMANMINER.scr:180
    ctx:self():setTarget(ctx:object("hTarget0")) -- FOREMANMINER.scr:181
    ctx:self():playAnimation("Figet2", "DoNothing") -- FOREMANMINER.scr:182
    ctx:self():playAnimation("Search", "MicroManage1C") -- FOREMANMINER.scr:183
    do return ctx:exit("TRUE") end -- FOREMANMINER.scr:187
end

script.labels["Micromanage1C"] = function(ctx)
    -- FOREMANMINER.scr:189
    ctx:wait(0, 20, "DoNothing") -- FOREMANMINER.scr:192
    ctx:self():walkTo(ctx:object("hOrderSpot1"), 10, "GiveMoveOutOrders") -- FOREMANMINER.scr:193
    do return ctx:exit("TRUE") end -- FOREMANMINER.scr:195
end

script.labels["GiveMoveOutOrders"] = function(ctx)
    -- FOREMANMINER.scr:197
    ctx:self():stop() -- FOREMANMINER.scr:200
    ctx:wait(0, 25, "MoveOut") -- FOREMANMINER.scr:201
    ctx:trigger("hTarget0", "LookUp") -- FOREMANMINER.scr:203
    ctx:trigger("hTarget1", "LookUp") -- FOREMANMINER.scr:204
    ctx:trigger("hTarget2", "LookUp") -- FOREMANMINER.scr:205
    ctx:self():playAnimation("Aware", "DoNothing") -- FOREMANMINER.scr:206
    ctx:self():playAnimation("HAttack2", "DoNothing") -- FOREMANMINER.scr:207
    ctx:self():playAnimation("Taunt", "DoNothing") -- FOREMANMINER.scr:208
    ctx:self():playAnimation("HAttack1", "DoNothing") -- FOREMANMINER.scr:209
    do return ctx:exit("TRUE") end -- FOREMANMINER.scr:212
end

script.labels["MoveOut"] = function(ctx)
    -- FOREMANMINER.scr:216
    ctx:wait(0, 5, "NewArea") -- FOREMANMINER.scr:219
    ctx:trigger("hTarget0", "NextSite") -- FOREMANMINER.scr:220
    ctx:trigger("hTarget1", "NextSite") -- FOREMANMINER.scr:221
    ctx:trigger("hTarget2", "NextSite") -- FOREMANMINER.scr:222
    do return ctx:exit("TRUE") end -- FOREMANMINER.scr:227
end

script.labels["NewArea"] = function(ctx)
    -- FOREMANMINER.scr:230
    if ctx:condition("NewArea== 0") then -- FOREMANMINER.scr:233
        mm9.gosub(script, ctx, "StartPositionA") -- FOREMANMINER.scr:234
    else -- FOREMANMINER.scr:236
        mm9.gosub(script, ctx, "StartPositionB") -- FOREMANMINER.scr:237
    end -- FOREMANMINER.scr:239
    do return ctx:exit("TRUE") end -- FOREMANMINER.scr:241
end

script.labels["OnDamage"] = function(ctx)
    -- FOREMANMINER.scr:245
    ctx:self():stop() -- FOREMANMINER.scr:250
    -- play sound "monster!!!"
    ctx:state().StopWorking = true -- FOREMANMINER.scr:252
    ctx:onEvent("OnAlert", "DoNothing") -- FOREMANMINER.scr:253
    ctx:onEvent("OnDamage", "DoNothing") -- FOREMANMINER.scr:254
    ctx:getParam(0, "hTarget") -- FOREMANMINER.scr:255
    ctx:self():setTarget(ctx:object("hTarget")) -- FOREMANMINER.scr:256
    ctx:wait(0, 1, "GoDamagePanic") -- FOREMANMINER.scr:258
    do return ctx:exit("TRUE") end -- FOREMANMINER.scr:260
end

script.labels["OnPanic"] = function(ctx)
    -- FOREMANMINER.scr:264
    ctx:self():stop() -- FOREMANMINER.scr:268
    ctx:onEvent("OnAlert", "DoNothing") -- FOREMANMINER.scr:269
    ctx:onEvent("OnDamage", "DoNothing") -- FOREMANMINER.scr:270
    ctx:state().StopWorking = true -- FOREMANMINER.scr:271
    ctx:getParam(0, "hTarget") -- FOREMANMINER.scr:272
    ctx:getParam(1, "hTarget2") -- FOREMANMINER.scr:273
    ctx:wait(12, 2, "DoNothing") -- FOREMANMINER.scr:274
    ctx:self():setTarget(ctx:object("hTarget")) -- FOREMANMINER.scr:276
    ctx:wait(0, 1.3, "FindTarget") -- FOREMANMINER.scr:277
    do return ctx:exit("TRUE") end -- FOREMANMINER.scr:279
end

script.labels["FindTarget"] = function(ctx)
    -- FOREMANMINER.scr:283
    -- play sound "monster!!!"
    ctx:self():stop() -- FOREMANMINER.scr:288
    ctx:self():setTarget(nil) -- FOREMANMINER.scr:289
    -- GetParam 1, hTarget2
    ctx:self():setTarget(ctx:object("hTarget2")) -- FOREMANMINER.scr:291
    ctx:wait(0, .7, "GoPanic") -- FOREMANMINER.scr:293
    do return ctx:exit("TRUE") end -- FOREMANMINER.scr:295
end

script.labels["FreakOut"] = function(ctx)
    -- FOREMANMINER.scr:298
    ctx:self():stop() -- FOREMANMINER.scr:301
    -- GetObjectHandle Trigger0, hTarget3
    -- Target hTarget3, TRUE
    ctx:wait(0, 1, "GoPanic") -- FOREMANMINER.scr:305
    do return ctx:exit("TRUE") end -- FOREMANMINER.scr:307
end

script.labels["GoDamagePanic"] = function(ctx)
    -- FOREMANMINER.scr:310
    ctx:self():playAnimation("Aware", "GoDamagePanic2") -- FOREMANMINER.scr:313
    ctx:self():sendAlert(nil) -- FOREMANMINER.scr:314
    do return ctx:exit("TRUE") end -- FOREMANMINER.scr:317
end

script.labels["GoDamagePanic2"] = function(ctx)
    -- FOREMANMINER.scr:320
    -- Target NULL
    mm9.gosub(script, ctx, "BunkerRun") -- FOREMANMINER.scr:325
    do return ctx:exit("TRUE") end -- FOREMANMINER.scr:328
end

script.labels["GoPanic"] = function(ctx)
    -- FOREMANMINER.scr:330
    ctx:self():playAnimation("Aware", "DoNothing") -- FOREMANMINER.scr:333
    ctx:wait(0, 1, "BunkerRun") -- FOREMANMINER.scr:334
    do return ctx:exit("TRUE") end -- FOREMANMINER.scr:336
end

script.labels["BunkerRun"] = function(ctx)
    -- FOREMANMINER.scr:338
    ctx:self():runTo(ctx:object("hBunker"), 40, "GoLockDown") -- FOREMANMINER.scr:340
    do return ctx:exit("TRUE") end -- FOREMANMINER.scr:342
end

script.labels["GoLockDown"] = function(ctx)
    -- FOREMANMINER.scr:344
    ctx:self():stop() -- FOREMANMINER.scr:346
    do return ctx:exit("") end -- FOREMANMINER.scr:347
end

script.labels["Main"] = function(ctx)
    -- FOREMANMINER.scr:353
    -- Retrieve Parameters from AI Actor
    ctx:getParam(0, "sWorkArea0Name") -- FOREMANMINER.scr:358
    ctx:getParam(1, "sWorkArea1Name") -- FOREMANMINER.scr:359
    ctx:getParam(2, "sWorkArea2Name") -- FOREMANMINER.scr:360
    ctx:getParam(3, "sWorkArea3Name") -- FOREMANMINER.scr:361
    ctx:getParam(4, "sBunkerName") -- FOREMANMINER.scr:362
    ctx:wait(0, 5, "InitForemanMiner") -- FOREMANMINER.scr:364
    do return ctx:exit("TRUE") end -- FOREMANMINER.scr:366
end

return script
