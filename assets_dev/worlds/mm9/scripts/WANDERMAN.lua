-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WANDERMAN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "Base.Inc" }

-- WanderMan.scr
-- Test script...
script.labels["OnUse"] = function(ctx)
    -- WANDERMAN.scr:10
    mm9.gosub(script, ctx, "BaseWanderGo") -- WANDERMAN.scr:12
    do return ctx:exit("") end -- WANDERMAN.scr:13
end

script.labels["Main"] = function(ctx)
    -- WANDERMAN.scr:17
    -- gosub InitBase
    mm9.gosub(script, ctx, "BaseWanderInit") -- WANDERMAN.scr:20
    ctx:addTrigger("Use", "OnUse") -- WANDERMAN.scr:22
    -- TraceON
    do return ctx:exit("") end -- WANDERMAN.scr:26
end

return script
