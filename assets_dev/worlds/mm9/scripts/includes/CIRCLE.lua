-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CIRCLE.inc"
script.includes = {}
script.labels = {}


-- Circle.inc
-- by SJR
-- 12-11-01
-- Purpose:generate circle coordinates
-- outputs: (u,v) = circle(x,y)
-- inputs
script.labels["InitCircle"] = function(ctx)
    -- CIRCLE.inc:21
    -- radianize angles, cap direction
    ctx:state().circle_SumdA = 0 -- CIRCLE.inc:24
    -- radianize it
    ctx:set("circle_dA", "circle_dA / 180 * PI") -- CIRCLE.inc:26
    if ctx:condition("circle_nDir>=0") then -- CIRCLE.inc:28
        ctx:state().circle_nDir = 1 -- CIRCLE.inc:29
    else -- CIRCLE.inc:30
        ctx:state().circle_nDir = -1 -- CIRCLE.inc:31
    end -- CIRCLE.inc:32
    do return ctx:exit(1) end -- CIRCLE.inc:34
end

script.labels["CircleIncrement"] = function(ctx)
    -- CIRCLE.inc:37
    -- rotates (u,v) by (+\-)circle_dA
    ctx:set("circle_SumdA", "circle_dA * circle_nDir + circle_SumdA") -- CIRCLE.inc:40
    ctx:cos("circle_SumdA", "circle_u") -- CIRCLE.inc:42
    ctx:sin("circle_SumdA", "circle_v") -- CIRCLE.inc:43
    ctx:set("circle_u", "circle_nRadius * circle_u") -- CIRCLE.inc:45
    ctx:set("circle_v", "circle_nRadius * circle_v") -- CIRCLE.inc:46
    do return ctx:exit(1) end -- CIRCLE.inc:48
end

return script
