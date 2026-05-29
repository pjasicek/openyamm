-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CHESSCAMERA.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 5, path = "BaseGlobals.inc" }

-- ChessCamera.scr
-- by SJR
script.labels["Main"] = function(ctx)
    -- CHESSCAMERA.scr:21
    ctx:addTrigger("Look", "ViewChessPiece") -- CHESSCAMERA.scr:23
    ctx:addTrigger("TurnOff", "CameraOff") -- CHESSCAMERA.scr:24
    ctx:state().sMyName = ctx:self():name() -- CHESSCAMERA.scr:27
    ctx:setConsoleStrVar("CHESS_CAM", "sMyName") -- CHESSCAMERA.scr:28
    do return ctx:exit("TRUE") end -- CHESSCAMERA.scr:30
end

script.labels["GetPlayerWet"] = function(ctx)
    -- CHESSCAMERA.scr:33
    -- jsl-->Added 2/16/02
    -- The SetPos command will now set the position of the player...
    -- This makes sure the player falls into the water.....
    ctx:state().x, ctx:state().y, ctx:state().z = ctx:player():pos() -- CHESSCAMERA.scr:41
    ctx:set("y", "y - 160") -- CHESSCAMERA.scr:43
    ctx:player():setPos("x", "y", "z") -- CHESSCAMERA.scr:45
    do return ctx:exit("") end -- CHESSCAMERA.scr:46
end

script.labels["ViewChessPiece"] = function(ctx)
    -- CHESSCAMERA.scr:50
    -- pans from hPanNode0 to hPanNode1
    ctx:getParam(0, "hPan") -- CHESSCAMERA.scr:53
    mm9.gosub(script, ctx, "AlignCamera") -- CHESSCAMERA.scr:55
    mm9.gosub(script, ctx, "CameraOn") -- CHESSCAMERA.scr:56
    mm9.gosub(script, ctx, "GetPlayerWet") -- CHESSCAMERA.scr:57
    ctx:self():faceObject(ctx:object("hPan"), 360, "DoNothing") -- CHESSCAMERA.scr:59
    do return ctx:exit("TRUE") end -- CHESSCAMERA.scr:61
end

script.labels["AlignCamera"] = function(ctx)
    -- CHESSCAMERA.scr:64
    -- sets pos and dir to player's
    if ctx:condition("hPlayer==0") then -- CHESSCAMERA.scr:67
    end -- CHESSCAMERA.scr:69
    ctx:state().x, ctx:state().y, ctx:state().z = ctx:player():pos() -- CHESSCAMERA.scr:70
    ctx:state().dx, ctx:state().dy, ctx:state().dz = ctx:player():rotation() -- CHESSCAMERA.scr:71
    ctx:state().dx, ctx:state().dy, ctx:state().dz = ctx:vecNorm("dx", "dy", "dz") -- CHESSCAMERA.scr:72
    ctx:set("y", "y + 38") -- CHESSCAMERA.scr:73
    ctx:self():setPos("x", "y", "z") -- CHESSCAMERA.scr:74
    ctx:self():faceDir("dx", "dy", "dz", 0, "DoNothing") -- CHESSCAMERA.scr:76
    do return ctx:exit("TRUE") end -- CHESSCAMERA.scr:78
end

script.labels["CameraOn"] = function(ctx)
    -- CHESSCAMERA.scr:81
    ctx:trigger("hMe", "on") -- CHESSCAMERA.scr:83
    ctx:letterBox("TRUE") -- CHESSCAMERA.scr:84
    do return ctx:exit("TRUE") end -- CHESSCAMERA.scr:86
end

script.labels["CameraOff"] = function(ctx)
    -- CHESSCAMERA.scr:89
    ctx:state().hPan = nil -- CHESSCAMERA.scr:91
    ctx:self():setTarget(nil) -- CHESSCAMERA.scr:92
    ctx:trigger("hMe", "off") -- CHESSCAMERA.scr:93
    ctx:letterBox("FALSE") -- CHESSCAMERA.scr:94
    do return ctx:exit("TRUE") end -- CHESSCAMERA.scr:96
end

return script
