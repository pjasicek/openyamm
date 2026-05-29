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
    ctx:wait(1, 1, "OnSpawn2") -- SPAWNGENERIC.scr:36
    do return ctx:exit("") end -- SPAWNGENERIC.scr:37
end

script.labels["Onspawn2"] = function(ctx)
    -- SPAWNGENERIC.scr:41
    if ctx:condition("sPath==Terrors") then -- SPAWNGENERIC.scr:44
        ctx:state().g_hobject = ctx:objectOrNil("EndCount") -- SPAWNGENERIC.scr:45
        if ctx:condition("g_hobject!=NULL") then -- SPAWNGENERIC.scr:46
            ctx:trigger("g_hobject", "Spawned") -- SPAWNGENERIC.scr:47
        end -- SPAWNGENERIC.scr:48
    end -- SPAWNGENERIC.scr:49
    ctx:self():doClientFx("GreaterDemon") -- SPAWNGENERIC.scr:53
    ctx:playSound("\\Sounds\\magic\\Windup10.wav", "DoNothing", 100, 24000, "FALSE", 100) -- SPAWNGENERIC.scr:54
    ctx:wait(1, 2, "Appear") -- SPAWNGENERIC.scr:55
    do return ctx:exit("") end -- SPAWNGENERIC.scr:56
end

script.labels["Appear"] = function(ctx)
    -- SPAWNGENERIC.scr:60
    -- play appear effect here
    ctx:playSound("\\Sounds\\spells\\TownPortal.wav", "DoNothing", 100, 24000, "FALSE", 100) -- SPAWNGENERIC.scr:64
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:self():pos() -- SPAWNGENERIC.scr:65
    ctx:state().hMonster = ctx:spawn("Xpos", "YPos", "ZPos", "sMonster") -- SPAWNGENERIC.scr:66
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
    ctx:set("sMonster", "sMonster + sScript") -- SPAWNGENERIC.scr:84
    do return ctx:exit("") end -- SPAWNGENERIC.scr:88
end

return script
