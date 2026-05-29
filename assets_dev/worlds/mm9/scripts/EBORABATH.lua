-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "EBORABATH.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "flags.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "baseMelee.inc" }

-- EboraBath.scr
-- By L. Dean Gibson II
-- Ebora's script in the bathhouse...
-- modified by Bones 10/22/02
-- TELP Patch 1.3 -- will not freeze if last conc slain while TB
-- corrected keys
script.labels["OnGossip"] = function(ctx)
    -- EBORABATH.scr:30
    ctx:rolloverText("nGossip", 1, 3000, 2000) -- EBORABATH.scr:32
    ctx:set("nGossip", "nGossip + 1") -- EBORABATH.scr:33
    if ctx:condition("nGossip>5") then -- EBORABATH.scr:35
        ctx:removeTrigger("OnGossip") -- EBORABATH.scr:36
    end -- EBORABATH.scr:37
    do return ctx:exit("TRUE") end -- EBORABATH.scr:39
end

script.labels["DeadConcubine"] = function(ctx)
    -- EBORABATH.scr:42
    -- when 3 concs are dead, trigger cinema
    ctx:set("nDeadConcubines", "nDeadConcubines + 1") -- EBORABATH.scr:45
    if ctx:condition("nDeadConcubines>=3") then -- EBORABATH.scr:47
        ctx:self():stop() -- EBORABATH.scr:48
        ctx:state().g_hTarget = nil -- EBORABATH.scr:49
        mm9.gosub(script, ctx, "AggressiveStop") -- EBORABATH.scr:50
        ctx:onEvent("OnFoundTarget", "DoNothing") -- EBORABATH.scr:51
        ctx:removeTrigger("DeadConcubine") -- EBORABATH.scr:52
        mm9.gosub(script, ctx, "EscapeTheTub") -- EBORABATH.scr:53
    else -- EBORABATH.scr:54
        ctx:set("nTaunt", "8 + nDeadConcubines") -- EBORABATH.scr:55
        ctx:rolloverText("nTaunt", 0) -- EBORABATH.scr:56
    end -- EBORABATH.scr:57
    do return ctx:exit("TRUE") end -- EBORABATH.scr:59
end

script.labels["EscapeTheTub"] = function(ctx)
    -- EBORABATH.scr:62
    mm9.gosub(script, ctx, "TurnCameraOn") -- EBORABATH.scr:65
    if ctx:condition("g_nTemp == TRUE") then -- EBORABATH.scr:67
        do return ctx:exit("") end -- EBORABATH.scr:68
    end -- EBORABATH.scr:69
    ctx:rolloverText(11, 2, 7000, 3000, 100, 500) -- EBORABATH.scr:71
    ctx:self():playAnimation("launch", "CastSpell") -- EBORABATH.scr:73
    -- GetObjectHandle BigColWinPool2, g_hObject
    -- Trigger g_hObject, MoveIt
    do return ctx:exit("TRUE") end -- EBORABATH.scr:79
end

script.labels["OnLaunchDone0"] = function(ctx)
    -- EBORABATH.scr:82
    mm9.gosub(script, ctx, "OnEboraArrive1") -- EBORABATH.scr:84
    -- LoopAnim fly 0
    -- GetObjectHandle EboraFly1 g_hObject
    -- RunTo g_hObject, 0, OnEboraArrive1
    -- GetPos g_hObject g_posX g_posY g_posZ
    -- GetMyHandle g_hMyObject
    -- GetStat g_hMyObject FlyVel g_velX
    -- g_velX = g_velX / 2
    -- 2082, 102, -1677
    -- MoveToPos g_posX, g_posY, g_posZ, g_velX, Land
    do return ctx:exit("") end -- EBORABATH.scr:98
end

script.labels["OnEboraArrive1"] = function(ctx)
    -- EBORABATH.scr:101
    ctx:state().g_hObject = ctx:objectOrNil("FlyToBlatt") -- EBORABATH.scr:103
    ctx:self():runTo(ctx:object("g_hObject"), 8, "Land") -- EBORABATH.scr:104
    do return ctx:exit("TRUE") end -- EBORABATH.scr:106
