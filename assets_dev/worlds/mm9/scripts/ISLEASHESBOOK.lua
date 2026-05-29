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
    ctx:state().bSafeToStart = false -- ISLEASHESBOOK.scr:32
    mm9.gosub(script, ctx, "ContainerCheck") -- ISLEASHESBOOK.scr:34
    if ctx:condition("bSafeToStart==FALSE") then -- ISLEASHESBOOK.scr:36
        do return ctx:exit("") end -- ISLEASHESBOOK.scr:37
    end -- ISLEASHESBOOK.scr:38
    if ctx:hasKey(29) then -- ISLEASHESBOOK.scr:40-41
        if not ctx:hasKey(28) then -- ISLEASHESBOOK.scr:42-43
            mm9.gosub(script, ctx, "DestroyMonsters") -- ISLEASHESBOOK.scr:44
            ctx:screenFadeOut(1) -- ISLEASHESBOOK.scr:45
            ctx:letterBox("true") -- ISLEASHESBOOK.scr:46
            ctx:object("camera0"):trigger("on") -- ISLEASHESBOOK.scr:47-48
            ctx:screenFadeIn(1) -- ISLEASHESBOOK.scr:49
            ctx:wait(1, 1, "StartDestroy") -- ISLEASHESBOOK.scr:50
            do return ctx:exit("") end -- ISLEASHESBOOK.scr:51
        end -- ISLEASHESBOOK.scr:52
    end -- ISLEASHESBOOK.scr:53
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:54
end

script.labels["ContainerCheck"] = function(ctx)
    -- ISLEASHESBOOK.scr:58
    ctx:state().g_hplayer = ctx:player() -- ISLEASHESBOOK.scr:61
    ctx:getContainerCount("g_hplayer", "g_ntemp") -- ISLEASHESBOOK.scr:62
    if ctx:condition("g_ntemp==0") then -- ISLEASHESBOOK.scr:64
        ctx:wait(1, 1, "ContainerCheck") -- ISLEASHESBOOK.scr:66
        do return ctx:exit("") end -- ISLEASHESBOOK.scr:67
    end -- ISLEASHESBOOK.scr:69
    ctx:state().g_hobject = ctx:player():container(0) -- ISLEASHESBOOK.scr:71
    ctx:state().g_btemp = ctx:object("g_hobject"):isClass("AIRail") -- ISLEASHESBOOK.scr:72
    if ctx:condition("g_btemp==TRUE") then -- ISLEASHESBOOK.scr:73
        ctx:state().bSafeToStart = true -- ISLEASHESBOOK.scr:74
    end -- ISLEASHESBOOK.scr:75
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:77
end

script.labels["DestroyMonsters"] = function(ctx)
    -- ISLEASHESBOOK.scr:81
    ctx:state().g_ntemp = 0 -- ISLEASHESBOOK.scr:84
    ctx:getObjects("AIBase", 500, 10, "g_hMonsterArray", "g_nMonsterCount") -- ISLEASHESBOOK.scr:86
    if ctx:condition("g_nMonsterCount==0") then -- ISLEASHESBOOK.scr:88
        do return ctx:exit("") end -- ISLEASHESBOOK.scr:89
    end -- ISLEASHESBOOK.scr:90
    while ctx:condition("g_nTemp < g_nMonsterCount") do -- ISLEASHESBOOK.scr:92
        ctx:arrayGet("g_hMonsterArray", "g_nTemp", "g_hObject") -- ISLEASHESBOOK.scr:94
        ctx:object("g_hobject"):remove() -- ISLEASHESBOOK.scr:95
        ctx:set("g_nTemp", "g_nTemp + 1") -- ISLEASHESBOOK.scr:97
    end -- ISLEASHESBOOK.scr:100
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:103
end

script.labels["StartDestroy"] = function(ctx)
    -- ISLEASHESBOOK.scr:106
    ctx:object("SpawnMgr"):trigger("off") -- ISLEASHESBOOK.scr:110-111
    ctx:object("FortWall"):trigger("destroy") -- ISLEASHESBOOK.scr:112-113
    ctx:wait(1, .2, "Shoot") -- ISLEASHESBOOK.scr:114
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:115
end

script.labels["Shoot"] = function(ctx)
    -- ISLEASHESBOOK.scr:119
    ctx:object("shooter"):trigger("on") -- ISLEASHESBOOK.scr:122-123
    ctx:wait(1, 1, "Camera1") -- ISLEASHESBOOK.scr:124
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:125
end

script.labels["Camera1"] = function(ctx)
    -- ISLEASHESBOOK.scr:128
    ctx:object("camera0"):trigger("off") -- ISLEASHESBOOK.scr:131-132
    ctx:object("camera1"):trigger("on") -- ISLEASHESBOOK.scr:133-134
    ctx:wait(1, 1, "Shoot2") -- ISLEASHESBOOK.scr:135
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:136
end

script.labels["Shoot2"] = function(ctx)
    -- ISLEASHESBOOK.scr:139
    ctx:object("Shooter0"):trigger("On") -- ISLEASHESBOOK.scr:141-142
    ctx:playSound("\\sounds\\spells\\ebolt01.wav", "DoNothing", 100, 24000, "FALSE", 100) -- ISLEASHESBOOK.scr:143
    ctx:wait(1, 1, "Camera2") -- ISLEASHESBOOK.scr:144
    ctx:wait(2, 1.3, "OnSink") -- ISLEASHESBOOK.scr:145
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:146
end

