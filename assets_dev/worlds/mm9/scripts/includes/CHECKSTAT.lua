-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CHECKSTAT.inc"
script.includes = {}
script.labels = {}


-- CheckStat.inc
-- by SJR
-- Purpose:basic stat comparisons
-- Must init 'stat_hPlayer' yourself
-- Must init STATINDEX, STATCOMPARE
script.labels["CheckStat"] = function(ctx)
    -- CHECKSTAT.inc:18
    ctx:getAttribute("STATINDEX", "stat_nValue") -- CHECKSTAT.inc:20
    if ctx:condition("stat_nValue > STATCOMPARE") then -- CHECKSTAT.inc:22
        ctx:state().STATRESULT = 1 -- CHECKSTAT.inc:23
        do return ctx:exit("") end -- CHECKSTAT.inc:24
    end -- CHECKSTAT.inc:25
    if ctx:condition("stat_nValue == STATCOMPARE") then -- CHECKSTAT.inc:26
        ctx:state().STATRESULT = 0 -- CHECKSTAT.inc:27
        do return ctx:exit("") end -- CHECKSTAT.inc:28
    end -- CHECKSTAT.inc:29
    if ctx:condition("stat_nValue < STATCOMPARE") then -- CHECKSTAT.inc:30
        ctx:state().STATRESULT = -1 -- CHECKSTAT.inc:31
        do return ctx:exit("") end -- CHECKSTAT.inc:32
    end -- CHECKSTAT.inc:33
    do return ctx:exit(1) end -- CHECKSTAT.inc:35
end

return script
