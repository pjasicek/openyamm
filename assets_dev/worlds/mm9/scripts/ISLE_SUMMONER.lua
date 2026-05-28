-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ISLE_SUMMONER.scr"
script.includes = {}
script.labels = {}


-- Summoner.scr
-- by SJR
-- 11-01-01
-- Purpose:uses SpawnMgr to summon
-- guys, look all dramatic
-- and give player an incentive
-- to kill the summoner soon
-- ScriptParams:
-- p0 = name of spawn locations
-- p1 = index of first
-- p2 = index of last
script.labels["Main"] = function(ctx)
    -- ISLE_SUMMONER.scr:29
    ctx:getParam(0, "sCreatureName") -- ISLE_SUMMONER.scr:31
    ctx:getParam(1, "sLocationName") -- ISLE_SUMMONER.scr:32
    ctx:command("onpoststartworld", "InitSummoner") -- ISLE_SUMMONER.scr:34
    ctx:command("onpostminisaveload", "InitSummoner") -- ISLE_SUMMONER.scr:35
    ctx:command("oncachefiles", "CacheFiles") -- ISLE_SUMMONER.scr:36
    do return ctx:exit(1) end -- ISLE_SUMMONER.scr:38
end

script.labels["CacheFiles"] = function(ctx)
    -- ISLE_SUMMONER.scr:41
    ctx:command("cachescript", "\"Isle_SpawnCreature.scr\"") -- ISLE_SUMMONER.scr:43
    do return ctx:exit(1) end -- ISLE_SUMMONER.scr:45
end

script.labels["InitSummoner"] = function(ctx)
    -- ISLE_SUMMONER.scr:48
    ctx:command("spawn_param", "= sCreatureName + sScriptName") -- ISLE_SUMMONER.scr:50
    ctx:command("getobjecthandle", "sLocationName, hDummy") -- ISLE_SUMMONER.scr:51
    ctx:command("getpos", "hDummy, x,y,z") -- ISLE_SUMMONER.scr:52
    ctx:addTrigger("spawn", "SpawnCreature") -- ISLE_SUMMONER.scr:54
    do return ctx:exit(1) end -- ISLE_SUMMONER.scr:56
end

script.labels["SpawnCreature"] = function(ctx)
    -- ISLE_SUMMONER.scr:59
    if ctx:condition("nCounter>=5") then -- ISLE_SUMMONER.scr:61
        ctx:command("removetrigger", "spawn") -- ISLE_SUMMONER.scr:62
    end -- ISLE_SUMMONER.scr:63
    ctx:command("ncounter", "= nCounter + 1") -- ISLE_SUMMONER.scr:65
    ctx:command("playanim", "hattack1") -- ISLE_SUMMONER.scr:66
    ctx:command("spawn", "hDummy, x,y,z, SPAWN_PARAM") -- ISLE_SUMMONER.scr:67
    do return ctx:exit(1) end -- ISLE_SUMMONER.scr:69
end

return script
