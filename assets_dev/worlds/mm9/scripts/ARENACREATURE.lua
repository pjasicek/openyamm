-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ARENACREATURE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "basedoor.inc" }

-- ArenaCreature.scr
-- timmy
-- handles scholar promo stuff
script.labels["OnArrive"] = function(ctx)
    -- ARENACREATURE.scr:20
    ctx:self():stop() -- ARENACREATURE.scr:24
    ctx:self():taunt("OnStartFight") -- ARENACREATURE.scr:26
    -- wait 1 2 OnStartFight
    do return ctx:exit("TRUE") end -- ARENACREATURE.scr:29
end

script.labels["OnStartFight"] = function(ctx)
    -- ARENACREATURE.scr:32
    ctx:object("ShopkeeperElfMaleB0"):trigger("Arrive") -- ARENACREATURE.scr:35-36
    do return ctx:exit("") end -- ARENACREATURE.scr:38
end

script.labels["Init"] = function(ctx)
    -- ARENACREATURE.scr:41
    ctx:state().g_ntemp = ctx:self():getStat("HitPoints") -- ARENACREATURE.scr:45
    ctx:set("nMinHP", "g_ntemp * .7") -- ARENACREATURE.scr:46
    ctx:set("nMaxHP", "g_ntemp * 1.5") -- ARENACREATURE.scr:47
    ctx:randomInt("nMinHP", "nMaxHP", "nHitPoints") -- ARENACREATURE.scr:48
    ctx:self():setStat("Hitpoints", "nHitPoints") -- ARENACREATURE.scr:49
    ctx:self():setStat("GaveTreasure", "TRUE") -- ARENACREATURE.scr:50
    local object = ctx:object("RotatingDoor2") -- ARENACREATURE.scr:52
    object:trigger("Unlock") -- ARENACREATURE.scr:53
    object:trigger("Use") -- ARENACREATURE.scr:54
    local object = ctx:object("RotatingDoor4") -- ARENACREATURE.scr:56
    object:trigger("Unlock") -- ARENACREATURE.scr:57
    object:trigger("Use") -- ARENACREATURE.scr:58
    ctx:wait(29, 2.2, "GetOutThere") -- ARENACREATURE.scr:60
    do return ctx:exit("") end -- ARENACREATURE.scr:62
end

script.labels["GetOutThere"] = function(ctx)
    -- ARENACREATURE.scr:65
    ctx:state().g_hobject = ctx:objectOrNil("marker2") -- ARENACREATURE.scr:68
    ctx:self():setTarget(ctx:object("g_hObject")) -- ARENACREATURE.scr:69
    ctx:self():runTo(ctx:object("g_hobject"), 128, "OnArrive") -- ARENACREATURE.scr:71
    do return ctx:exit("") end -- ARENACREATURE.scr:72
end

script.labels["OnHate"] = function(ctx)
    -- ARENACREATURE.scr:76
    ctx:self():addEnemy("AIBase") -- ARENACREATURE.scr:79
    ctx:self():addFriend("Player") -- ARENACREATURE.scr:80
    ctx:state().sScript = ctx:self():stringProperty("ScriptName") -- ARENACREATURE.scr:84
    -- cprint running script
    -- cprint sScript
    local object = ctx:object("RotatingDoor2") -- ARENACREATURE.scr:88
    object:trigger("close") -- ARENACREATURE.scr:89
    object:trigger("lock") -- ARENACREATURE.scr:90
    local object = ctx:object("RotatingDoor4") -- ARENACREATURE.scr:92
    object:trigger("close") -- ARENACREATURE.scr:93
    object:trigger("lock") -- ARENACREATURE.scr:94
    ctx:runScript("sScript") -- ARENACREATURE.scr:96
    do return ctx:exit("") end -- ARENACREATURE.scr:98
end

script.labels["FaceMarker"] = function(ctx)
    -- ARENACREATURE.scr:101
    ctx:state().g_hObject = ctx:objectOrNil("Marker2") -- ARENACREATURE.scr:104
    ctx:self():faceObject(ctx:object("g_hObject"), 0) -- ARENACREATURE.scr:105
    do return ctx:exit("") end -- ARENACREATURE.scr:106
end

script.labels["Main"] = function(ctx)
    -- ARENACREATURE.scr:110
    -- traceon
    -- Don't Forget to Delete this!
    ctx:getParam(0, "sMonster_ID") -- ARENACREATURE.scr:115
    ctx:giveKey(1011) -- ARENACREATURE.scr:116
    ctx:addTrigger("HateAll", "OnHate") -- ARENACREATURE.scr:117
    ctx:wait(2, 0.1, "FaceMarker") -- ARENACREATURE.scr:118
    ctx:wait(1, 3, "Init") -- ARENACREATURE.scr:119
    mm9.gosub(script, ctx, "BaseDoorInit") -- ARENACREATURE.scr:121
    ctx:self():setStringProperty("DeathTriggerTarget", "ShopkeeperElfMaleB0") -- ARENACREATURE.scr:126
    ctx:self():setStringProperty("DeathTriggerMessage", "IDied") -- ARENACREATURE.scr:127
    ctx:self():setNumberProperty("RunAwayChance", 0) -- ARENACREATURE.scr:128
    ctx:self():setNumberProperty("CanOpenDoors", 0) -- ARENACREATURE.scr:129
    ctx:state().g_sTemp = ctx:self():stringProperty("ScriptName") -- ARENACREATURE.scr:131
    ctx:cacheScript("g_sTemp") -- ARENACREATURE.scr:133
    do return ctx:exit("") end -- ARENACREATURE.scr:136
end

return script
