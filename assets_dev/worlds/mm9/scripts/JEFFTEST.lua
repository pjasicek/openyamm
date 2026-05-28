-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "JEFFTEST.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 2, path = "globals.inc" }

script.labels["DoRotate"] = function(ctx)
    -- JEFFTEST.scr:10
    ctx:command("rotate", "axis_x,axis_y,axis_z,180,rate,DoRotate") -- JEFFTEST.scr:11
    do return ctx:exit("") end -- JEFFTEST.scr:12
end

script.labels["Rotate"] = function(ctx)
    -- JEFFTEST.scr:14
    ctx:getParam(0, "axis_x") -- JEFFTEST.scr:15
    ctx:getParam(1, "axis_y") -- JEFFTEST.scr:16
    ctx:getParam(2, "axis_z") -- JEFFTEST.scr:17
    ctx:getParam(3, "rate") -- JEFFTEST.scr:18
    mm9.gosub(script, ctx, "DoRotate") -- JEFFTEST.scr:19
    do return ctx:exit("") end -- JEFFTEST.scr:20
end

script.labels["Main"] = function(ctx)
    -- JEFFTEST.scr:23
    ctx:addTrigger("Rotate", "Rotate") -- JEFFTEST.scr:26
    ctx:getParam(0, "axis_x") -- JEFFTEST.scr:28
    ctx:getParam(1, "axis_y") -- JEFFTEST.scr:29
    ctx:getParam(2, "axis_z") -- JEFFTEST.scr:30
    ctx:getParam(3, "rate") -- JEFFTEST.scr:31
    mm9.gosub(script, ctx, "DoRotate") -- JEFFTEST.scr:33
    do return ctx:exit("") end -- JEFFTEST.scr:35
end

return script
