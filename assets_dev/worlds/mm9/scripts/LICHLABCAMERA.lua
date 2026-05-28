-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LICHLABCAMERA.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 1, path = "CutScene.inc" }
script.includes[#script.includes + 1] = { line = 2, path = "LichSceneTransitions.inc" }

-- #include spellnames.inc
script.labels["Main"] = function(ctx)
    -- LICHLABCAMERA.scr:6
    ctx:getParam(0, "sLocationName") -- LICHLABCAMERA.scr:8
    ctx:getParam(1, "sTargetName") -- LICHLABCAMERA.scr:9
    ctx:getParam(2, "sNotifyName") -- LICHLABCAMERA.scr:10
    ctx:getParam(3, "LISTFIRST") -- LICHLABCAMERA.scr:11
    ctx:getParam(4, "LISTLAST") -- LICHLABCAMERA.scr:12
    ctx:addTrigger("next", "SoftExit") -- LICHLABCAMERA.scr:14
    ctx:addTrigger("zoom", "ZoomToTarget") -- LICHLABCAMERA.scr:15
    mm9.gosub(script, ctx, "InitCutScene") -- LICHLABCAMERA.scr:17
    ctx:command("oncachefiles", "CacheFiles") -- LICHLABCAMERA.scr:19
    do return ctx:exit("TRUE") end -- LICHLABCAMERA.scr:21
end

script.labels["CacheFiles"] = function(ctx)
    -- LICHLABCAMERA.scr:24
    -- cache all for scene
    ctx:command("cacheclientfx", "SPELL_DARKGRASP") -- LICHLABCAMERA.scr:27
    ctx:command("cacheclientfx", "SPELL_PARALYZE") -- LICHLABCAMERA.scr:28
    ctx:command("cacheclientfx", "SPELL_ELEMBLAST") -- LICHLABCAMERA.scr:29
    ctx:command("cacheclientfx", "SPELL_SPARKLIES") -- LICHLABCAMERA.scr:30
    ctx:command("cacheclientfx", "SPELL_TRANSFUSION") -- LICHLABCAMERA.scr:31
    ctx:command("cacheclientfx", "SPELL_BLUEFIRE") -- LICHLABCAMERA.scr:32
    do return ctx:exit("TRUE") end -- LICHLABCAMERA.scr:34
end

script.labels["SoftExit"] = function(ctx)
    -- LICHLABCAMERA.scr:37
    ctx:command("removetrigger", "next") -- LICHLABCAMERA.scr:39
    ctx:addTrigger("next", "StartNextScene") -- LICHLABCAMERA.scr:40
    mm9.gosub(script, ctx, "RemoveCreatures") -- LICHLABCAMERA.scr:42
    ctx:command("screenfadeout", "0") -- LICHLABCAMERA.scr:44
    ctx:command("wait", "0, 2, SoftEntrance") -- LICHLABCAMERA.scr:46
    do return ctx:exit("TRUE") end -- LICHLABCAMERA.scr:48
end

script.labels["SoftEntrance"] = function(ctx)
    -- LICHLABCAMERA.scr:51
    mm9.gosub(script, ctx, "StartNextScene") -- LICHLABCAMERA.scr:53
    ctx:command("screenfadein", "2") -- LICHLABCAMERA.scr:54
    do return ctx:exit("TRUE") end -- LICHLABCAMERA.scr:56
end

script.labels["OnSceneDone"] = function(ctx)
    -- LICHLABCAMERA.scr:59
    ctx:command("screenfadeout", "0") -- LICHLABCAMERA.scr:61
    ctx:command("screenfadein", "4") -- LICHLABCAMERA.scr:62
    mm9.gosub(script, ctx, "RemoveActors") -- LICHLABCAMERA.scr:64
    mm9.gosub(script, ctx, "ReplaceCreatures") -- LICHLABCAMERA.scr:65
    do return ctx:exit("TRUE") end -- LICHLABCAMERA.scr:67
end

script.labels["OnSceneStart"] = function(ctx)
    -- LICHLABCAMERA.scr:70
    mm9.gosub(script, ctx, "RemoveCreatures") -- LICHLABCAMERA.scr:72
    do return ctx:exit("TRUE") end -- LICHLABCAMERA.scr:74
end

return script
