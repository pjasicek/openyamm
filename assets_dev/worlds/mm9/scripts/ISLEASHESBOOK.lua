-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ISLEASHESBOOK.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- IsleAshesBook.scr
-- timmy
-- handles Isle of Ashes Book Quest
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
-- flag variables
script.labels["OnUse"] = function(ctx)
    -- ISLEASHESBOOK.scr:29
    ctx:command("set", "bSafeToStart, FALSE") -- ISLEASHESBOOK.scr:32
    mm9.gosub(script, ctx, "ContainerCheck") -- ISLEASHESBOOK.scr:34
    if ctx:condition("bSafeToStart==FALSE") then -- ISLEASHESBOOK.scr:36
        do return ctx:exit("") end -- ISLEASHESBOOK.scr:37
    end -- ISLEASHESBOOK.scr:38
    if ctx:hasKey(29) then -- ISLEASHESBOOK.scr:40-41
        if not ctx:hasKey(28) then -- ISLEASHESBOOK.scr:42-43
            mm9.gosub(script, ctx, "DestroyMonsters") -- ISLEASHESBOOK.scr:44
            ctx:command("screenfadeout", "1") -- ISLEASHESBOOK.scr:45
            ctx:command("letterbox", "true") -- ISLEASHESBOOK.scr:46
            ctx:command("getobjecthandle", "camera0 g_hobject") -- ISLEASHESBOOK.scr:47
            ctx:trigger("g_hobject", "on") -- ISLEASHESBOOK.scr:48
            ctx:command("screenfadein", "1") -- ISLEASHESBOOK.scr:49
            ctx:command("wait", "1 1 StartDestroy") -- ISLEASHESBOOK.scr:50
            do return ctx:exit("") end -- ISLEASHESBOOK.scr:51
        end -- ISLEASHESBOOK.scr:52
    end -- ISLEASHESBOOK.scr:53
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:54
end

script.labels["ContainerCheck"] = function(ctx)
    -- ISLEASHESBOOK.scr:58
    ctx:command("getplayerhandle", "g_hplayer") -- ISLEASHESBOOK.scr:61
    ctx:command("getcontainercount", "g_hplayer g_ntemp") -- ISLEASHESBOOK.scr:62
    if ctx:condition("g_ntemp==0") then -- ISLEASHESBOOK.scr:64
        ctx:command("wait", "1 1 ContainerCheck") -- ISLEASHESBOOK.scr:66
        do return ctx:exit("") end -- ISLEASHESBOOK.scr:67
    end -- ISLEASHESBOOK.scr:69
    ctx:command("getcontainer", "g_hplayer 0 g_hobject") -- ISLEASHESBOOK.scr:71
    ctx:command("isclass", "g_hobject AIRail g_btemp") -- ISLEASHESBOOK.scr:72
    if ctx:condition("g_btemp==TRUE") then -- ISLEASHESBOOK.scr:73
        ctx:command("set", "bSafeToStart, True") -- ISLEASHESBOOK.scr:74
    end -- ISLEASHESBOOK.scr:75
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:77
end

script.labels["DestroyMonsters"] = function(ctx)
    -- ISLEASHESBOOK.scr:81
    ctx:command("set", "g_ntemp, 0") -- ISLEASHESBOOK.scr:84
    ctx:command("getobjects", "AIBase, 500, 10, g_hMonsterArray, g_nMonsterCount") -- ISLEASHESBOOK.scr:86
    if ctx:condition("g_nMonsterCount==0") then -- ISLEASHESBOOK.scr:88
        do return ctx:exit("") end -- ISLEASHESBOOK.scr:89
    end -- ISLEASHESBOOK.scr:90
    while ctx:condition("g_nTemp < g_nMonsterCount") do -- ISLEASHESBOOK.scr:92
        ctx:command("arrayget", "g_hMonsterArray, g_nTemp, g_hObject") -- ISLEASHESBOOK.scr:94
        ctx:command("removeobject", "g_hobject") -- ISLEASHESBOOK.scr:95
        ctx:command("g_ntemp", "= g_nTemp + 1") -- ISLEASHESBOOK.scr:97
    end -- ISLEASHESBOOK.scr:100
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:103
end

