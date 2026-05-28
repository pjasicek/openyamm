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
    ctx:command("getmyhandle", "g_hmyobject") -- NJAMFREEZE.scr:26
    ctx:command("setflag", "g_hmyobject Solid") -- NJAMFREEZE.scr:27
    ctx:command("setflag", "g_hmyobject Visible") -- NJAMFREEZE.scr:28
    ctx:command("setflag", "g_hmyobject Gravity") -- NJAMFREEZE.scr:29
    ctx:command("playsound", "\\Sounds\\spells\\TownPortal.wav, DoNothing, 100, 24000, FALSE, 100") -- NJAMFREEZE.scr:30
    ctx:command("getobjecthandle", "NJamMarker g_hobject") -- NJAMFREEZE.scr:32
    ctx:command("runto", "g_hobject 0 OnArrive") -- NJAMFREEZE.scr:33
    do return ctx:exit("") end -- NJAMFREEZE.scr:34
end

script.labels["OnArrive"] = function(ctx)
    -- NJAMFREEZE.scr:37
    ctx:command("getobjecthandle", "LeverHand g_hobject") -- NJAMFREEZE.scr:40
    ctx:trigger("g_hobject", "Play") -- NJAMFREEZE.scr:41
    do return ctx:exit("") end -- NJAMFREEZE.scr:43
end

script.labels["OnPanic"] = function(ctx)
    -- NJAMFREEZE.scr:46
    ctx:command("getobjecthandle", "Earthquake g_hobject") -- NJAMFREEZE.scr:49
    ctx:trigger("g_hobject", "Trigger") -- NJAMFREEZE.scr:50
    ctx:command("playanim", "njam_wingame OnFreeze") -- NJAMFREEZE.scr:51
    do return ctx:exit("") end -- NJAMFREEZE.scr:52
end

script.labels["OnFreeze"] = function(ctx)
    -- NJAMFREEZE.scr:55
    ctx:command("loopanim", "Njam 0 DoNothing") -- NJAMFREEZE.scr:58
    do return ctx:exit("") end -- NJAMFREEZE.scr:59
end

script.labels["OnLightning"] = function(ctx)
    -- NJAMFREEZE.scr:62
    ctx:command("loopanim", "njam_twitch 0 DoNothing") -- NJAMFREEZE.scr:68
    mm9.gosub(script, ctx, "OnFreezeSkin") -- NJAMFREEZE.scr:69
    ctx:command("getobjecthandle", "Lightning1 g_hobject") -- NJAMFREEZE.scr:70
    ctx:trigger("g_hobject", "On") -- NJAMFREEZE.scr:71
    ctx:command("getobjecthandle", "Lightning2 g_hobject") -- NJAMFREEZE.scr:73
    ctx:trigger("g_hobject", "On") -- NJAMFREEZE.scr:74
    ctx:command("wait", "1 7 OnLightningOff") -- NJAMFREEZE.scr:76
    do return ctx:exit("") end -- NJAMFREEZE.scr:77
end

script.labels["OnLightningOff"] = function(ctx)
    -- NJAMFREEZE.scr:81
    ctx:command("loopanim", "njam_frozen 0 DoNothing") -- NJAMFREEZE.scr:84
    ctx:command("getobjecthandle", "Lightning1 g_hobject") -- NJAMFREEZE.scr:85
    ctx:trigger("g_hobject", "Off") -- NJAMFREEZE.scr:86
    ctx:command("getobjecthandle", "Lightning2 g_hobject") -- NJAMFREEZE.scr:87
    ctx:trigger("g_hobject", "Off") -- NJAMFREEZE.scr:88
    ctx:command("getobjecthandle", "Earthquake g_hobject") -- NJAMFREEZE.scr:89
    ctx:trigger("g_hobject", "Off") -- NJAMFREEZE.scr:90
    ctx:command("getobjecthandle", "winman g_hobject") -- NJAMFREEZE.scr:91
    ctx:trigger("g_hobject", "Frozen") -- NJAMFREEZE.scr:92
    do return ctx:exit("") end -- NJAMFREEZE.scr:94
end

