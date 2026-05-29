-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "AK_GUARDESCAPE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 12, path = "ListTraverse.inc" }

-- AK_GuardEscape.scr
-- kd
-- 11-1
-- Parameters
-- p0 - Marker Root name  (ie for Markers Mrk0, Mrk1, Mrk2  "Mrk" is the root name)
-- p1 - index of first marker
-- p2 - index of last marker
script.labels["OnTraverseDone"] = function(ctx)
    -- AK_GUARDESCAPE.scr:15
    if ctx:condition("LISTINDEX==LISTLAST") then -- AK_GUARDESCAPE.scr:17
        ctx:self():stop() -- AK_GUARDESCAPE.scr:18
        ctx:state().LISTOBJECT = ctx:self() -- AK_GUARDESCAPE.scr:19
        ctx:object("LISTOBJECT"):remove() -- AK_GUARDESCAPE.scr:20
    end -- AK_GUARDESCAPE.scr:21
    do return ctx:exit(1) end -- AK_GUARDESCAPE.scr:23
end

script.labels["Main"] = function(ctx)
    -- AK_GUARDESCAPE.scr:26
    ctx:getParam(0, "LISTNAME") -- AK_GUARDESCAPE.scr:28
    ctx:getParam(1, "LISTFIRST") -- AK_GUARDESCAPE.scr:29
    ctx:getParam(2, "LISTLAST") -- AK_GUARDESCAPE.scr:30
    mm9.gosub(script, ctx, "SetTraverseRun") -- AK_GUARDESCAPE.scr:32
    mm9.gosub(script, ctx, "SetTraverseOnce") -- AK_GUARDESCAPE.scr:33
    ctx:onEvent("OnDamage", "TraverseBegin") -- AK_GUARDESCAPE.scr:35
    ctx:onEvent("OnStuck", "TraverseResume") -- AK_GUARDESCAPE.scr:36
    ctx:addTrigger("Go", "RunAway") -- AK_GUARDESCAPE.scr:37
    do return ctx:exit(1) end -- AK_GUARDESCAPE.scr:39
end

script.labels["RunAway"] = function(ctx)
    -- AK_GUARDESCAPE.scr:42
    -- display help text
    ctx:rolloverText(150, 1, 5000, 4000) -- AK_GUARDESCAPE.scr:45
    do return ctx:exit(1) end -- AK_GUARDESCAPE.scr:47
end

return script