script.labels["StartDestroy"] = function(ctx)
    -- ISLEASHESBOOK.scr:106
    ctx:command("getobjecthandle", "SpawnMgr g_hobject") -- ISLEASHESBOOK.scr:110
    ctx:trigger("g_hobject", "off") -- ISLEASHESBOOK.scr:111
    ctx:command("getobjecthandle", "FortWall g_hobject") -- ISLEASHESBOOK.scr:112
    ctx:trigger("g_hobject", "destroy") -- ISLEASHESBOOK.scr:113
    ctx:command("wait", "1 .2 Shoot") -- ISLEASHESBOOK.scr:114
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:115
end

script.labels["Shoot"] = function(ctx)
    -- ISLEASHESBOOK.scr:119
    ctx:command("getobjecthandle", "shooter g_hobject") -- ISLEASHESBOOK.scr:122
    ctx:trigger("g_hobject", "on") -- ISLEASHESBOOK.scr:123
    ctx:command("wait", "1 1 Camera1") -- ISLEASHESBOOK.scr:124
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:125
end

script.labels["Camera1"] = function(ctx)
    -- ISLEASHESBOOK.scr:128
    ctx:command("getobjecthandle", "camera0 g_hobject") -- ISLEASHESBOOK.scr:131
    ctx:trigger("g_hobject", "off") -- ISLEASHESBOOK.scr:132
    ctx:command("getobjecthandle", "camera1 g_hobject") -- ISLEASHESBOOK.scr:133
    ctx:trigger("g_hobject", "on") -- ISLEASHESBOOK.scr:134
    ctx:command("wait", "1 1 Shoot2") -- ISLEASHESBOOK.scr:135
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:136
end

script.labels["Shoot2"] = function(ctx)
    -- ISLEASHESBOOK.scr:139
    ctx:command("getobjecthandle", "Shooter0 g_hobject") -- ISLEASHESBOOK.scr:141
    ctx:trigger("g_hobject", "On") -- ISLEASHESBOOK.scr:142
    ctx:command("playsound", "\\sounds\\spells\\ebolt01.wav, DoNothing, 100, 24000, FALSE, 100") -- ISLEASHESBOOK.scr:143
    ctx:command("wait", "1 1 Camera2") -- ISLEASHESBOOK.scr:144
    ctx:command("wait", "2 1.3 OnSink") -- ISLEASHESBOOK.scr:145
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:146
end

script.labels["Camera2"] = function(ctx)
    -- ISLEASHESBOOK.scr:149
    ctx:command("getobjecthandle", "camera1 g_hobject") -- ISLEASHESBOOK.scr:152
    ctx:trigger("g_hobject", "off") -- ISLEASHESBOOK.scr:153
    ctx:command("getobjecthandle", "camera2 g_hobject") -- ISLEASHESBOOK.scr:154
    ctx:trigger("g_hobject", "on") -- ISLEASHESBOOK.scr:155
    -- wait 1 1 Shoot2
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:157
end

script.labels["OnSink"] = function(ctx)
    -- ISLEASHESBOOK.scr:160
    -- explosion sound here...
    -- blub blub
    ctx:command("playsound", "\\sounds\\spells\\eblast03.wav, DoNothing, 100, 24000, FALSE, 100") -- ISLEASHESBOOK.scr:165
    ctx:command("playsound", "\\sounds\\events\\drown01.wav, DoNothing, 100, 24000, FALSE, 100") -- ISLEASHESBOOK.scr:166
    ctx:command("getobjecthandle", "FortWall0 g_hobject") -- ISLEASHESBOOK.scr:168
    ctx:trigger("g_hobject", "destroy") -- ISLEASHESBOOK.scr:169
    ctx:command("playsound", "\\sounds\\ambient\\fire\\forrestfireloop.wav, DoNothing, 80, 24000, FALSE, 100") -- ISLEASHESBOOK.scr:170
    -- getobjecthandle Prop19 g_hobject
    -- clearflag g_hobject, visible
    -- clearflag g_hobject, solid
    -- clearflag g_hobject, gravity
    ctx:command("getobjecthandle", "Terrain3 g_hobject") -- ISLEASHESBOOK.scr:175
    ctx:trigger("g_hobject", "open") -- ISLEASHESBOOK.scr:176
    -- getobjecthandle Earthquake g_hobject
    -- trigger g_hobject trigger
    ctx:command("getobjecthandle", "Boat g_hobject") -- ISLEASHESBOOK.scr:179
    ctx:trigger("g_hobject", "move") -- ISLEASHESBOOK.scr:180
    ctx:giveKey(28) -- ISLEASHESBOOK.scr:181
    ctx:giveExp(5200) -- ISLEASHESBOOK.scr:183
    ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- ISLEASHESBOOK.scr:184
    ctx:command("wait", "1 4 OnCrane") -- ISLEASHESBOOK.scr:185
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:186
end

