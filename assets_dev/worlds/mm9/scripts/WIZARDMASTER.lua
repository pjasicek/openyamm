-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WIZARDMASTER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "CutSceneActor.inc" }

-- WizardMaster.scr
-- 01-01-02
-- by SJR
-- Purpose:
script.labels["Main"] = function(ctx)
    -- WIZARDMASTER.scr:27
    ctx:getParam(1, "sLocationName") -- WIZARDMASTER.scr:29
    ctx:command("onpoststartworld", "InitWizardMaster") -- WIZARDMASTER.scr:31
    ctx:command("oncachefiles", "CacheFiles") -- WIZARDMASTER.scr:32
    do return ctx:exit("TRUE") end -- WIZARDMASTER.scr:34
end

script.labels["InitWizardMaster"] = function(ctx)
    -- WIZARDMASTER.scr:37
    ctx:setConsoleNumVar("PLAYER_FRIEND", "TRUE") -- WIZARDMASTER.scr:39
    ctx:command("addfriend", "GreaterDemon") -- WIZARDMASTER.scr:41
    ctx:command("getmyhandle", "hMe") -- WIZARDMASTER.scr:43
    ctx:command("getobjecthandle", "sLocationName, hLocation") -- WIZARDMASTER.scr:44
    ctx:command("getpos", "hLocation, x,y,z") -- WIZARDMASTER.scr:45
    ctx:addTrigger("start", "ConjureSpell") -- WIZARDMASTER.scr:47
    ctx:addTrigger("finish", "BanishDemon") -- WIZARDMASTER.scr:48
    ctx:command("ontargetdead", "OnTargetDead") -- WIZARDMASTER.scr:50
    do return ctx:exit("TRUE") end -- WIZARDMASTER.scr:52
end

script.labels["CacheFiles"] = function(ctx)
    -- WIZARDMASTER.scr:67
    -- cache all for scene
    ctx:command("cacheclientfx", "SPELL_GREENDOTS") -- WIZARDMASTER.scr:70
    ctx:command("cacheclientfx", "SPELL_BUGS") -- WIZARDMASTER.scr:71
    ctx:command("cacheclientfx", "SPELL_BLUEDOTS") -- WIZARDMASTER.scr:72
    ctx:command("cacheclientfx", "SPELL_SPELLREAVER") -- WIZARDMASTER.scr:73
    ctx:command("cacheclientfx", "SPELL_DARKGRASP") -- WIZARDMASTER.scr:74
    ctx:command("cacheclientfx", "SPELL_PARALYZE") -- WIZARDMASTER.scr:75
    ctx:command("cacheclientfx", "SPELL_ELEMBLAST") -- WIZARDMASTER.scr:76
    ctx:command("cacheclientfx", "SPELL_COLUMNOFFIRE") -- WIZARDMASTER.scr:77
    ctx:command("cacheclientfx", "SPELL_SPARKLIES") -- WIZARDMASTER.scr:78
    ctx:command("cacheclientfx", "SPELL_TOWNPORTAL") -- WIZARDMASTER.scr:79
    ctx:command("cacheclientfx", "SPELL_METEOR") -- WIZARDMASTER.scr:80
    ctx:command("cacheclientfx", "SPELL_BLUEFIRE") -- WIZARDMASTER.scr:81
    ctx:command("cachesound", "\"sounds\\animsounds\\dragon\\hattack1.wav\"") -- WIZARDMASTER.scr:83
    ctx:command("cachesound", "\"sounds\\animsounds\\dragon\\wingattack.wav\"") -- WIZARDMASTER.scr:84
    ctx:command("cachesound", "\"sounds\\animsounds\\dragon\\rattack1.wav\"") -- WIZARDMASTER.scr:85
    ctx:command("cachesound", "\"sounds\\animsounds\\dragon\\die1.wav\"") -- WIZARDMASTER.scr:86
    ctx:command("cachesound", "\"sounds\\animsounds\\dragon\\fidget2.wav\"") -- WIZARDMASTER.scr:87
    ctx:command("cachesound", "\"sounds\\magic\\cast01.wav\"") -- WIZARDMASTER.scr:88
    ctx:command("cachesound", "\"sounds\\magic\\cast03.wav\"") -- WIZARDMASTER.scr:89
    ctx:command("cachesound", "\"sounds\\magic\\wizardeyeloop.wav\"") -- WIZARDMASTER.scr:90
    ctx:command("cachesound", "\"sounds\\ambient\\thunder\\thunderlong.wav\"") -- WIZARDMASTER.scr:91
    ctx:command("cachesound", "\"sounds\\animsounds\\evilsorcerer\\rattack1.wav\"") -- WIZARDMASTER.scr:92
    ctx:command("cachesound", "\"sounds\\animsounds\\evilsorcerer\\wince2.wav\"") -- WIZARDMASTER.scr:93
    ctx:command("cachesound", "\"sounds\\animsounds\\evilsorcerer\\die1.wav\"") -- WIZARDMASTER.scr:94
    do return ctx:exit("TRUE") end -- WIZARDMASTER.scr:96
