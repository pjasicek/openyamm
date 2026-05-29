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
    ctx:object("camera0"):trigger("StartPendulum") -- E3DUNGEONDIRECTOR.scr:18-19
    ctx:state().start = 1 -- E3DUNGEONDIRECTOR.scr:21
    do return ctx:exit("") end -- E3DUNGEONDIRECTOR.scr:23
end

script.labels["OnStartThronePath"] = function(ctx)
    -- E3DUNGEONDIRECTOR.scr:26
    ctx:object("camera0"):trigger("StartThrone") -- E3DUNGEONDIRECTOR.scr:28-29
    do return ctx:exit("") end -- E3DUNGEONDIRECTOR.scr:31
end

script.labels["OnStartScythePath"] = function(ctx)
    -- E3DUNGEONDIRECTOR.scr:34
    ctx:object("camera0"):trigger("StartScythe") -- E3DUNGEONDIRECTOR.scr:36-37
    do return ctx:exit("") end -- E3DUNGEONDIRECTOR.scr:39
end

script.labels["OnStartSawPath"] = function(ctx)
    -- E3DUNGEONDIRECTOR.scr:42
    ctx:object("camera0"):trigger("StartSaw") -- E3DUNGEONDIRECTOR.scr:44-45
    do return ctx:exit("") end -- E3DUNGEONDIRECTOR.scr:47
end

script.labels["OnStartWardrobePath"] = function(ctx)
    -- E3DUNGEONDIRECTOR.scr:50
    ctx:object("camera0"):trigger("StartWardrobe") -- E3DUNGEONDIRECTOR.scr:52-53
    do return ctx:exit("") end -- E3DUNGEONDIRECTOR.scr:55
end

script.labels["OnStartWardrobe2Path"] = function(ctx)
    -- E3DUNGEONDIRECTOR.scr:58
    ctx:object("camera0"):trigger("StartWardrobe2") -- E3DUNGEONDIRECTOR.scr:60-61
    do return ctx:exit("") end -- E3DUNGEONDIRECTOR.scr:63
end

script.labels["OnStartSconcePath"] = function(ctx)
    -- E3DUNGEONDIRECTOR.scr:66
    ctx:object("camera0"):trigger("StartSconce") -- E3DUNGEONDIRECTOR.scr:68-69
    do return ctx:exit("") end -- E3DUNGEONDIRECTOR.scr:71
end

script.labels["OnStartTreasurePath"] = function(ctx)
    -- E3DUNGEONDIRECTOR.scr:74
    ctx:object("camera0"):trigger("StartTreasure") -- E3DUNGEONDIRECTOR.scr:76-77
    do return ctx:exit("") end -- E3DUNGEONDIRECTOR.scr:79
end

script.labels["OnStartPitPath"] = function(ctx)
    -- E3DUNGEONDIRECTOR.scr:82
    ctx:object("camera0"):trigger("StartPit") -- E3DUNGEONDIRECTOR.scr:84-85
    do return ctx:exit("") end -- E3DUNGEONDIRECTOR.scr:87
end

script.labels["OnStartPit2Path"] = function(ctx)
    -- E3DUNGEONDIRECTOR.scr:90
    ctx:object("camera0"):trigger("StartPit2") -- E3DUNGEONDIRECTOR.scr:92-93
    do return ctx:exit("") end -- E3DUNGEONDIRECTOR.scr:95
end

script.labels["OnStartTrapDoorPath"] = function(ctx)
    -- E3DUNGEONDIRECTOR.scr:98
    ctx:object("camera0"):trigger("StartTrapDoor") -- E3DUNGEONDIRECTOR.scr:100-101
    do return ctx:exit("") end -- E3DUNGEONDIRECTOR.scr:103
end

script.labels["OnStartChasmPath"] = function(ctx)
    -- E3DUNGEONDIRECTOR.scr:106
    ctx:object("camera0"):trigger("StartChasm") -- E3DUNGEONDIRECTOR.scr:108-109
    do return ctx:exit("") end -- E3DUNGEONDIRECTOR.scr:111
end

script.labels["OnStartLichPath"] = function(ctx)
    -- E3DUNGEONDIRECTOR.scr:114
    ctx:object("camera0"):trigger("StartLich") -- E3DUNGEONDIRECTOR.scr:116-117
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