end

script.labels["Land"] = function(ctx)
    -- EBORABATH.scr:109
    ctx:self():playAnimation("land", "LandDone") -- EBORABATH.scr:111
    do return ctx:exit("TRUE") end -- EBORABATH.scr:113
end

script.labels["LandDone"] = function(ctx)
    -- EBORABATH.scr:116
    -- GetMyHandle g_hMyObject
    -- GetStat g_hMyObject FlyVel g_velX
    -- g_velX = g_velX / 2
    -- hard coded coords inserted since getobjecthandle is fucked for some reason here
    -- 1825 44 -1797
    -- tell FatBlatt we've arrived! he can move again
    ctx:object("BigColWinPool2"):trigger("EboraArrive") -- EBORABATH.scr:125-126
    -- RunTo g_hObject, 0, EboraDone
    ctx:state().hEboraMarker = ctx:objectOrNil("sEboraMarker1") -- EBORABATH.scr:130
    ctx:self():faceObject(ctx:object("hEboraMarker"), 180) -- EBORABATH.scr:131
    ctx:rolloverText(12, 0) -- EBORABATH.scr:132
    ctx:wait(1, 3, "TurnCameraOff") -- EBORABATH.scr:133
    do return ctx:exit("") end -- EBORABATH.scr:135
end

script.labels["DeadPal"] = function(ctx)
    -- EBORABATH.scr:138
    -- Ebora's fat friend is dead! Time to ditch this joint!
    ctx:rolloverText(12, 0) -- EBORABATH.scr:144
    -- gosub TurnCameraOn
    ctx:self():playAnimation("fidget2", "CastSpell") -- EBORABATH.scr:148
    do return ctx:exit("TRUE") end -- EBORABATH.scr:150
end

script.labels["CastSpell"] = function(ctx)
    -- EBORABATH.scr:153
    ctx:self():playAnimation("Castspell", "DitchTheJoint") -- EBORABATH.scr:155
    do return ctx:exit("TRUE") end -- EBORABATH.scr:157
end

script.labels["DitchTheJoint"] = function(ctx)
    -- EBORABATH.scr:160
    ctx:self():doClientFx("SPELL_COLUMNOFFIRE", "FALSE", "TRUE") -- EBORABATH.scr:163
    ctx:playSound("sounds\\spells\\column03.wav", "DoNothing", 1, 1000, "FALSE", 100) -- EBORABATH.scr:164
    ctx:wait(1, 1, "ClearMe") -- EBORABATH.scr:165
    if ctx:hasKey(348) then -- EBORABATH.scr:168-169
        if not ctx:hasKey(349) then -- EBORABATH.scr:170-171
            ctx:giveKey(349) -- EBORABATH.scr:172
            ctx:giveExp(80000) -- EBORABATH.scr:173
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 5000, "FALSE", 100) -- EBORABATH.scr:174
        end -- EBORABATH.scr:175
    else -- EBORABATH.scr:176
        ctx:giveKey(350) -- EBORABATH.scr:177
    end -- EBORABATH.scr:178
    ctx:wait(27, 1.5, "TurnCameraOff") -- EBORABATH.scr:181
    do return ctx:exit("TRUE") end -- EBORABATH.scr:183
end

script.labels["ClearMe"] = function(ctx)
    -- EBORABATH.scr:186
    ctx:self():setFlag("FLAG_VISIBLE", false) -- EBORABATH.scr:189
    do return ctx:exit("") end -- EBORABATH.scr:192
end

script.labels["CacheFiles"] = function(ctx)
    -- EBORABATH.scr:195
    ctx:cacheClientFx("SPELL_COLUMNOFFIRE") -- EBORABATH.scr:197
    do return ctx:exit("TRUE") end -- EBORABATH.scr:199
end

