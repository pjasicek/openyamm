-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NJAMFREEZE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }

-- NjamFreeze.scr
-- By Timmy
-- 11/16
-- Manager for Njam's freezing stuff
-- flag variables
script.labels["OnChase"] = function(ctx)
    -- NJAMFREEZE.scr:22
    ctx:self():setFlag("Solid", true) -- NJAMFREEZE.scr:27
    ctx:self():setFlag("Visible", true) -- NJAMFREEZE.scr:28
    ctx:self():setFlag("Gravity", true) -- NJAMFREEZE.scr:29
    ctx:playSound("\\Sounds\\spells\\TownPortal.wav", "DoNothing", 100, 24000, "FALSE", 100) -- NJAMFREEZE.scr:30
    ctx:state().g_hobject = ctx:objectOrNil("NJamMarker") -- NJAMFREEZE.scr:32
    ctx:self():runTo(ctx:object("g_hobject"), 0, "OnArrive") -- NJAMFREEZE.scr:33
    do return ctx:exit("") end -- NJAMFREEZE.scr:34
end

script.labels["OnArrive"] = function(ctx)
    -- NJAMFREEZE.scr:37
    ctx:object("LeverHand"):trigger("Play") -- NJAMFREEZE.scr:40-41
    do return ctx:exit("") end -- NJAMFREEZE.scr:43
end

script.labels["OnPanic"] = function(ctx)
    -- NJAMFREEZE.scr:46
    ctx:object("Earthquake"):trigger("Trigger") -- NJAMFREEZE.scr:49-50
    ctx:self():playAnimation("njam_wingame", "OnFreeze") -- NJAMFREEZE.scr:51
    do return ctx:exit("") end -- NJAMFREEZE.scr:52
end

script.labels["OnFreeze"] = function(ctx)
    -- NJAMFREEZE.scr:55
    ctx:self():loopAnimation("Njam", 0, "DoNothing") -- NJAMFREEZE.scr:58
    do return ctx:exit("") end -- NJAMFREEZE.scr:59
end

script.labels["OnLightning"] = function(ctx)
    -- NJAMFREEZE.scr:62
    ctx:self():loopAnimation("njam_twitch", 0, "DoNothing") -- NJAMFREEZE.scr:68
    mm9.gosub(script, ctx, "OnFreezeSkin") -- NJAMFREEZE.scr:69
    ctx:object("Lightning1"):trigger("On") -- NJAMFREEZE.scr:70-71
    ctx:object("Lightning2"):trigger("On") -- NJAMFREEZE.scr:73-74
    ctx:wait(1, 7, "OnLightningOff") -- NJAMFREEZE.scr:76
    do return ctx:exit("") end -- NJAMFREEZE.scr:77
end

script.labels["OnLightningOff"] = function(ctx)
    -- NJAMFREEZE.scr:81
    ctx:self():loopAnimation("njam_frozen", 0, "DoNothing") -- NJAMFREEZE.scr:84
    ctx:object("Lightning1"):trigger("Off") -- NJAMFREEZE.scr:85-86
    ctx:object("Lightning2"):trigger("Off") -- NJAMFREEZE.scr:87-88
    ctx:object("Earthquake"):trigger("Off") -- NJAMFREEZE.scr:89-90
    ctx:object("winman"):trigger("Frozen") -- NJAMFREEZE.scr:91-92
    do return ctx:exit("") end -- NJAMFREEZE.scr:94
end

script.labels["OnCameraSwitch"] = function(ctx)
    -- NJAMFREEZE.scr:97
    ctx:object("WinMan"):trigger("CameraSwitch") -- NJAMFREEZE.scr:100-101
    do return ctx:exit("") end -- NJAMFREEZE.scr:103
end

script.labels["OnCameraSwitch2"] = function(ctx)
    -- NJAMFREEZE.scr:106
    ctx:object("WinMan"):trigger("CameraSwitch2") -- NJAMFREEZE.scr:109-110
    do return ctx:exit("") end -- NJAMFREEZE.scr:112
end

script.labels["OnStartBall"] = function(ctx)
    -- NJAMFREEZE.scr:115
    ctx:self():doClientFx("sSpellEffect") -- NJAMFREEZE.scr:118
    ctx:playSound("\\Sounds\\spells\\column01.wav", "DoNothing", 100, 24000, "FALSE", 100) -- NJAMFREEZE.scr:119
    do return ctx:exit("") end -- NJAMFREEZE.scr:120
end

script.labels["OnFreezeSkin"] = function(ctx)
    -- NJAMFREEZE.scr:123
    ctx:state().Model_skin = nil -- NJAMFREEZE.scr:128
    ctx:state().g_ncounter = 0 -- NJAMFREEZE.scr:129
    -- removemodelkey Freeze
    ctx:wait(2, 3, "OnFreezeSkin2") -- NJAMFREEZE.scr:132
    do return ctx:exit("") end -- NJAMFREEZE.scr:133
end

script.labels["OnFreezeSkin2"] = function(ctx)
    -- NJAMFREEZE.scr:136
    mm9.gosub(script, ctx, "SetFreezeSkin") -- NJAMFREEZE.scr:140
    ctx:playSound("\\Sounds\\spells\\Purify.wav", "DoNothing", 100, 24000, "FALSE", 100) -- NJAMFREEZE.scr:142
    ctx:self():setModelFilenames("model_name", "Model_skin") -- NJAMFREEZE.scr:143
    ctx:self():loopAnimation("njam_twitch", 0, "DoNothing") -- NJAMFREEZE.scr:144
    if ctx:condition("g_ncounter>7") then -- NJAMFREEZE.scr:146
        ctx:self():loopAnimation("njam_frozen", 0, "DoNothing") -- NJAMFREEZE.scr:147
        do return ctx:exit("") end -- NJAMFREEZE.scr:148
    end -- NJAMFREEZE.scr:149
    ctx:wait(3, .4, "OnFreezeSkin2") -- NJAMFREEZE.scr:150
    do return ctx:exit("") end -- NJAMFREEZE.scr:151
