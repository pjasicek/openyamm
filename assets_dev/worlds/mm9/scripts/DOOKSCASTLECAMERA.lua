-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DOOKSCASTLECAMERA.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 1, path = "CutScene.inc" }

script.labels["Main"] = function(ctx)
    -- DOOKSCASTLECAMERA.scr:4
    do return ctx:exit(1) end -- DOOKSCASTLECAMERA.scr:6
    ctx:getParam(0, "sLocationName") -- DOOKSCASTLECAMERA.scr:7
    ctx:getParam(1, "sTargetName") -- DOOKSCASTLECAMERA.scr:8
    ctx:getParam(2, "sNotifyName") -- DOOKSCASTLECAMERA.scr:9
    ctx:getParam(3, "LISTFIRST") -- DOOKSCASTLECAMERA.scr:10
    ctx:getParam(4, "LISTLAST") -- DOOKSCASTLECAMERA.scr:11
    -- OnPostStartWorld InitDooksCastleCamera
    ctx:wait(0, 5, "InitDooksCastleCamera") -- DOOKSCASTLECAMERA.scr:14
    do return ctx:exit(1) end -- DOOKSCASTLECAMERA.scr:16
end

script.labels["InitDooksCastleCamera"] = function(ctx)
    -- DOOKSCASTLECAMERA.scr:19
    ctx:addTrigger("Next", "StartNextScene") -- DOOKSCASTLECAMERA.scr:21
    ctx:addTrigger("Zoom", "ZoomToTarget") -- DOOKSCASTLECAMERA.scr:22
    ctx:state().cutscene_nRate = 64 -- DOOKSCASTLECAMERA.scr:24
    ctx:state().cutscene_nGap = 96 -- DOOKSCASTLECAMERA.scr:25
    mm9.gosub(script, ctx, "InitCutScene") -- DOOKSCASTLECAMERA.scr:27
    do return ctx:exit(1) end -- DOOKSCASTLECAMERA.scr:29
end

return script
