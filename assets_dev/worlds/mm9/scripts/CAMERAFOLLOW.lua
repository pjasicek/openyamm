-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CAMERAFOLLOW.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 5, path = "aiglobals.inc" }

-- CameraFollow.scr
-- Jeff Leggett
-- Test...
script.labels["FollowTick"] = function(ctx)
    -- CAMERAFOLLOW.scr:7
    ctx:command("getvelocity", "g_hObject, g_posX, g_posY, g_posZ") -- CAMERAFOLLOW.scr:8
    ctx:command("setvelocity", "g_hMyObject, g_posX, g_posY, g_posZ") -- CAMERAFOLLOW.scr:9
    ctx:command("wait", "0,0.01,FollowTick") -- CAMERAFOLLOW.scr:10
    do return ctx:exit("") end -- CAMERAFOLLOW.scr:11
end

script.labels["FollowStart"] = function(ctx)
    -- CAMERAFOLLOW.scr:13
    mm9.gosub(script, ctx, "FollowTick") -- CAMERAFOLLOW.scr:14
    do return ctx:exit("") end -- CAMERAFOLLOW.scr:15
end

script.labels["GoCinematic"] = function(ctx)
    -- CAMERAFOLLOW.scr:17
    -- LetterBox TRUE
    ctx:command("screenfadein", "1") -- CAMERAFOLLOW.scr:19
    do return ctx:exit("") end -- CAMERAFOLLOW.scr:20
end

script.labels["TurnOn"] = function(ctx)
    -- CAMERAFOLLOW.scr:22
    ctx:getParam(0, "g_hObject") -- CAMERAFOLLOW.scr:23
    ctx:command("target", "g_hObject") -- CAMERAFOLLOW.scr:25
    -- Trigger g_hMyObject,ON
    -- gosub FollowStart
    ctx:command("screenfadeout", "1") -- CAMERAFOLLOW.scr:30
    ctx:command("wait", "1,1,GoCinematic") -- CAMERAFOLLOW.scr:31
    do return ctx:exit("FALSE") end -- CAMERAFOLLOW.scr:33
end

script.labels["TurnOff"] = function(ctx)
    -- CAMERAFOLLOW.scr:35
    -- LetterBox FALSE
    do return ctx:exit("FALSE") end -- CAMERAFOLLOW.scr:37
end

script.labels["Main"] = function(ctx)
    -- CAMERAFOLLOW.scr:39
    ctx:command("getmyhandle", "g_hMyObject") -- CAMERAFOLLOW.scr:40
    ctx:addTrigger("On", "TurnOn") -- CAMERAFOLLOW.scr:42
    ctx:addTrigger("Off", "TurnOff") -- CAMERAFOLLOW.scr:43
    do return ctx:exit("") end -- CAMERAFOLLOW.scr:45
end

return script