script.labels["OnCameraSwitch"] = function(ctx)
    -- NJAMFREEZE.scr:97
    ctx:command("getobjecthandle", "WinMan g_hobject") -- NJAMFREEZE.scr:100
    ctx:trigger("g_hobject", "CameraSwitch") -- NJAMFREEZE.scr:101
    do return ctx:exit("") end -- NJAMFREEZE.scr:103
end

script.labels["OnCameraSwitch2"] = function(ctx)
    -- NJAMFREEZE.scr:106
    ctx:command("getobjecthandle", "WinMan g_hobject") -- NJAMFREEZE.scr:109
    ctx:trigger("g_hobject", "CameraSwitch2") -- NJAMFREEZE.scr:110
    do return ctx:exit("") end -- NJAMFREEZE.scr:112
end

script.labels["OnStartBall"] = function(ctx)
    -- NJAMFREEZE.scr:115
    ctx:command("doclientfx", "g_hmyObject,sSpellEffect") -- NJAMFREEZE.scr:118
    ctx:command("playsound", "\\Sounds\\spells\\column01.wav, DoNothing, 100, 24000, FALSE, 100") -- NJAMFREEZE.scr:119
    do return ctx:exit("") end -- NJAMFREEZE.scr:120
end

script.labels["OnFreezeSkin"] = function(ctx)
    -- NJAMFREEZE.scr:123
    ctx:command("set", "Model_skin NULL") -- NJAMFREEZE.scr:128
    ctx:command("set", "g_ncounter, 0") -- NJAMFREEZE.scr:129
    -- removemodelkey Freeze
    ctx:command("wait", "2 3 OnFreezeSkin2") -- NJAMFREEZE.scr:132
    do return ctx:exit("") end -- NJAMFREEZE.scr:133
end

script.labels["OnFreezeSkin2"] = function(ctx)
    -- NJAMFREEZE.scr:136
    mm9.gosub(script, ctx, "SetFreezeSkin") -- NJAMFREEZE.scr:140
    ctx:command("playsound", "\\Sounds\\spells\\Purify.wav, DoNothing, 100, 24000, FALSE, 100") -- NJAMFREEZE.scr:142
    ctx:command("setmodelfilenames", "model_name Model_skin") -- NJAMFREEZE.scr:143
    ctx:command("loopanim", "njam_twitch 0 DoNothing") -- NJAMFREEZE.scr:144
    if ctx:condition("g_ncounter>7") then -- NJAMFREEZE.scr:146
        ctx:command("loopanim", "njam_frozen 0 DoNothing") -- NJAMFREEZE.scr:147
        do return ctx:exit("") end -- NJAMFREEZE.scr:148
    end -- NJAMFREEZE.scr:149
    ctx:command("wait", "3 .4 OnFreezeSkin2") -- NJAMFREEZE.scr:150
    do return ctx:exit("") end -- NJAMFREEZE.scr:151
end

script.labels["SetFreezeSkin"] = function(ctx)
    -- NJAMFREEZE.scr:154
    ctx:command("g_ncounter", "= g_ncounter + 1") -- NJAMFREEZE.scr:157
    if ctx:condition("g_ncounter==1") then -- NJAMFREEZE.scr:159
        ctx:command("set", "Model_skin skins\\Njam1.dtx") -- NJAMFREEZE.scr:160
        do return ctx:exit("") end -- NJAMFREEZE.scr:161
    end -- NJAMFREEZE.scr:162
    if ctx:condition("g_ncounter==2") then -- NJAMFREEZE.scr:164
        ctx:command("set", "Model_skin skins\\Njam2.dtx") -- NJAMFREEZE.scr:165
        do return ctx:exit("") end -- NJAMFREEZE.scr:166
    end -- NJAMFREEZE.scr:167
    if ctx:condition("g_ncounter==3") then -- NJAMFREEZE.scr:169
        ctx:command("set", "Model_skin skins\\Njam3.dtx") -- NJAMFREEZE.scr:170
        do return ctx:exit("") end -- NJAMFREEZE.scr:171
    end -- NJAMFREEZE.scr:172
    if ctx:condition("g_ncounter==4") then -- NJAMFREEZE.scr:174
        ctx:command("set", "Model_skin skins\\Njam4.dtx") -- NJAMFREEZE.scr:175
        do return ctx:exit("") end -- NJAMFREEZE.scr:176
    end -- NJAMFREEZE.scr:177
    if ctx:condition("g_ncounter==5") then -- NJAMFREEZE.scr:179
        ctx:command("set", "Model_skin skins\\Njam5.dtx") -- NJAMFREEZE.scr:180
        do return ctx:exit("") end -- NJAMFREEZE.scr:181
    end -- NJAMFREEZE.scr:182
    if ctx:condition("g_ncounter==6") then -- NJAMFREEZE.scr:184
        ctx:command("set", "Model_skin skins\\Njam6.dtx") -- NJAMFREEZE.scr:185
        do return ctx:exit("") end -- NJAMFREEZE.scr:186
    end -- NJAMFREEZE.scr:187
    if ctx:condition("g_ncounter==7") then -- NJAMFREEZE.scr:189
        ctx:command("set", "Model_skin skins\\Njam7.dtx") -- NJAMFREEZE.scr:190
        do return ctx:exit("") end -- NJAMFREEZE.scr:191
    end -- NJAMFREEZE.scr:192
    do return ctx:exit("") end -- NJAMFREEZE.scr:195
