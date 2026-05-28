-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "YANMIRFORT_BUGSPAWN.scr"
script.includes = {}
script.labels = {}


-- YanmirFort_BugSpawn.scr
-- Jeff Leggett
-- 01/03/2002
-- 10 - 15 minutes of real-time before we'll spawn...
script.labels["DoSpawn"] = function(ctx)
    -- YANMIRFORT_BUGSPAWN.scr:26
    -- Make sure player can't see this happen.
    ctx:command("getplayerhandle", "hPlayer") -- YANMIRFORT_BUGSPAWN.scr:37
    ctx:command("isvisible", "hPlayer,bVisible") -- YANMIRFORT_BUGSPAWN.scr:39
    if ctx:condition("bVisible==1") then -- YANMIRFORT_BUGSPAWN.scr:41
        ctx:command("nrewaitnbr", "= nReWaitNbr + 1") -- YANMIRFORT_BUGSPAWN.scr:42
        if ctx:condition("nReWaitNbr > 29") then -- YANMIRFORT_BUGSPAWN.scr:43
            ctx:command("nrewaitnbr", "= 16") -- YANMIRFORT_BUGSPAWN.scr:44
        end -- YANMIRFORT_BUGSPAWN.scr:45
        -- keep waiting until player leaves...
        ctx:command("wait", "nReWaitNbr,5,DoSpawn") -- YANMIRFORT_BUGSPAWN.scr:47
        do return ctx:exit("") end -- YANMIRFORT_BUGSPAWN.scr:48
    end -- YANMIRFORT_BUGSPAWN.scr:49
    ctx:command("getpos", "hMyObject,x,y,z") -- YANMIRFORT_BUGSPAWN.scr:51
    ctx:command("spawn", "hSpawn,x,y,z,sCmd") -- YANMIRFORT_BUGSPAWN.scr:52
    do return ctx:exit("") end -- YANMIRFORT_BUGSPAWN.scr:54
end

script.labels["OnRespawnMe"] = function(ctx)
    -- YANMIRFORT_BUGSPAWN.scr:57
    ctx:command("nwaitnbr", "= nWaitNbr + 1") -- YANMIRFORT_BUGSPAWN.scr:60
    if ctx:condition("nWaitNbr > 15") then -- YANMIRFORT_BUGSPAWN.scr:62
        ctx:command("nwaitnbr", "= 0") -- YANMIRFORT_BUGSPAWN.scr:63
    end -- YANMIRFORT_BUGSPAWN.scr:64
    ctx:command("getrandomfloat", "MIN_SPAWN_TIME,MAX_SPAWN_TIME,nRandom") -- YANMIRFORT_BUGSPAWN.scr:66
    ctx:command("wait", "nWaitNbr,nRandom,DoSpawn") -- YANMIRFORT_BUGSPAWN.scr:68
    do return ctx:exit("") end -- YANMIRFORT_BUGSPAWN.scr:71
end

script.labels["Main"] = function(ctx)
    -- YANMIRFORT_BUGSPAWN.scr:74
    ctx:command("getmyhandle", "hMyObject") -- YANMIRFORT_BUGSPAWN.scr:76
    ctx:command("getobjectname", "hMyObject,sMyName") -- YANMIRFORT_BUGSPAWN.scr:78
    -- DeathTriggerTarget
    ctx:command("set", "sCmd,IceLobbercicle DeathTriggerMessage RespawnMe") -- YANMIRFORT_BUGSPAWN.scr:80
    ctx:command("scmd", "= sCmd + SPACE + sMyName") -- YANMIRFORT_BUGSPAWN.scr:82
    ctx:command("debugout", "spawnCmd=") -- YANMIRFORT_BUGSPAWN.scr:84
    ctx:command("debugout", "sCmd") -- YANMIRFORT_BUGSPAWN.scr:85
    ctx:addTrigger("RespawnMe", "OnRespawnMe") -- YANMIRFORT_BUGSPAWN.scr:87
    do return ctx:exit("") end -- YANMIRFORT_BUGSPAWN.scr:89
end

return script