end

script.labels["SetFreezeSkin"] = function(ctx)
    -- NJAMFREEZE.scr:154
    ctx:set("g_ncounter", "g_ncounter + 1") -- NJAMFREEZE.scr:157
    if ctx:condition("g_ncounter==1") then -- NJAMFREEZE.scr:159
        ctx:set("Model_skin", "skins\\Njam1.dtx") -- NJAMFREEZE.scr:160
        do return ctx:exit("") end -- NJAMFREEZE.scr:161
    end -- NJAMFREEZE.scr:162
    if ctx:condition("g_ncounter==2") then -- NJAMFREEZE.scr:164
        ctx:set("Model_skin", "skins\\Njam2.dtx") -- NJAMFREEZE.scr:165
        do return ctx:exit("") end -- NJAMFREEZE.scr:166
    end -- NJAMFREEZE.scr:167
    if ctx:condition("g_ncounter==3") then -- NJAMFREEZE.scr:169
        ctx:set("Model_skin", "skins\\Njam3.dtx") -- NJAMFREEZE.scr:170
        do return ctx:exit("") end -- NJAMFREEZE.scr:171
    end -- NJAMFREEZE.scr:172
    if ctx:condition("g_ncounter==4") then -- NJAMFREEZE.scr:174
        ctx:set("Model_skin", "skins\\Njam4.dtx") -- NJAMFREEZE.scr:175
        do return ctx:exit("") end -- NJAMFREEZE.scr:176
    end -- NJAMFREEZE.scr:177
    if ctx:condition("g_ncounter==5") then -- NJAMFREEZE.scr:179
        ctx:set("Model_skin", "skins\\Njam5.dtx") -- NJAMFREEZE.scr:180
        do return ctx:exit("") end -- NJAMFREEZE.scr:181
    end -- NJAMFREEZE.scr:182
    if ctx:condition("g_ncounter==6") then -- NJAMFREEZE.scr:184
        ctx:set("Model_skin", "skins\\Njam6.dtx") -- NJAMFREEZE.scr:185
        do return ctx:exit("") end -- NJAMFREEZE.scr:186
    end -- NJAMFREEZE.scr:187
    if ctx:condition("g_ncounter==7") then -- NJAMFREEZE.scr:189
        ctx:set("Model_skin", "skins\\Njam7.dtx") -- NJAMFREEZE.scr:190
        do return ctx:exit("") end -- NJAMFREEZE.scr:191
    end -- NJAMFREEZE.scr:192
    do return ctx:exit("") end -- NJAMFREEZE.scr:195
end

script.labels["Init"] = function(ctx)
    -- NJAMFREEZE.scr:199
    ctx:cacheTexture("skins\\Njam1.dtx") -- NJAMFREEZE.scr:202
    ctx:cacheTexture("skins\\Njam2.dtx") -- NJAMFREEZE.scr:203
    ctx:cacheTexture("skins\\Njam3.dtx") -- NJAMFREEZE.scr:204
    ctx:cacheTexture("skins\\Njam4.dtx") -- NJAMFREEZE.scr:205
    ctx:cacheTexture("skins\\Njam5.dtx") -- NJAMFREEZE.scr:206
    ctx:cacheTexture("skins\\Njam6.dtx") -- NJAMFREEZE.scr:207
    ctx:cacheTexture("skins\\Njam7.dtx") -- NJAMFREEZE.scr:208
    ctx:self():setFlag("Visible", false) -- NJAMFREEZE.scr:211
    ctx:self():setFlag("Gravity", false) -- NJAMFREEZE.scr:212
    ctx:self():setFlag("Solid", false) -- NJAMFREEZE.scr:213
    do return ctx:exit("") end -- NJAMFREEZE.scr:215
end

script.labels["OnFootstep"] = function(ctx)
    -- NJAMFREEZE.scr:218
    ctx:playSound("\\Sounds\\AnimSounds\\Footsteps\\Dirt1.wav", "DoNothing", 100, 24000, "FALSE", 100) -- NJAMFREEZE.scr:221
    do return ctx:exit("") end -- NJAMFREEZE.scr:222
end

script.labels["Main"] = function(ctx)
    -- NJAMFREEZE.scr:225
    -- TraceOn ;delete me!!
    ctx:addTrigger("Chase", "OnChase") -- NJAMFREEZE.scr:229
    ctx:addTrigger("Panic", "OnPanic") -- NJAMFREEZE.scr:230
    ctx:addModelKey("StartBall", "OnStartBall") -- NJAMFREEZE.scr:231
    ctx:addModelKey("Lightning", "OnLightning") -- NJAMFREEZE.scr:232
    ctx:addModelKey("CameraSwitch", "OnCameraSwitch") -- NJAMFREEZE.scr:233
    ctx:addModelKey("CameraSwitch2", "OnCameraSwitch2") -- NJAMFREEZE.scr:234
    ctx:addModelKey("footstep", "OnFootstep") -- NJAMFREEZE.scr:235
    -- AddModelKey Freeze, OnFreezeskin
    ctx:addTrigger("Freeze", "OnFreezeskin") -- NJAMFREEZE.scr:237
    mm9.gosub(script, ctx, "Init") -- NJAMFREEZE.scr:238
    do return ctx:exit("") end -- NJAMFREEZE.scr:239
end

return script
