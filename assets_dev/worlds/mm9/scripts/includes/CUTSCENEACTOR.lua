-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CUTSCENEACTOR.inc"
script.includes = {}
script.labels = {}


-- CutSceneActor.inc
-- by SJR
-- 11-07-01
-- Purpose:single routine for
-- messaging CutScene.inc
-- when scene done
script.labels["EndScene"] = function(ctx)
    -- CUTSCENEACTOR.inc:14
    -- call this once at the end of each scene
    -- get the registered name of the camera
    if ctx:condition("sceneactor_hCamera==0") then -- CUTSCENEACTOR.inc:18
        ctx:getConsoleStrVar("CUTSCENE_NAME", "sceneactor_sCameraName") -- CUTSCENEACTOR.inc:19
        ctx:command("getobjecthandle", "sceneactor_sCameraName, sceneactor_hCamera") -- CUTSCENEACTOR.inc:20
        if ctx:condition("sceneactor_hCamera==0") then -- CUTSCENEACTOR.inc:21
            do return ctx:exit(1) end -- CUTSCENEACTOR.inc:22
        end -- CUTSCENEACTOR.inc:23
    end -- CUTSCENEACTOR.inc:24
    -- signal it to advance to the next scene
    ctx:trigger("sceneactor_hCamera", "Next") -- CUTSCENEACTOR.inc:27
    do return ctx:exit(1) end -- CUTSCENEACTOR.inc:29
end

return script
