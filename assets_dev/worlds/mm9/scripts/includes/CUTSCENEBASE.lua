-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CUTSCENEBASE.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "ListMaker.inc" }

-- BaseCutScene.inc
-- by SJR
-- 10-16-01
-- Purpose:base include for cut scenes
-- Parent must set up:
-- sNotifyName, sLocationName, sTargetName, LISTFIRST, LISTLAST
script.labels["InitCutSceneBase"] = function(ctx)
    -- CUTSCENEBASE.inc:29
    -- must set up your vars
    -- before calling this
    -- get last one, then wrap to first
    ctx:command("listindex", "= LISTLAST") -- CUTSCENEBASE.inc:34
    ctx:command("getmyhandle", "cutscene_hMe") -- CUTSCENEBASE.inc:36
    ctx:command("getobjectname", "cutscene_hMe, cutscene_sMyName") -- CUTSCENEBASE.inc:37
    ctx:setConsoleStrVar("CUTSCENE_NAME", "cutscene_sMyName") -- CUTSCENEBASE.inc:38
    ctx:addTrigger("Next", "StartNextScene") -- CUTSCENEBASE.inc:40
    do return ctx:exit("TRUE") end -- CUTSCENEBASE.inc:42
end

script.labels["SceneInterrupt"] = function(ctx)
    -- CUTSCENEBASE.inc:45
    -- look at something not on the list
    ctx:getParam(0, "cutscene_hTarget") -- CUTSCENEBASE.inc:48
    mm9.gosub(script, ctx, "AlignCamera") -- CUTSCENEBASE.inc:49
    if ctx:condition("LISTINDEX==LISTFIRST") then -- CUTSCENEBASE.inc:51
        mm9.gosub(script, ctx, "CameraOn") -- CUTSCENEBASE.inc:52
    end -- CUTSCENEBASE.inc:53
    -- put it into "last scene mode"
    if ctx:condition("LISTINDEX==LISTLAST") then -- CUTSCENEBASE.inc:56
        ctx:command("removetrigger", "Next") -- CUTSCENEBASE.inc:57
        ctx:addTrigger("Next", "CameraOff") -- CUTSCENEBASE.inc:58
    end -- CUTSCENEBASE.inc:59
    do return ctx:exit("TRUE") end -- CUTSCENEBASE.inc:61
end

script.labels["StartNextScene"] = function(ctx)
    -- CUTSCENEBASE.inc:64
    -- next set of locations+targets
    mm9.gosub(script, ctx, "GetNextLocation") -- CUTSCENEBASE.inc:67
    -- quit if either object is bad
    if ctx:condition("cutscene_hLocation==0") then -- CUTSCENEBASE.inc:69
        mm9.gosub(script, ctx, "CameraOff") -- CUTSCENEBASE.inc:70
        do return ctx:exit("TRUE") end -- CUTSCENEBASE.inc:71
    end -- CUTSCENEBASE.inc:72
    if ctx:condition("cutscene_hTarget==0") then -- CUTSCENEBASE.inc:73
        mm9.gosub(script, ctx, "CameraOff") -- CUTSCENEBASE.inc:74
        do return ctx:exit("TRUE") end -- CUTSCENEBASE.inc:75
    end -- CUTSCENEBASE.inc:76
    mm9.gosub(script, ctx, "AlignCamera") -- CUTSCENEBASE.inc:78
    ctx:trigger("cutscene_hNotify", "trigger") -- CUTSCENEBASE.inc:79
    -- only turn cam on once, otherwise blinking occurs
    if ctx:condition("LISTINDEX==LISTFIRST") then -- CUTSCENEBASE.inc:82
        mm9.gosub(script, ctx, "CameraOn") -- CUTSCENEBASE.inc:83
    end -- CUTSCENEBASE.inc:84
    -- put it into "last scene mode"
    if ctx:condition("LISTINDEX==LISTLAST") then -- CUTSCENEBASE.inc:87
        ctx:command("removetrigger", "Next") -- CUTSCENEBASE.inc:88
        ctx:addTrigger("Next", "CameraOff") -- CUTSCENEBASE.inc:89
    end -- CUTSCENEBASE.inc:90
    do return ctx:exit("TRUE") end -- CUTSCENEBASE.inc:92
end

script.labels["GetNextLocation"] = function(ctx)
    -- CUTSCENEBASE.inc:95
    -- advance all scene objects by 1
    ctx:command("listname", "= sLocationName") -- CUTSCENEBASE.inc:98
    mm9.gosub(script, ctx, "GetNextObject") -- CUTSCENEBASE.inc:99
    ctx:command("cutscene_hlocation", "= LISTOBJECT") -- CUTSCENEBASE.inc:100
    ctx:command("listname", "= sTargetName") -- CUTSCENEBASE.inc:102
    mm9.gosub(script, ctx, "GetCurrentObject") -- CUTSCENEBASE.inc:103
    ctx:command("cutscene_htarget", "= LISTOBJECT") -- CUTSCENEBASE.inc:104
    ctx:command("listname", "= sNotifyName") -- CUTSCENEBASE.inc:106
    mm9.gosub(script, ctx, "GetCurrentObject") -- CUTSCENEBASE.inc:107
    ctx:command("cutscene_hnotify", "= LISTOBJECT") -- CUTSCENEBASE.inc:108
    do return ctx:exit("TRUE") end -- CUTSCENEBASE.inc:110
end

script.labels["AlignCamera"] = function(ctx)
    -- CUTSCENEBASE.inc:113
    -- sets pos to cutscene_hLocation
    -- sets dir to cutscene_hTarget
    ctx:command("getpos", "cutscene_hLocation, cutscene_x,cutscene_y,cutscene_z") -- CUTSCENEBASE.inc:117
    ctx:command("setpos", "cutscene_hMe, cutscene_x,cutscene_y,cutscene_z") -- CUTSCENEBASE.inc:118
    ctx:command("faceobject", "cutscene_hTarget, 0, DoNothing") -- CUTSCENEBASE.inc:119
    do return ctx:exit("TRUE") end -- CUTSCENEBASE.inc:121
end

script.labels["CameraOn"] = function(ctx)
    -- CUTSCENEBASE.inc:124
    -- camera and letterbox on
    mm9.gosub(script, ctx, "OnSceneStart") -- CUTSCENEBASE.inc:127
    ctx:trigger("cutscene_hMe", "on") -- CUTSCENEBASE.inc:128
    ctx:command("letterbox", "TRUE") -- CUTSCENEBASE.inc:130
    do return ctx:exit("TRUE") end -- CUTSCENEBASE.inc:132
end

script.labels["CameraOff"] = function(ctx)
    -- CUTSCENEBASE.inc:135
    -- camera, letterbox, fade off
    ctx:trigger("cutscene_hMe", "off") -- CUTSCENEBASE.inc:138
    mm9.gosub(script, ctx, "OnSceneDone") -- CUTSCENEBASE.inc:139
    ctx:command("letterbox", "FALSE") -- CUTSCENEBASE.inc:141
    do return ctx:exit("TRUE") end -- CUTSCENEBASE.inc:143
end

script.labels["OnSceneDone"] = function(ctx)
    -- CUTSCENEBASE.inc:146
    -- called when the entire sequence
    -- is done. override this routine
    do return ctx:exit(1) end -- CUTSCENEBASE.inc:150
end

script.labels["OnSceneStart"] = function(ctx)
    -- CUTSCENEBASE.inc:153
    -- called when the entire sequence
    -- has started. override this routine
    do return ctx:exit(1) end -- CUTSCENEBASE.inc:157
end

return script
