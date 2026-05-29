-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WORLDTEST.scr"
script.includes = {}
script.labels = {}


script.labels["Callback"] = function(ctx)
    -- WORLDTEST.scr:9
    ctx:wait(0, 2, "Tick") -- WORLDTEST.scr:10
    do return ctx:exit("") end -- WORLDTEST.scr:11
end

script.labels["Tick"] = function(ctx)
    -- WORLDTEST.scr:13
    ctx:state().g_posX, ctx:state().g_posY, ctx:state().g_posZ = ctx:self():pos() -- WORLDTEST.scr:15
    ctx:add("g_posZ", "g_temp") -- WORLDTEST.scr:17
    ctx:state().g_temp = (tonumber(ctx:state().g_temp) or 0) * -1 -- WORLDTEST.scr:19
    ctx:self():moveToPos("g_posX", "g_posY", "g_posZ", 100, "Callback") -- WORLDTEST.scr:21
    do return ctx:exit("") end -- WORLDTEST.scr:24
end

script.labels["Main"] = function(ctx)
    -- WORLDTEST.scr:27
    mm9.gosub(script, ctx, "Tick") -- WORLDTEST.scr:30
    do return ctx:exit("") end -- WORLDTEST.scr:32
end

return script
