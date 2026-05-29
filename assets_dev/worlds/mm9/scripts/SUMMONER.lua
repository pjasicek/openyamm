-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SUMMONER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 15, path = "baseMelee.inc" }
script.includes[#script.includes + 1] = { line = 16, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 17, path = "ListMaker.inc" }

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
    -- SUMMONER.scr:25
    ctx:getParam(0, "LISTNAME") -- SUMMONER.scr:27
    ctx:getParam(1, "LISTFIRST") -- SUMMONER.scr:28
    ctx:getParam(2, "LISTLAST") -- SUMMONER.scr:29
    ctx:onEvent("OnPostStartWorld", "InitSummoner") -- SUMMONER.scr:31
    ctx:onEvent("OnPostMiniSaveLoad", "InitSummoner") -- SUMMONER.scr:32
    ctx:onEvent("OnCacheFiles", "CacheFiles") -- SUMMONER.scr:33
    do return ctx:exit("TRUE") end -- SUMMONER.scr:35
end

script.labels["CacheFiles"] = function(ctx)
    -- SUMMONER.scr:38
    ctx:cacheClientFx("SPELL_SPARKLIES") -- SUMMONER.scr:40
    ctx:cacheClientFx("SPELL_BLUEFIRE") -- SUMMONER.scr:41
    ctx:cacheSound("sounds\\magic\\cast09.wav") -- SUMMONER.scr:43
    ctx:cacheSound("sounds\\magic\\cast06.wav") -- SUMMONER.scr:44
    do return ctx:exit("TRUE") end -- SUMMONER.scr:46
end

script.labels["InitSummoner"] = function(ctx)
    -- SUMMONER.scr:49
    ctx:state().hSpawner = ctx:objectOrNil("SpawnMgr") -- SUMMONER.scr:51
    ctx:addTrigger("trigger", "OnMinionDied") -- SUMMONER.scr:53
    ctx:addTrigger("startup", "SummonStarters") -- SUMMONER.scr:54
    mm9.gosub(script, ctx, "BaseInit") -- SUMMONER.scr:56
    ctx:onEvent("OnDeath", "OnDeath") -- SUMMONER.scr:58
    do return ctx:exit("TRUE") end -- SUMMONER.scr:60
end

script.labels["SummonStarters"] = function(ctx)
    -- SUMMONER.scr:63
    -- summon the starter batch
    mm9.gosub(script, ctx, "GetFirstObject") -- SUMMONER.scr:66
    while ctx:condition("ARRIVEDLAST!=TRUE") do -- SUMMONER.scr:67
        ctx:object("LISTOBJECT"):doClientFx("SPELL_SPARKLIES", "FALSE", "TRUE") -- SUMMONER.scr:68
        ctx:object("LISTOBJECT"):doClientFx("SPELL_BLUEFIRE", "FALSE", "TRUE") -- SUMMONER.scr:69
        ctx:trigger("LISTOBJECT", "spawn") -- SUMMONER.scr:70
        mm9.gosub(script, ctx, "GetNextObject") -- SUMMONER.scr:71
    end -- SUMMONER.scr:72
    ctx:trigger("LISTOBJECT", "spawn") -- SUMMONER.scr:73
    mm9.gosub(script, ctx, "OnMinionDied") -- SUMMONER.scr:75
    do return ctx:exit("TRUE") end -- SUMMONER.scr:77
end

script.labels["OnDeath"] = function(ctx)
    -- SUMMONER.scr:80
    -- since dead, shut off spawning
    ctx:trigger("hSpawner", "off") -- SUMMONER.scr:83
    do return ctx:exit("TRUE") end -- SUMMONER.scr:85
end

script.labels["OnMinionDied"] = function(ctx)
    -- SUMMONER.scr:88
    -- play summon anim, randomize next spawn point
    -- randomize the spawn location
    ctx:randomInt("LISTFIRST", "LISTLAST", "LISTINDEX") -- SUMMONER.scr:92
    mm9.gosub(script, ctx, "GetCurrentObject") -- SUMMONER.scr:93
    ctx:trigger("LISTOBJECT", "focus") -- SUMMONER.scr:94
    ctx:object("LISTOBJECT"):doClientFx("SPELL_SPARKLIES", "FALSE", "TRUE") -- SUMMONER.scr:95
    ctx:object("LISTOBJECT"):doClientFx("SPELL_BLUEFIRE", "FALSE", "TRUE") -- SUMMONER.scr:96
    -- act like a powerful lich guy
    ctx:self():playAnimation("RAttack1", "StopMoving") -- SUMMONER.scr:99
    ctx:playSound("sounds\\magic\\cast09.wav", "DoNothing", 1, 500, "FALSE", 100) -- SUMMONER.scr:100
    ctx:playSound("sounds\\magic\\cast06.wav", "DoNothing", 1, 500, "FALSE", 100) -- SUMMONER.scr:101
    ctx:playSound("sounds\\animsounds\\banshee\\transition.wav", "DoNothing", 1, 500, "FALSE", 100) -- SUMMONER.scr:102
    do return ctx:exit("TRUE") end -- SUMMONER.scr:104
end

return script
