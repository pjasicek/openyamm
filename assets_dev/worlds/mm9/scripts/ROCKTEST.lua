-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ROCKTEST.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- rockttest.scr
-- Destructable Object Script Test
script.labels["HandleTouch"] = function(ctx)
    -- ROCKTEST.scr:12
    ctx:command("setmodelfilenames", "models\\\\props\\\\barreldestroy.abc, skins\\\\props\\\\barreldestroy.dtx") -- ROCKTEST.scr:15
    ctx:command("loopanim", "Destroy, 3") -- ROCKTEST.scr:16
    do return ctx:exit("") end -- ROCKTEST.scr:18
end

script.labels["Main"] = function(ctx)
    -- ROCKTEST.scr:21
    ctx:command("getmyhandle", "g_hMyObject") -- ROCKTEST.scr:24
    ctx:command("setmodelfilenames", "models\\\\props\\\\barrel.abc, \"\"") -- ROCKTEST.scr:26
    ctx:command("ondeath", "HandleTouch") -- ROCKTEST.scr:28
    -- OnTouchNotify HandleTouch
    do return ctx:exit("") end -- ROCKTEST.scr:32
end

return script