script.labels["InitEboraBath"] = function(ctx)
    -- EBORABATH.scr:202
    ctx:state().hCamera = ctx:objectOrNil("EboraCam1") -- EBORABATH.scr:204
    ctx:self():setNumberProperty("CanDamage", "FALSE") -- EBORABATH.scr:207
    ctx:addTrigger("OnGossip", "OnGossip") -- EBORABATH.scr:209
    ctx:addTrigger("DeadConcubine", "DeadConcubine") -- EBORABATH.scr:210
    ctx:addTrigger("DeadPal", "DeadPal") -- EBORABATH.scr:211
    ctx:onEvent("OnFoundPlayer", "OnFoundPlayer") -- EBORABATH.scr:213
    ctx:self():setModelFilenames("models\\ebora.abc", "skins\\succubusredgstrng.dtx") -- EBORABATH.scr:215
    ctx:self():setIdle() -- EBORABATH.scr:217
    do return ctx:exit("TRUE") end -- EBORABATH.scr:219
end

script.labels["OnFoundPlayer"] = function(ctx)
    -- EBORABATH.scr:222
    ctx:onEvent("OnFoundPlayer", "DoNothing") -- EBORABATH.scr:224
    ctx:getParam(0, "g_hTarget") -- EBORABATH.scr:226
    ctx:self():playAnimation("launch", "OnLaunchDone") -- EBORABATH.scr:228
    ctx:rolloverText(14, 0) -- EBORABATH.scr:230
    do return ctx:exit("TRUE") end -- EBORABATH.scr:232
end

script.labels["OnLaunchDone"] = function(ctx)
    -- EBORABATH.scr:235
    -- gosub SetupTarget
    -- gosub AggressiveStart
    do return ctx:exit("TRUE") end -- EBORABATH.scr:240
end

script.labels["TurnCameraOn"] = function(ctx)
    -- EBORABATH.scr:243
    ctx:letterBox("TRUE") -- EBORABATH.scr:246
    ctx:trigger("hCamera", "on") -- EBORABATH.scr:247
    do return ctx:exit("TRUE") end -- EBORABATH.scr:249
end

script.labels["TurnCameraOff"] = function(ctx)
    -- EBORABATH.scr:252
    ctx:letterBox("FALSE") -- EBORABATH.scr:254
    ctx:trigger("hCamera", "off") -- EBORABATH.scr:255
    if ctx:hasKey(498) then -- EBORABATH.scr:257-258
        ctx:self():remove() -- EBORABATH.scr:259
    end -- EBORABATH.scr:260
    do return ctx:exit("TRUE") end -- EBORABATH.scr:262
end

script.labels["Main"] = function(ctx)
    -- EBORABATH.scr:266
    -- traceon
    ctx:onEvent("OnPostStartWorld", "InitEboraBath") -- EBORABATH.scr:271
    ctx:onEvent("OnPostMiniSaveLoad", "InitEboraBath") -- EBORABATH.scr:272
    ctx:onEvent("OnCacheFiles", "CacheFiles") -- EBORABATH.scr:273
    do return ctx:exit("TRUE") end -- EBORABATH.scr:275
end

script.labels["TurnCameraOn"] = function(ctx)
    -- EBORABATH.scr:278
    -- Bones
    -- overloaded
    ctx:isTurnBased("g_nTemp") -- EBORABATH.scr:283
    if ctx:condition("g_nTemp == TRUE") then -- EBORABATH.scr:284
        ctx:screenFadeOut(1) -- EBORABATH.scr:285
        ctx:rolloverText(18, 0) -- EBORABATH.scr:286
        ctx:wait(0, 1, "EscapeTheTub") -- EBORABATH.scr:287
        do return ctx:exit("") end -- EBORABATH.scr:288
    end -- EBORABATH.scr:289
    ctx:screenFadeIn(1) -- EBORABATH.scr:291
    do return mm9.gotoLabel(script, ctx, "TurnCameraOn") end -- EBORABATH.scr:292
end

return script
