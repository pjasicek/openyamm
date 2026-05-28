-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WORLDTEST.scr"
script.includes = {}
script.labels = {}


script.labels["Callback"] = function(ctx)
    -- WORLDTEST.scr:9
    ctx:command("wait", "0, 2, Tick") -- WORLDTEST.scr:10
    do return ctx:exit("") end -- WORLDTEST.scr:11
end

script.labels["Tick"] = function(ctx)
    -- WORLDTEST.scr:13
    ctx:command("getpos", "g_hMyObject,g_posX,g_posY,g_posZ") -- WORLDTEST.scr:15
    ctx:command("add", "g_posZ, g_temp") -- WORLDTEST.scr:17
    ctx:command("mul", "g_temp, -1") -- WORLDTEST.scr:19
    ctx:command("movetopos", "g_posX, g_posY, g_posZ, 100, Callback") -- WORLDTEST.scr:21
    do return ctx:exit("") end -- WORLDTEST.scr:24
end

script.labels["Main"] = function(ctx)
    -- WORLDTEST.scr:27
    ctx:command("getmyhandle", "g_hMyObject") -- WORLDTEST.scr:28
    mm9.gosub(script, ctx, "Tick") -- WORLDTEST.scr:30
    do return ctx:exit("") end -- WORLDTEST.scr:32
end

return script
