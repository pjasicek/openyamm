-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GENIECRYSTAL.scr"
script.includes = {}
script.labels = {}


-- BaseGlobals.inc
-- by SJR
-- 11-12-01
-- Purpose:be a genie crystal
-- ScriptParams:
-- p0 = name of genie
script.labels["Main"] = function(ctx)
    -- GENIECRYSTAL.scr:15
    ctx:getParam(0, "sGenieName") -- GENIECRYSTAL.scr:17
    ctx:addTrigger("use", "CallGenie") -- GENIECRYSTAL.scr:19
    do return ctx:exit(1) end -- GENIECRYSTAL.scr:21
end

script.labels["CallGenie"] = function(ctx)
    -- GENIECRYSTAL.scr:24
    ctx:removeTrigger("use") -- GENIECRYSTAL.scr:26
    ctx:state().hGenie = ctx:objectOrNil("sGenieName") -- GENIECRYSTAL.scr:28
    if ctx:condition("hGenie!=0") then -- GENIECRYSTAL.scr:30
        ctx:trigger("hGenie", "appear") -- GENIECRYSTAL.scr:31
    end -- GENIECRYSTAL.scr:32
    do return ctx:exit(1) end -- GENIECRYSTAL.scr:34
end

return script
