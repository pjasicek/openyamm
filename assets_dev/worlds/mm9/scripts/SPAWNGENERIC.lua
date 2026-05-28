-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SPAWNGENERIC.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- SpawnGeneric.scr
-- timmy
-- spawns a Generic Monster
-- 1/21/02
-- flag variables
script.labels["Onspawn"] = function(ctx)
    -- SPAWNGENERIC.scr:32
    ctx:command("wait", "1 1 OnSpawn2") -- SPAWNGENERIC.scr:36
    do return ctx:exit("") end -- SPAWNGENERIC.scr:37
end

script.labels["Onspawn2"] = function(ctx)
    -- SPAWNGENERIC.scr:41
    if ctx:condition("sPath==Terrors") then -- SPAWNGENERIC.scr:44
        ctx:command("getobjecthandle", "EndCount g_hobject") -- SPAWNGENERIC.scr:45
        if ctx:condition("g_hobject!=NULL") then -- SPAWNGENERIC.scr:46
            ctx:trigger("g_hobject", "Spawned") -- SPAWNGENERIC.scr:47
        end -- SPAWNGENERIC.scr:48
    end -- SPAWNGENERIC.scr:49
    ctx:command("getmyhandle", "g_hmyobject") -- SPAWNGENERIC.scr:52
    ctx:command("doclientfx", "g_hMyObject,GreaterDemon") -- SPAWNGENERIC.scr:53
    ctx:command("playsound", "\\Sounds\\magic\\Windup10.wav, DoNothing, 100, 24000, FALSE, 100") -- SPAWNGENERIC.scr:54
    ctx:command("wait", "1 2 Appear") -- SPAWNGENERIC.scr:55
    do return ctx:exit("") end -- SPAWNGENERIC.scr:56
end

script.labels["Appear"] = function(ctx)
    -- SPAWNGENERIC.scr:60
    -- play appear effect here
    ctx:command("playsound", "\\Sounds\\spells\\TownPortal.wav, DoNothing, 100, 24000, FALSE, 100") -- SPAWNGENERIC.scr:64
    ctx:command("getpos", "g_hmyobject XPos YPos ZPos") -- SPAWNGENERIC.scr:65
    ctx:command("spawn", "hMonster Xpos YPos ZPos sMonster") -- SPAWNGENERIC.scr:66
    do return ctx:exit("") end -- SPAWNGENERIC.scr:67
end

script.labels["Main"] = function(ctx)
    -- SPAWNGENERIC.scr:72
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Spawn", "Onspawn") -- SPAWNGENERIC.scr:77
    ctx:getParam(0, "sMonster") -- SPAWNGENERIC.scr:78
    ctx:getParam(1, "sPath") -- SPAWNGENERIC.scr:79
    if ctx:condition("bFace==1") then -- SPAWNGENERIC.scr:81
        do return ctx:exit("") end -- SPAWNGENERIC.scr:82
    end -- SPAWNGENERIC.scr:83
    ctx:command("smonster", "= sMonster + sScript") -- SPAWNGENERIC.scr:84
    do return ctx:exit("") end -- SPAWNGENERIC.scr:88
end

return script
