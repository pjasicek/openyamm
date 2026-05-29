-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CUTSCENE.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 16, path = "CutSceneBase.inc" }

-- CutScene.inc
-- by SJR
-- 10-16-01
-- Purpose:Must be run by a camera
-- object. Handles cut scenes
-- Triggers:
-- "Next" = snap to next scene
-- "Move" = move to next scene
-- Parent must set up:
-- sNotifyName, sLocationName, sTargetName
-- LISTFIRST, LISTLAST
script.labels["InitCutScene"] = function(ctx)
    -- CUTSCENE.inc:29
    mm9.gosub(script, ctx, "InitCutSceneBase") -- CUTSCENE.inc:31
    do return ctx:exit("TRUE") end -- CUTSCENE.inc:33
end

script.labels["StartNextScene"] = function(ctx)
    -- CUTSCENE.inc:36
    mm9.gosub(script, ctx, "StartNextScene") -- CUTSCENE.inc:38
    do return ctx:exit("TRUE") end -- CUTSCENE.inc:40
end

script.labels["OnZoomToTarget"] = function(ctx)
    -- CUTSCENE.inc:43
    do return ctx:exit("TRUE") end -- CUTSCENE.inc:45
end

script.labels["OnZoomFromTarget"] = function(ctx)
    -- CUTSCENE.inc:48
    do return ctx:exit("TRUE") end -- CUTSCENE.inc:50
end

script.labels["FollowTarget"] = function(ctx)
    -- CUTSCENE.inc:53
    -- view follows the target
    ctx:self():setTarget(ctx:object("cutscene_hTarget")) -- CUTSCENE.inc:56
    do return ctx:exit("TRUE") end -- CUTSCENE.inc:58
end

script.labels["RevolveAroundTarget"] = function(ctx)
    -- CUTSCENE.inc:61
    do return ctx:exit("TRUE") end -- CUTSCENE.inc:63
end

script.labels["ZoomToTarget"] = function(ctx)
    -- CUTSCENE.inc:66
    -- closes in on the target
    ctx:state().cutscene_nDist = ctx:object("cutscene_hMe"):distanceTo(ctx:object("cutscene_hTarget")) -- CUTSCENE.inc:69
    ctx:set("cutscene_nDist", "cutscene_nDist - cutscene_nGap") -- CUTSCENE.inc:70
    ctx:state().cutscene_xDir, ctx:state().cutscene_yDir, ctx:state().cutscene_zDir = ctx:self():forwardDir() -- CUTSCENE.inc:71
    ctx:self():moveDir("cutscene_xDir", "cutscene_yDir", "cutscene_zDir", "cutscene_nDist", "cutscene_nRate", "OnZoomToTarget") -- CUTSCENE.inc:72
    do return ctx:exit("TRUE") end -- CUTSCENE.inc:74
end

script.labels["ZoomFromTarget"] = function(ctx)
    -- CUTSCENE.inc:77
    -- pulls back from target
    ctx:state().cutscene_nDist = ctx:object("cutscene_hMe"):distanceTo(ctx:object("cutscene_hTarget")) -- CUTSCENE.inc:80
    ctx:set("cutscene_nDist", "cutscene_nDist - cutscene_nGap") -- CUTSCENE.inc:81
    ctx:state().cutscene_xDir, ctx:state().cutscene_yDir, ctx:state().cutscene_zDir = ctx:object("cutscene_hMe"):rotation() -- CUTSCENE.inc:82
    ctx:set("cutscene_xDir", "cutscene_xDir * -1") -- CUTSCENE.inc:83
    ctx:set("cutscene_yDir", "cutscene_yDir * -1") -- CUTSCENE.inc:84
    ctx:set("cutscene_zDir", "cutscene_zDir * -1") -- CUTSCENE.inc:85
    ctx:self():moveDir("cutscene_xDir", "cutscene_yDir", "cutscene_zDir", "cutscene_nDist", "cutscene_nRate", "OnZoomFromTarget") -- CUTSCENE.inc:86
    do return ctx:exit("TRUE") end -- CUTSCENE.inc:88
end

return script
