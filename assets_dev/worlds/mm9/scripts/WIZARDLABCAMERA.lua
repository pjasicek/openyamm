-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WIZARDLABCAMERA.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 1, path = "CutScene.inc" }

script.labels["Main"] = function(ctx)
    -- WIZARDLABCAMERA.scr:4
    ctx:getParam(0, "sLocationName") -- WIZARDLABCAMERA.scr:6
    ctx:getParam(1, "sTargetName") -- WIZARDLABCAMERA.scr:7
    ctx:getParam(2, "sNotifyName") -- WIZARDLABCAMERA.scr:8
    ctx:getParam(3, "LISTFIRST") -- WIZARDLABCAMERA.scr:9
    ctx:getParam(4, "LISTLAST") -- WIZARDLABCAMERA.scr:10
    mm9.gosub(script, ctx, "InitWizardLabCamera") -- WIZARDLABCAMERA.scr:12
    do return ctx:exit(1) end -- WIZARDLABCAMERA.scr:14
end

script.labels["InitWizardLabCamera"] = function(ctx)
    -- WIZARDLABCAMERA.scr:17
    ctx:addTrigger("next", "SoftExit") -- WIZARDLABCAMERA.scr:19
    mm9.gosub(script, ctx, "InitCutScene") -- WIZARDLABCAMERA.scr:21
    do return ctx:exit(1) end -- WIZARDLABCAMERA.scr:23
end

script.labels["SoftExit"] = function(ctx)
    -- WIZARDLABCAMERA.scr:26
    ctx:command("removetrigger", "next") -- WIZARDLABCAMERA.scr:28
    ctx:addTrigger("next", "StartNextScene") -- WIZARDLABCAMERA.scr:29
    ctx:command("screenfadeout", "0") -- WIZARDLABCAMERA.scr:31
    ctx:command("wait", "0, 2, SoftEntrance") -- WIZARDLABCAMERA.scr:33
    do return ctx:exit("TRUE") end -- WIZARDLABCAMERA.scr:35
end

script.labels["SoftEntrance"] = function(ctx)
    -- WIZARDLABCAMERA.scr:38
    mm9.gosub(script, ctx, "StartNextScene") -- WIZARDLABCAMERA.scr:40
    ctx:command("screenfadein", "2") -- WIZARDLABCAMERA.scr:42
    do return ctx:exit("TRUE") end -- WIZARDLABCAMERA.scr:44
end

return script