script.labels["Camera2"] = function(ctx)
    -- ISLEASHESBOOK.scr:149
    ctx:object("camera1"):trigger("off") -- ISLEASHESBOOK.scr:152-153
    ctx:object("camera2"):trigger("on") -- ISLEASHESBOOK.scr:154-155
    -- wait 1 1 Shoot2
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:157
end

script.labels["OnSink"] = function(ctx)
    -- ISLEASHESBOOK.scr:160
    -- explosion sound here...
    -- blub blub
    ctx:playSound("\\sounds\\spells\\eblast03.wav", "DoNothing", 100, 24000, "FALSE", 100) -- ISLEASHESBOOK.scr:165
    ctx:playSound("\\sounds\\events\\drown01.wav", "DoNothing", 100, 24000, "FALSE", 100) -- ISLEASHESBOOK.scr:166
    ctx:object("FortWall0"):trigger("destroy") -- ISLEASHESBOOK.scr:168-169
    ctx:playSound("\\sounds\\ambient\\fire\\forrestfireloop.wav", "DoNothing", 80, 24000, "FALSE", 100) -- ISLEASHESBOOK.scr:170
    -- getobjecthandle Prop19 g_hobject
    -- clearflag g_hobject, visible
    -- clearflag g_hobject, solid
    -- clearflag g_hobject, gravity
    ctx:object("Terrain3"):trigger("open") -- ISLEASHESBOOK.scr:175-176
    -- getobjecthandle Earthquake g_hobject
    -- trigger g_hobject trigger
    ctx:object("Boat"):trigger("move") -- ISLEASHESBOOK.scr:179-180
    ctx:giveKey(28) -- ISLEASHESBOOK.scr:181
    ctx:giveExp(5200) -- ISLEASHESBOOK.scr:183
    ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- ISLEASHESBOOK.scr:184
    ctx:wait(1, 4, "OnCrane") -- ISLEASHESBOOK.scr:185
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:186
end

script.labels["OnCrane"] = function(ctx)
    -- ISLEASHESBOOK.scr:190
    ctx:object("camera2"):trigger("Pan") -- ISLEASHESBOOK.scr:194-195
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:196
end

script.labels["OnCrane2"] = function(ctx)
    -- ISLEASHESBOOK.scr:199
    ctx:playSound("\\sounds\\events\\drown01.wav", "DoNothing", 100, 24000, "FALSE", 100) -- ISLEASHESBOOK.scr:202
    ctx:object("camera2"):trigger("off") -- ISLEASHESBOOK.scr:203-204
    ctx:object("camera3"):trigger("on") -- ISLEASHESBOOK.scr:205-206
    ctx:wait(1, 4, "FadeOut") -- ISLEASHESBOOK.scr:207
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:208
end

script.labels["FadeOut"] = function(ctx)
    -- ISLEASHESBOOK.scr:211
    ctx:screenFadeOut(1) -- ISLEASHESBOOK.scr:213
    ctx:wait(1, 1, "FadeOut2") -- ISLEASHESBOOK.scr:214
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:215
end

script.labels["FadeOut2"] = function(ctx)
    -- ISLEASHESBOOK.scr:218
    ctx:letterBox("False") -- ISLEASHESBOOK.scr:220
    ctx:object("camera3"):trigger("off") -- ISLEASHESBOOK.scr:221-222
    ctx:object("ExitTrigger1"):trigger("trigger") -- ISLEASHESBOOK.scr:223-224
    ctx:screenFadeIn(2) -- ISLEASHESBOOK.scr:225
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:226
end

script.labels["Init"] = function(ctx)
    -- ISLEASHESBOOK.scr:230
    if not ctx:hasKey(28) then -- ISLEASHESBOOK.scr:233-234
        do return ctx:exit("") end -- ISLEASHESBOOK.scr:235
    end -- ISLEASHESBOOK.scr:236
    ctx:object("FortWall0"):trigger("destroy") -- ISLEASHESBOOK.scr:238-239
    local object = ctx:object("Terrain3") -- ISLEASHESBOOK.scr:240
    object:trigger("sinkspeed") -- ISLEASHESBOOK.scr:241
    object:trigger("open") -- ISLEASHESBOOK.scr:242
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:243
end

script.labels["Main"] = function(ctx)
    -- ISLEASHESBOOK.scr:247
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Crane", "OnCrane2") -- ISLEASHESBOOK.scr:252
    ctx:addTrigger("Use", "OnUse") -- ISLEASHESBOOK.scr:253
    ctx:onEvent("OnPostStartWorld", "Init") -- ISLEASHESBOOK.scr:254
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- ISLEASHESBOOK.scr:255
    ctx:onEvent("OnPostSaveLoad", "Init") -- ISLEASHESBOOK.scr:256
    ctx:wait(1, .1, "Init") -- ISLEASHESBOOK.scr:257
    do return ctx:exit("") end -- ISLEASHESBOOK.scr:258
end

return script