end

script.labels["OnDeath"] = function(ctx)
    -- WIZARDMASTER.scr:99
    ctx:getParam(0, "g_hObject") -- WIZARDMASTER.scr:101
    ctx:command("isplayer", "g_hObject, g_bTemp") -- WIZARDMASTER.scr:102
    if ctx:condition("g_bTemp==TRUE") then -- WIZARDMASTER.scr:103
        ctx:setConsoleNumVar("PLAYER_FRIEND", "FALSE") -- WIZARDMASTER.scr:104
    end -- WIZARDMASTER.scr:105
    do return ctx:exit("TRUE") end -- WIZARDMASTER.scr:107
end

script.labels["OnDamage"] = function(ctx)
    -- WIZARDMASTER.scr:109
    ctx:getParam(0, "g_hObject") -- WIZARDMASTER.scr:111
    ctx:command("isplayer", "g_hObject, g_bTemp") -- WIZARDMASTER.scr:112
    if ctx:condition("g_bTemp==TRUE") then -- WIZARDMASTER.scr:113
        ctx:setConsoleNumVar("PLAYER_FRIEND", "FALSE") -- WIZARDMASTER.scr:114
    end -- WIZARDMASTER.scr:115
    do return ctx:exit("TRUE") end -- WIZARDMASTER.scr:117
end

script.labels["ConjureSpell"] = function(ctx)
    -- WIZARDMASTER.scr:120
    ctx:command("loopanim", "fidget2, 0") -- WIZARDMASTER.scr:122
    ctx:command("doclientfx", "hLocation, SPELL_METEOR, FALSE, TRUE") -- WIZARDMASTER.scr:124
    ctx:command("doclientfx", "hLocation, SPELL_TOWNPORTAL, FALSE, TRUE") -- WIZARDMASTER.scr:125
    ctx:command("doclientfx", "hLocation, SPELL_SPARKLIES, FALSE, TRUE") -- WIZARDMASTER.scr:126
    ctx:command("doclientfx", "hLocation, SPELL_COLUMNOFFIRE, FALSE, TRUE") -- WIZARDMASTER.scr:127
    ctx:command("wait", "0, 1.5, CastSpell") -- WIZARDMASTER.scr:129
    do return ctx:exit("TRUE") end -- WIZARDMASTER.scr:131
end

script.labels["CastSpell"] = function(ctx)
    -- WIZARDMASTER.scr:134
    ctx:command("playanim", "rattack1, DoNothing") -- WIZARDMASTER.scr:136
    ctx:command("playsound", "\"sounds\\magic\\cast03.wav\", DoNothing, 1, 5000, FALSE, 200") -- WIZARDMASTER.scr:138
    ctx:command("wait", "0, 1, Summon") -- WIZARDMASTER.scr:139
    do return ctx:exit("TRUE") end -- WIZARDMASTER.scr:141
end

script.labels["Summon"] = function(ctx)
    -- WIZARDMASTER.scr:144
    ctx:command("playsound", "\"sounds\\animsounds\\dragon\\fidget2.wav\", DoNothing, 1, 5000, FALSE, 200") -- WIZARDMASTER.scr:146
    ctx:command("spawn", "hLocation, x,y,z, SPAWN_PARAM") -- WIZARDMASTER.scr:147
    ctx:command("createobjectlink", "hLocation") -- WIZARDMASTER.scr:148
    ctx:command("doclientfx", "hLocation, SPELL_ELEMBLAST, FALSE, TRUE") -- WIZARDMASTER.scr:150
    ctx:command("doclientfx", "hLocation, SPELL_PARALYZE, FALSE, TRUE") -- WIZARDMASTER.scr:151
    ctx:command("playanim", "taunt, Backup") -- WIZARDMASTER.scr:153
    do return ctx:exit("TRUE") end -- WIZARDMASTER.scr:155
end

script.labels["Backup"] = function(ctx)
    -- WIZARDMASTER.scr:158
    ctx:command("wait", "0, 1, EndScene") -- WIZARDMASTER.scr:160
    ctx:command("getreversedir", "x,y,z") -- WIZARDMASTER.scr:161
    ctx:command("strafe", "x,y,z, FALSE") -- WIZARDMASTER.scr:162
    ctx:command("onobstacle", "BeginBanish") -- WIZARDMASTER.scr:163
    do return ctx:exit("TRUE") end -- WIZARDMASTER.scr:165
end

script.labels["OnTargetDead"] = function(ctx)
    -- WIZARDMASTER.scr:168
    ctx:command("hlocation", "= NULL") -- WIZARDMASTER.scr:170
    ctx:getConsoleNumVar("PLAYER_FRIEND", "g_nTemp") -- WIZARDMASTER.scr:171
    if ctx:condition("g_nTemp==FALSE") then -- WIZARDMASTER.scr:172
        ctx:command("addenemy", "Player") -- WIZARDMASTER.scr:173
        ctx:command("runscript", "\"EvilSorcerer.scr\"") -- WIZARDMASTER.scr:174
    else -- WIZARDMASTER.scr:175
        mm9.gosub(script, ctx, "PassOut") -- WIZARDMASTER.scr:176
    end -- WIZARDMASTER.scr:177
    do return ctx:exit("TRUE") end -- WIZARDMASTER.scr:179
