-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GIVESTAT.scr"
script.includes = {}
script.labels = {}


-- GiveStat.scr
-- by SJR
-- Purpose:gives a certain stat
-- a certain bonus
-- ScriptParams:
-- p0 = string name of stat (might,magic,endurance,
-- accuracy, speed, luck)
-- p1 = amount of increase
-- p2 = who it affects (0,1)->(current,party)
-- p3 = duration (in minutes, 0 means permanent)
script.labels["Main"] = function(ctx)
    -- GIVESTAT.scr:24
    ctx:getParam(0, "sStatName") -- GIVESTAT.scr:26
    ctx:getParam(1, "STAT_VALUE") -- GIVESTAT.scr:27
    ctx:getParam(2, "STAT_PARTY") -- GIVESTAT.scr:28
    ctx:getParam(3, "STAT_TIME") -- GIVESTAT.scr:29
    if ctx:condition("sStatName==\"Might\"") then -- GIVESTAT.scr:31
        ctx:state().STAT_TYPE = 0 -- GIVESTAT.scr:32
    else -- GIVESTAT.scr:33
        if ctx:condition("sStatName==\"Magic\"") then -- GIVESTAT.scr:34
            ctx:state().STAT_TYPE = 1 -- GIVESTAT.scr:35
        else -- GIVESTAT.scr:36
            if ctx:condition("sStatName==\"Endurance\"") then -- GIVESTAT.scr:37
                ctx:state().STAT_TYPE = 2 -- GIVESTAT.scr:38
            else -- GIVESTAT.scr:39
                if ctx:condition("sStatName==\"Accuracy\"") then -- GIVESTAT.scr:40
                    ctx:state().STAT_TYPE = 3 -- GIVESTAT.scr:41
                else -- GIVESTAT.scr:42
                    if ctx:condition("sStatName==\"Speed\"") then -- GIVESTAT.scr:43
                        ctx:state().STAT_TYPE = 4 -- GIVESTAT.scr:44
                    else -- GIVESTAT.scr:45
                        if ctx:condition("sStatName==\"Luck\"") then -- GIVESTAT.scr:46
                            ctx:state().STAT_TYPE = 5 -- GIVESTAT.scr:47
                        end -- GIVESTAT.scr:48
                    end -- GIVESTAT.scr:49
                end -- GIVESTAT.scr:50
            end -- GIVESTAT.scr:51
        end -- GIVESTAT.scr:52
    end -- GIVESTAT.scr:53
    -- 1 real minute = 10 game minutes = 600 game seconds
    ctx:set("STAT_TIME", "STAT_TIME * 600") -- GIVESTAT.scr:56
    ctx:addTrigger("give", "GiveStat") -- GIVESTAT.scr:58
    do return ctx:exit(1) end -- GIVESTAT.scr:60
end

script.labels["GiveStat"] = function(ctx)
    -- GIVESTAT.scr:63
    ctx:giveAttribute("STAT_TYPE", "STAT_VALUE", "STAT_PARTY", "STAT_TIME") -- GIVESTAT.scr:65
    do return ctx:exit(1) end -- GIVESTAT.scr:67
end

return script