script.labels["OnCrane"] = function(ctx)
    -- ISLEASHESBOOK.scr:190
    ctx:command("getobjecthandle", "camera2 g_hobject") -- ISLEASHESBOOK.scr:194
    ctx:trigger("g_hobject", "Pan") -- ISLEASHESBOOK.scr:195
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:196
end

script.labels["OnCrane2"] = function(ctx)
    -- ISLEASHESBOOK.scr:199
    ctx:command("playsound", "\\sounds\\events\\drown01.wav, DoNothing, 100, 24000, FALSE, 100") -- ISLEASHESBOOK.scr:202
    ctx:command("getobjecthandle", "camera2 g_hobject") -- ISLEASHESBOOK.scr:203
    ctx:trigger("g_hobject", "off") -- ISLEASHESBOOK.scr:204
    ctx:command("getobjecthandle", "camera3 g_hobject") -- ISLEASHESBOOK.scr:205
    ctx:trigger("g_hobject", "on") -- ISLEASHESBOOK.scr:206
    ctx:command("wait", "1 4 FadeOut") -- ISLEASHESBOOK.scr:207
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:208
end

script.labels["FadeOut"] = function(ctx)
    -- ISLEASHESBOOK.scr:211
    ctx:command("screenfadeout", "1") -- ISLEASHESBOOK.scr:213
    ctx:command("wait", "1 1 FadeOut2") -- ISLEASHESBOOK.scr:214
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:215
end

script.labels["FadeOut2"] = function(ctx)
    -- ISLEASHESBOOK.scr:218
    ctx:command("letterbox", "False") -- ISLEASHESBOOK.scr:220
    ctx:command("getobjecthandle", "camera3 g_hobject") -- ISLEASHESBOOK.scr:221
    ctx:trigger("g_hobject", "off") -- ISLEASHESBOOK.scr:222
    ctx:command("getobjecthandle", "ExitTrigger1 g_hobject") -- ISLEASHESBOOK.scr:223
    ctx:trigger("g_hobject", "trigger") -- ISLEASHESBOOK.scr:224
    ctx:command("screenfadein", "2") -- ISLEASHESBOOK.scr:225
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:226
end

script.labels["Init"] = function(ctx)
    -- ISLEASHESBOOK.scr:230
    if not ctx:hasKey(28) then -- ISLEASHESBOOK.scr:233-234
        do return ctx:exit("") end -- ISLEASHESBOOK.scr:235
    end -- ISLEASHESBOOK.scr:236
    ctx:command("getobjecthandle", "FortWall0 g_hobject") -- ISLEASHESBOOK.scr:238
    ctx:trigger("g_hobject", "destroy") -- ISLEASHESBOOK.scr:239
    ctx:command("getobjecthandle", "Terrain3 g_hobject") -- ISLEASHESBOOK.scr:240
    ctx:trigger("g_hobject", "sinkspeed") -- ISLEASHESBOOK.scr:241
    ctx:trigger("g_hobject", "open") -- ISLEASHESBOOK.scr:242
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:243
end

script.labels["Main"] = function(ctx)
    -- ISLEASHESBOOK.scr:247
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Crane", "OnCrane2") -- ISLEASHESBOOK.scr:252
    ctx:addTrigger("Use", "OnUse") -- ISLEASHESBOOK.scr:253
    ctx:command("onpoststartworld", "Init") -- ISLEASHESBOOK.scr:254
    ctx:command("onpostminisaveload", "Init") -- ISLEASHESBOOK.scr:255
    ctx:command("onpostsaveload", "Init") -- ISLEASHESBOOK.scr:256
    ctx:command("wait", "1 .1 Init") -- ISLEASHESBOOK.scr:257
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:258
end

return script
