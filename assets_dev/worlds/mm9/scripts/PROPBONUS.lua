-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "PROPBONUS.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 15, path = "BaseGlobals.inc" }

-- Prop[whatever].scr
-- by SJR
-- 12-20-01
-- Purpose:give bonuses out when the
-- player clicks on junk that
-- is strewn about.
-- ScriptParams:
-- p0 = type of bonus
-- (0,1,2,3,4)==(gold, health, exp, skill, attribute)
-- p1 = minimum value
-- p2 = maximum value
-- p3 = animation name (such as 'tumble' for trashpile.abc)
script.labels["Main"] = function(ctx)
    -- PROPBONUS.scr:26
    ctx:getParam(0, "nType") -- PROPBONUS.scr:28
    ctx:getParam(1, "BONUS_MIN") -- PROPBONUS.scr:29
    ctx:getParam(2, "BONUS_MAX") -- PROPBONUS.scr:30
    ctx:getParam(3, "sAnimName") -- PROPBONUS.scr:31
    -- default to gold
    if ctx:condition("nType<0") then -- PROPBONUS.scr:34
        ctx:command("ntype", "= 0") -- PROPBONUS.scr:35
    else -- PROPBONUS.scr:36
        if ctx:condition("nType>3") then -- PROPBONUS.scr:37
            ctx:command("ntype", "= 0") -- PROPBONUS.scr:38
        end -- PROPBONUS.scr:39
    end -- PROPBONUS.scr:40
    ctx:addTrigger("use", "GiveBonus") -- PROPBONUS.scr:42
    do return ctx:exit("TRUE") end -- PROPBONUS.scr:44
end

script.labels["GiveBonus"] = function(ctx)
    -- PROPBONUS.scr:47
    ctx:command("getrandomint", "BONUS_MIN,BONUS_MAX, nBonusValue") -- PROPBONUS.scr:49
    if ctx:condition("nType==0") then -- PROPBONUS.scr:51
        ctx:giveGold("nBonusValue") -- PROPBONUS.scr:52
    end -- PROPBONUS.scr:53
    if ctx:condition("nType==1") then -- PROPBONUS.scr:55
        if ctx:condition("hPlayer==0") then -- PROPBONUS.scr:56
            ctx:command("getplayerhandle", "hPlayer") -- PROPBONUS.scr:57
        end -- PROPBONUS.scr:58
        ctx:command("heal", "hPlayer, nBonusValue") -- PROPBONUS.scr:59
    end -- PROPBONUS.scr:60
    if ctx:condition("nType==2") then -- PROPBONUS.scr:62
        ctx:giveExp("nBonusValue") -- PROPBONUS.scr:63
    end -- PROPBONUS.scr:64
    if ctx:condition("nType==3") then -- PROPBONUS.scr:66
        -- give skill points here
    end -- PROPBONUS.scr:68
    if ctx:condition("nType==4") then -- PROPBONUS.scr:70
        -- give attr points here
    end -- PROPBONUS.scr:72
    ctx:command("playanim", "sAnimName, FadeOut") -- PROPBONUS.scr:74
    do return ctx:exit("TRUE") end -- PROPBONUS.scr:76
end

script.labels["FadeOut"] = function(ctx)
    -- PROPBONUS.scr:79
    -- loop an alpha decreaser to fade
    if ctx:condition("nBonusValue<=0") then -- PROPBONUS.scr:82
        ctx:command("getmyhandle", "hPlayer") -- PROPBONUS.scr:83
        ctx:command("removeobject", "hPlayer") -- PROPBONUS.scr:84
        do return ctx:exit("TRUE") end -- PROPBONUS.scr:85
    end -- PROPBONUS.scr:86
    -- decrement the alpha by frametime
    -- GetFrameTime nType
    -- nType = nType / 2
    -- GetColor nBonusValue
    -- nBonusValue = nBonusValue - nType
    -- SetColor nBonusValue
    ctx:command("wait", "0, .01, FadeOut") -- PROPBONUS.scr:95
    do return ctx:exit("TRUE") end -- PROPBONUS.scr:97
end

return script
