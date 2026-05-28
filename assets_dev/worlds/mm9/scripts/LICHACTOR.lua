-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LICHACTOR.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 1, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 2, path = "CutSceneActor.inc" }
script.includes[#script.includes + 1] = { line = 3, path = "LichLabScenes.inc" }

script.labels["Main"] = function(ctx)
    -- LICHACTOR.scr:13
    ctx:command("wait", "0, 3, Init") -- LICHACTOR.scr:15
    do return ctx:exit(1) end -- LICHACTOR.scr:17
end

script.labels["Init"] = function(ctx)
    -- LICHACTOR.scr:20
    mm9.gosub(script, ctx, "InitLichLabScenes") -- LICHACTOR.scr:22
    ctx:command("getobjecthandle", "MarkerTarget2, h") -- LICHACTOR.scr:23
    ctx:command("faceobject", "h, 180, DoNothing") -- LICHACTOR.scr:24
    ctx:addTrigger("finish", "OnTurn") -- LICHACTOR.scr:25
    do return ctx:exit(1) end -- LICHACTOR.scr:27
end

script.labels["OnScene0"] = function(ctx)
    -- LICHACTOR.scr:30
    mm9.gosub(script, ctx, "OnScene2") -- LICHACTOR.scr:32
    do return ctx:exit(1) end -- LICHACTOR.scr:33
end

script.labels["OnScene2"] = function(ctx)
    -- LICHACTOR.scr:36
    ctx:command("stop", "") -- LICHACTOR.scr:38
    ctx:command("ncounter", "= nCounter + 1") -- LICHACTOR.scr:39
    if ctx:condition("nCounter>5") then -- LICHACTOR.scr:40
        ctx:command("ncounter", "= 0") -- LICHACTOR.scr:41
        mm9.gosub(script, ctx, "EndScene") -- LICHACTOR.scr:42
    else -- LICHACTOR.scr:43
        ctx:command("playsound", "sounds\\magic\\cast02.wav, DoNothing, 1, 500, 0, 100") -- LICHACTOR.scr:44
        ctx:command("playanim", "hattack1, Pause") -- LICHACTOR.scr:45
    end -- LICHACTOR.scr:46
    do return ctx:exit(1) end -- LICHACTOR.scr:48
end

script.labels["Pause"] = function(ctx)
    -- LICHACTOR.scr:51
    ctx:command("message_index", "= MESSAGE_INDEX + 1") -- LICHACTOR.scr:53
    ctx:command("wait", "0, 3, OnScene2") -- LICHACTOR.scr:54
    do return ctx:exit(1) end -- LICHACTOR.scr:56
end

script.labels["OnTurn"] = function(ctx)
    -- LICHACTOR.scr:59
    ctx:command("playanim", "wince1, RunAway") -- LICHACTOR.scr:61
    do return ctx:exit(1) end -- LICHACTOR.scr:63
end

script.labels["RunAway"] = function(ctx)
    -- LICHACTOR.scr:66
    ctx:command("getmyhandle", "h") -- LICHACTOR.scr:68
    ctx:command("getforwarddir", "h, x,y,z") -- LICHACTOR.scr:69
    ctx:command("vecscale", "x,y,z, -1") -- LICHACTOR.scr:70
    ctx:command("facedir", "x,y,z, 720, DoNothing") -- LICHACTOR.scr:71
    ctx:command("die", "") -- LICHACTOR.scr:72
    do return ctx:exit(1) end -- LICHACTOR.scr:74
end

return script
