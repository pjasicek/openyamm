-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "E3DUNGEONDIRECTOR.scr"
script.includes = {}
script.labels = {}


-- Director.scr
-- John Machin
-- This script handles all camera movement and cut scenes
script.labels["OnStartPendulumPath"] = function(ctx)
    -- E3DUNGEONDIRECTOR.scr:12
    if ctx:condition("start = 1") then -- E3DUNGEONDIRECTOR.scr:14
        do return ctx:exit("") end -- E3DUNGEONDIRECTOR.scr:15
    end -- E3DUNGEONDIRECTOR.scr:16
    ctx:command("getobjecthandle", "camera0,hCamera0") -- E3DUNGEONDIRECTOR.scr:18
    ctx:trigger("hCamera0", "StartPendulum") -- E3DUNGEONDIRECTOR.scr:19
    ctx:command("set", "start,1") -- E3DUNGEONDIRECTOR.scr:21
    do return ctx:exit("") end -- E3DUNGEONDIRECTOR.scr:23
end

script.labels["OnStartThronePath"] = function(ctx)
    -- E3DUNGEONDIRECTOR.scr:26
    ctx:command("getobjecthandle", "camera0,hCamera0") -- E3DUNGEONDIRECTOR.scr:28
    ctx:trigger("hCamera0", "StartThrone") -- E3DUNGEONDIRECTOR.scr:29
    do return ctx:exit("") end -- E3DUNGEONDIRECTOR.scr:31
end

script.labels["OnStartScythePath"] = function(ctx)
    -- E3DUNGEONDIRECTOR.scr:34
    ctx:command("getobjecthandle", "camera0,hCamera0") -- E3DUNGEONDIRECTOR.scr:36
    ctx:trigger("hCamera0", "StartScythe") -- E3DUNGEONDIRECTOR.scr:37
    do return ctx:exit("") end -- E3DUNGEONDIRECTOR.scr:39
end

script.labels["OnStartSawPath"] = function(ctx)
    -- E3DUNGEONDIRECTOR.scr:42
    ctx:command("getobjecthandle", "camera0,hCamera0") -- E3DUNGEONDIRECTOR.scr:44
    ctx:trigger("hCamera0", "StartSaw") -- E3DUNGEONDIRECTOR.scr:45
    do return ctx:exit("") end -- E3DUNGEONDIRECTOR.scr:47
end

script.labels["OnStartWardrobePath"] = function(ctx)
    -- E3DUNGEONDIRECTOR.scr:50
    ctx:command("getobjecthandle", "camera0,hCamera0") -- E3DUNGEONDIRECTOR.scr:52
    ctx:trigger("hCamera0", "StartWardrobe") -- E3DUNGEONDIRECTOR.scr:53
    do return ctx:exit("") end -- E3DUNGEONDIRECTOR.scr:55
end

script.labels["OnStartWardrobe2Path"] = function(ctx)
    -- E3DUNGEONDIRECTOR.scr:58
    ctx:command("getobjecthandle", "camera0,hCamera0") -- E3DUNGEONDIRECTOR.scr:60
    ctx:trigger("hCamera0", "StartWardrobe2") -- E3DUNGEONDIRECTOR.scr:61
    do return ctx:exit("") end -- E3DUNGEONDIRECTOR.scr:63
end

script.labels["OnStartSconcePath"] = function(ctx)
    -- E3DUNGEONDIRECTOR.scr:66
    ctx:command("getobjecthandle", "camera0,hCamera0") -- E3DUNGEONDIRECTOR.scr:68
    ctx:trigger("hCamera0", "StartSconce") -- E3DUNGEONDIRECTOR.scr:69
    do return ctx:exit("") end -- E3DUNGEONDIRECTOR.scr:71
end

script.labels["OnStartTreasurePath"] = function(ctx)
    -- E3DUNGEONDIRECTOR.scr:74
    ctx:command("getobjecthandle", "camera0,hCamera0") -- E3DUNGEONDIRECTOR.scr:76
    ctx:trigger("hCamera0", "StartTreasure") -- E3DUNGEONDIRECTOR.scr:77
    do return ctx:exit("") end -- E3DUNGEONDIRECTOR.scr:79
end

