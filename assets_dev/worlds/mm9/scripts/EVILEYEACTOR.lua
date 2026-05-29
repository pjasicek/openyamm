-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "EVILEYEACTOR.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 1, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 2, path = "CutSceneActor.inc" }
script.includes[#script.includes + 1] = { line = 3, path = "LichLabScenes.inc" }
script.includes[#script.includes + 1] = { line = 4, path = "TheThing.inc" }
script.includes[#script.includes + 1] = { line = 5, path = "Flags.inc" }

script.labels["Main"] = function(ctx)
    -- EVILEYEACTOR.scr:13
    ctx:getParam(0, "sDoorName") -- EVILEYEACTOR.scr:15
    ctx:wait(0, 3, "Init") -- EVILEYEACTOR.scr:17
    do return ctx:exit("TRUE") end -- EVILEYEACTOR.scr:19
end

script.labels["Init"] = function(ctx)
    -- EVILEYEACTOR.scr:22
    ctx:self():setStat("Gravity", 0) -- EVILEYEACTOR.scr:24
    mm9.gosub(script, ctx, "InitLichLabScenes") -- EVILEYEACTOR.scr:25
    mm9.gosub(script, ctx, "InitTheThing") -- EVILEYEACTOR.scr:26
    ctx:state().hLich = ctx:objectOrNil("PowerLich0") -- EVILEYEACTOR.scr:27
    ctx:self():faceObject(ctx:object("hLich"), 360, "DoNothing") -- EVILEYEACTOR.scr:29
    do return ctx:exit("TRUE") end -- EVILEYEACTOR.scr:31
end

script.labels["OnScene2"] = function(ctx)
    -- EVILEYEACTOR.scr:34
    ctx:cprint("OnScene2") -- EVILEYEACTOR.scr:36
    ctx:onEvent("OnObstacle", "OnScene2") -- EVILEYEACTOR.scr:37
    -- GetRandomInt
    do return ctx:exit("TRUE") end -- EVILEYEACTOR.scr:40
end

script.labels["OnScene3"] = function(ctx)
    -- EVILEYEACTOR.scr:43
    ctx:cprint("OnScene3") -- EVILEYEACTOR.scr:45
    ctx:self():stop() -- EVILEYEACTOR.scr:46
    ctx:onEvent("OnObstacle", "DoNothing") -- EVILEYEACTOR.scr:47
    ctx:self():setFlag("FLAG_GOTHRUWORLD", true) -- EVILEYEACTOR.scr:48
    ctx:self():playAnimation("rattack1", "EndScene") -- EVILEYEACTOR.scr:49
    do return ctx:exit("TRUE") end -- EVILEYEACTOR.scr:51
end

script.labels["OnScene4"] = function(ctx)
    -- EVILEYEACTOR.scr:54
    ctx:state().hDoor = ctx:objectOrNil("sDoorName") -- EVILEYEACTOR.scr:56
    ctx:self():playAnimation("hattack1", "DoNothing") -- EVILEYEACTOR.scr:57
    ctx:trigger("hDoor", "destroy") -- EVILEYEACTOR.scr:58
    ctx:self():runTo(ctx:object("hLich"), 25, "Finish") -- EVILEYEACTOR.scr:59
    do return ctx:exit("TRUE") end -- EVILEYEACTOR.scr:61
end

script.labels["Finish"] = function(ctx)
    -- EVILEYEACTOR.scr:64
    ctx:self():stop() -- EVILEYEACTOR.scr:66
    ctx:self():playAnimation("hattack1", "DoNothing") -- EVILEYEACTOR.scr:67
    ctx:trigger("hLich", "finish") -- EVILEYEACTOR.scr:68
    ctx:wait(0, 3, "EndScene") -- EVILEYEACTOR.scr:69
    do return ctx:exit("TRUE") end -- EVILEYEACTOR.scr:71
end

script.labels["OnScene5"] = function(ctx)
    -- EVILEYEACTOR.scr:74
    ctx:state().hLich = ctx:objectOrNil("MarkerTarget1") -- EVILEYEACTOR.scr:76
    ctx:self():runTo(ctx:object("hLich"), 100, "EndCinema") -- EVILEYEACTOR.scr:77
    do return ctx:exit("TRUE") end -- EVILEYEACTOR.scr:79
end

script.labels["EndCinema"] = function(ctx)
    -- EVILEYEACTOR.scr:82
    ctx:self():stop() -- EVILEYEACTOR.scr:84
    mm9.gosub(script, ctx, "EndScene") -- EVILEYEACTOR.scr:85
    do return ctx:exit("TRUE") end -- EVILEYEACTOR.scr:87
end

return script
