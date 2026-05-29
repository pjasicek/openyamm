-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "PIGCAM.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 1, path = "BaseGlobals.inc" }

script.labels["Main"] = function(ctx)
    -- PIGCAM.scr:17
    ctx:getParam(0, "sPigName") -- PIGCAM.scr:18
    ctx:wait(0, 3, "InitPigCam") -- PIGCAM.scr:19
    do return ctx:exit("TRUE") end -- PIGCAM.scr:21
end

script.labels["InitPigCam"] = function(ctx)
    -- PIGCAM.scr:23
    ctx:addTrigger("start", "OnStart") -- PIGCAM.scr:24
    do return ctx:exit("TRUE") end -- PIGCAM.scr:26
end

script.labels["OnStart"] = function(ctx)
    -- PIGCAM.scr:28
    ctx:state().hPig = ctx:objectOrNil("sPigName") -- PIGCAM.scr:30
    ctx:trigger("hMe", "on") -- PIGCAM.scr:33
    mm9.gosub(script, ctx, "RaceLoop") -- PIGCAM.scr:34
    do return ctx:exit("TRUE") end -- PIGCAM.scr:36
end

script.labels["RaceLoop"] = function(ctx)
    -- PIGCAM.scr:38
    ctx:state().x, ctx:state().y, ctx:state().z = ctx:object("hPig"):pos() -- PIGCAM.scr:39
    ctx:state().dx, ctx:state().dy, ctx:state().dz = ctx:player():rotation() -- PIGCAM.scr:40
    ctx:set("dy", "dy - .35") -- PIGCAM.scr:41
    ctx:self():faceDir("dx", "dy", "dz", 0, "DoNothing") -- PIGCAM.scr:42
    ctx:set("y", "y + 25") -- PIGCAM.scr:43
    ctx:self():moveToPos("x", "y", "z", 0, "DoNothing") -- PIGCAM.scr:44
    ctx:wait(0, .05, "RaceLoop") -- PIGCAM.scr:45
    do return ctx:exit("TRUE") end -- PIGCAM.scr:47
end

return script