script.labels["OnStartPitPath"] = function(ctx)
    -- E3DUNGEONDIRECTOR.scr:82
    ctx:command("getobjecthandle", "camera0,hCamera0") -- E3DUNGEONDIRECTOR.scr:84
    ctx:trigger("hCamera0", "StartPit") -- E3DUNGEONDIRECTOR.scr:85
    do return ctx:exit("") end -- E3DUNGEONDIRECTOR.scr:87
end

script.labels["OnStartPit2Path"] = function(ctx)
    -- E3DUNGEONDIRECTOR.scr:90
    ctx:command("getobjecthandle", "camera0,hCamera0") -- E3DUNGEONDIRECTOR.scr:92
    ctx:trigger("hCamera0", "StartPit2") -- E3DUNGEONDIRECTOR.scr:93
    do return ctx:exit("") end -- E3DUNGEONDIRECTOR.scr:95
end

script.labels["OnStartTrapDoorPath"] = function(ctx)
    -- E3DUNGEONDIRECTOR.scr:98
    ctx:command("getobjecthandle", "camera0,hCamera0") -- E3DUNGEONDIRECTOR.scr:100
    ctx:trigger("hCamera0", "StartTrapDoor") -- E3DUNGEONDIRECTOR.scr:101
    do return ctx:exit("") end -- E3DUNGEONDIRECTOR.scr:103
end

script.labels["OnStartChasmPath"] = function(ctx)
    -- E3DUNGEONDIRECTOR.scr:106
    ctx:command("getobjecthandle", "camera0,hCamera0") -- E3DUNGEONDIRECTOR.scr:108
    ctx:trigger("hCamera0", "StartChasm") -- E3DUNGEONDIRECTOR.scr:109
    do return ctx:exit("") end -- E3DUNGEONDIRECTOR.scr:111
end

script.labels["OnStartLichPath"] = function(ctx)
    -- E3DUNGEONDIRECTOR.scr:114
    ctx:command("getobjecthandle", "camera0,hCamera0") -- E3DUNGEONDIRECTOR.scr:116
    ctx:trigger("hCamera0", "StartLich") -- E3DUNGEONDIRECTOR.scr:117
    do return ctx:exit("") end -- E3DUNGEONDIRECTOR.scr:119
end

script.labels["Main"] = function(ctx)
    -- E3DUNGEONDIRECTOR.scr:122
    -- This routine is automatically run
    -- at script startup...
    -- TraceOn
    ctx:addTrigger("StartPendulumPath", "OnStartPendulumPath") -- E3DUNGEONDIRECTOR.scr:129
    ctx:addTrigger("StartThronePath", "OnStartThronePath") -- E3DUNGEONDIRECTOR.scr:130
    ctx:addTrigger("StartScythePath", "OnStartScythePath") -- E3DUNGEONDIRECTOR.scr:131
    ctx:addTrigger("StartSawPath", "OnStartSawPath") -- E3DUNGEONDIRECTOR.scr:132
    ctx:addTrigger("StartWardrobePath", "OnStartWardrobePath") -- E3DUNGEONDIRECTOR.scr:133
    ctx:addTrigger("StartWardrobe2Path", "OnStartWardrobe2Path") -- E3DUNGEONDIRECTOR.scr:134
    ctx:addTrigger("StartSconcePath", "OnStartSconcePath") -- E3DUNGEONDIRECTOR.scr:135
    ctx:addTrigger("StartTreasurePath", "OnStartTreasurePath") -- E3DUNGEONDIRECTOR.scr:136
    ctx:addTrigger("StartPitPath", "OnStartPitPath") -- E3DUNGEONDIRECTOR.scr:137
    ctx:addTrigger("StartPit2Path", "OnStartPit2Path") -- E3DUNGEONDIRECTOR.scr:138
    ctx:addTrigger("StartTrapDoorPath", "OnStartTrapDoorPath") -- E3DUNGEONDIRECTOR.scr:139
    ctx:addTrigger("StartChasmPath", "OnStartChasmPath") -- E3DUNGEONDIRECTOR.scr:140
    ctx:addTrigger("StartLichPath", "OnStartLichPath") -- E3DUNGEONDIRECTOR.scr:141
    do return ctx:exit("") end -- E3DUNGEONDIRECTOR.scr:143
end

return script
