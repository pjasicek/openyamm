-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CHECKSTAT.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 18, path = "CheckStat.inc" }

-- CheckStat.inc
-- by SJR
-- Purpose:basic stat comparisons
-- ScriptParams:
-- p0 = type of stat (ie strength)
-- 0=might, 1=magic, 2=endurance
-- 3=accuracy, 4=speed, 5=luck
-- p1 = comparison type (-1,0,1) for (<,==,>)
-- p2 = number to compare with
-- p3 = object to trigger OnSuccess
-- p4 = object to trigger OnFailure
-- Trigger this thing when you want to check a stat
-- and it will trigger either p3 or p4 when finished.
script.labels["Main"] = function(ctx)
    -- CHECKSTAT.scr:27
    ctx:getParam(0, "STATINDEX") -- CHECKSTAT.scr:29
    ctx:getParam(1, "opComparison") -- CHECKSTAT.scr:30
    ctx:getParam(2, "STATCOMPARE") -- CHECKSTAT.scr:31
    ctx:getParam(3, "sSuccessName") -- CHECKSTAT.scr:33
    ctx:getParam(4, "sFailureName") -- CHECKSTAT.scr:34
    -- OnPostStartWorld InitCheckStat
    ctx:wait(0, 5, "InitCheckStat") -- CHECKSTAT.scr:37
    do return ctx:exit(1) end -- CHECKSTAT.scr:39
end

script.labels["InitCheckStat"] = function(ctx)
    -- CHECKSTAT.scr:42
    ctx:addTrigger("trigger", "CheckThisStat") -- CHECKSTAT.scr:44
    do return ctx:exit(1) end -- CHECKSTAT.scr:46
end

script.labels["CheckThisStat"] = function(ctx)
    -- CHECKSTAT.scr:49
    mm9.gosub(script, ctx, "CheckStat") -- CHECKSTAT.scr:51
    if ctx:condition("STATRESULT == opComparison") then -- CHECKSTAT.scr:53
        ctx:state().hTrigger = ctx:objectOrNil("sSuccessName") -- CHECKSTAT.scr:54
    else -- CHECKSTAT.scr:55
        ctx:state().hTrigger = ctx:objectOrNil("sFailureName") -- CHECKSTAT.scr:56
    end -- CHECKSTAT.scr:57
    ctx:trigger("hTrigger", "trigger") -- CHECKSTAT.scr:59
    do return ctx:exit(1) end -- CHECKSTAT.scr:61
end

return script
