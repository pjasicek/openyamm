-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BASEGLOBALS.inc"
script.includes = {}
script.labels = {}


-- BaseGlobals.inc
-- by SJR
-- Purpose:cut down on
-- unneeded vars
-- and provide much needed
-- stop callback!
script.labels["DoNothing"] = function(ctx)
    -- BASEGLOBALS.inc:16
    do return ctx:exit("TRUE") end -- BASEGLOBALS.inc:18
end

script.labels["StopMoving"] = function(ctx)
    -- BASEGLOBALS.inc:21
    ctx:self():stop() -- BASEGLOBALS.inc:23
    do return ctx:exit("TRUE") end -- BASEGLOBALS.inc:24
end

return script