end

script.labels["Init"] = function(ctx)
    -- NJAMFREEZE.scr:199
    ctx:command("cachetexture", "skins\\Njam1.dtx") -- NJAMFREEZE.scr:202
    ctx:command("cachetexture", "skins\\Njam2.dtx") -- NJAMFREEZE.scr:203
    ctx:command("cachetexture", "skins\\Njam3.dtx") -- NJAMFREEZE.scr:204
    ctx:command("cachetexture", "skins\\Njam4.dtx") -- NJAMFREEZE.scr:205
    ctx:command("cachetexture", "skins\\Njam5.dtx") -- NJAMFREEZE.scr:206
    ctx:command("cachetexture", "skins\\Njam6.dtx") -- NJAMFREEZE.scr:207
    ctx:command("cachetexture", "skins\\Njam7.dtx") -- NJAMFREEZE.scr:208
    ctx:command("getmyhandle", "g_hmyobject") -- NJAMFREEZE.scr:210
    ctx:command("clearflag", "g_hmyobject Visible") -- NJAMFREEZE.scr:211
    ctx:command("clearflag", "g_hmyobject Gravity") -- NJAMFREEZE.scr:212
    ctx:command("clearflag", "g_hmyobject Solid") -- NJAMFREEZE.scr:213
    do return ctx:exit("") end -- NJAMFREEZE.scr:215
end

script.labels["OnFootstep"] = function(ctx)
    -- NJAMFREEZE.scr:218
    ctx:command("playsound", "\\Sounds\\AnimSounds\\Footsteps\\Dirt1.wav, DoNothing, 100, 24000, FALSE, 100") -- NJAMFREEZE.scr:221
    do return ctx:exit("") end -- NJAMFREEZE.scr:222
end

script.labels["Main"] = function(ctx)
    -- NJAMFREEZE.scr:225
    -- TraceOn ;delete me!!
    ctx:addTrigger("Chase", "OnChase") -- NJAMFREEZE.scr:229
    ctx:addTrigger("Panic", "OnPanic") -- NJAMFREEZE.scr:230
    ctx:command("addmodelkey", "StartBall, OnStartBall") -- NJAMFREEZE.scr:231
    ctx:command("addmodelkey", "Lightning, OnLightning") -- NJAMFREEZE.scr:232
    ctx:command("addmodelkey", "CameraSwitch, OnCameraSwitch") -- NJAMFREEZE.scr:233
    ctx:command("addmodelkey", "CameraSwitch2, OnCameraSwitch2") -- NJAMFREEZE.scr:234
    ctx:command("addmodelkey", "footstep OnFootstep") -- NJAMFREEZE.scr:235
    -- AddModelKey Freeze, OnFreezeskin
    ctx:addTrigger("Freeze", "OnFreezeskin") -- NJAMFREEZE.scr:237
    mm9.gosub(script, ctx, "Init") -- NJAMFREEZE.scr:238
    do return ctx:exit("") end -- NJAMFREEZE.scr:239
end

return script