end

script.labels["BeginBanish"] = function(ctx)
    -- WIZARDMASTER.scr:182
    ctx:command("stop", "") -- WIZARDMASTER.scr:184
    ctx:command("doclientfx", "hMe, SPELL_SPARKLIES, TRUE, TRUE") -- WIZARDMASTER.scr:186
    ctx:command("doclientfx", "hMe, SPELL_BLUEFIRE, TRUE, TRUE") -- WIZARDMASTER.scr:187
    ctx:command("loopanim", "fidget2, 0") -- WIZARDMASTER.scr:189
    do return ctx:exit("TRUE") end -- WIZARDMASTER.scr:191
end

script.labels["BanishDemon"] = function(ctx)
    -- WIZARDMASTER.scr:194
    ctx:command("ncounter", "= nCounter + 1") -- WIZARDMASTER.scr:196
    if ctx:condition("nCounter<6") then -- WIZARDMASTER.scr:197
        do return ctx:exit("TRUE") end -- WIZARDMASTER.scr:198
    end -- WIZARDMASTER.scr:199
    ctx:command("playsound", "\"sounds\\magic\\wizardeyeloop.wav\", DoNothing, 1, 5000, FALSE, 200") -- WIZARDMASTER.scr:201
    if ctx:condition("hLocation!=0") then -- WIZARDMASTER.scr:202
        ctx:command("target", "hLocation, TRUE") -- WIZARDMASTER.scr:203
        ctx:command("doclientfx", "hLocation, SPELL_DARKGRASP, TRUE, TRUE") -- WIZARDMASTER.scr:204
        ctx:trigger("hLocation", "finish") -- WIZARDMASTER.scr:205
        ctx:command("setstat", "hLocation, Gravity, FALSE") -- WIZARDMASTER.scr:206
        ctx:command("setvelocity", "hLocation, 0, 25, 0") -- WIZARDMASTER.scr:207
        ctx:command("wait", "0, 4, PerformBanish") -- WIZARDMASTER.scr:208
    end -- WIZARDMASTER.scr:209
    do return ctx:exit("TRUE") end -- WIZARDMASTER.scr:211
end

script.labels["PerformBanish"] = function(ctx)
    -- WIZARDMASTER.scr:214
    ctx:command("playsound", "\"sounds\\magic\\wizardeyeloop.wav\", DoNothing, 1, 5000, FALSE, 200") -- WIZARDMASTER.scr:216
    if ctx:condition("hLocation!=0") then -- WIZARDMASTER.scr:217
        ctx:command("setvelocity", "hLocation, 0, -50, 0") -- WIZARDMASTER.scr:218
        ctx:command("wait", "0, 2, RemoveDemon") -- WIZARDMASTER.scr:219
    end -- WIZARDMASTER.scr:220
    do return ctx:exit("TRUE") end -- WIZARDMASTER.scr:222
end

script.labels["RemoveDemon"] = function(ctx)
    -- WIZARDMASTER.scr:225
    ctx:command("playanim", "fidget3, DoNothing") -- WIZARDMASTER.scr:227
    ctx:command("playsound", "\"sounds\\magic\\cast01.wav\", DoNothing, 1, 5000, FALSE, 200") -- WIZARDMASTER.scr:228
    ctx:command("playsound", "\"sounds\\animsounds\\evilsorcerer\\rattack1.wav\", DoNothing, 1, 5000, FALSE, 200") -- WIZARDMASTER.scr:229
    ctx:command("playsound", "\"sounds\\animsounds\\dragon\\fidget2.wav\", DoNothing, 1, 5000, FALSE, 200") -- WIZARDMASTER.scr:230
    if ctx:condition("hLocation!=0") then -- WIZARDMASTER.scr:231
        ctx:command("doclientfx", "hLocation, SPELL_SPELLREAVER, FALSE, TRUE") -- WIZARDMASTER.scr:232
        ctx:command("doclientfx", "hLocation, SPELL_ELEMBLAST, FALSE, TRUE") -- WIZARDMASTER.scr:233
        ctx:trigger("hLocation", "destroy") -- WIZARDMASTER.scr:234
    end -- WIZARDMASTER.scr:235
    do return ctx:exit("TRUE") end -- WIZARDMASTER.scr:237
end

script.labels["PassOut"] = function(ctx)
    -- WIZARDMASTER.scr:240
    ctx:command("playsound", "\"sounds\\animsounds\\evilsorcerer\\wince2.wav\", DoNothing, 1, 5000, FALSE, 200") -- WIZARDMASTER.scr:242
    ctx:command("die", "") -- WIZARDMASTER.scr:243
    do return ctx:exit("TRUE") end -- WIZARDMASTER.scr:245
end

return script
