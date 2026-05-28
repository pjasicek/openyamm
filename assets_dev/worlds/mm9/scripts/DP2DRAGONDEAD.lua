-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DP2DRAGONDEAD.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- DP2Monsterdead.scr
-- timmy
-- Checks to see if both Monsters are dead in MonsterPharaoh2
-- Parameters:
-- p0   amount of monsters you want to check for dead
-- #NumberArray			MonsterArray[20]
script.labels["CheckAllMonsters"] = function(ctx)
    -- DP2DRAGONDEAD.scr:21
    ctx:command("add", "Counter, 1") -- DP2DRAGONDEAD.scr:27
    if ctx:condition("counter<DeadCount") then -- DP2DRAGONDEAD.scr:29
        do return ctx:exit("") end -- DP2DRAGONDEAD.scr:30
    end -- DP2DRAGONDEAD.scr:31
    -- ---Monsters are dead, now do this!!---
    ctx:command("getobjecthandle", "Door12, g_hobject") -- DP2DRAGONDEAD.scr:35
    ctx:trigger("g_hobject", "Open") -- DP2DRAGONDEAD.scr:36
    ctx:command("set", "BeenDone, true") -- DP2DRAGONDEAD.scr:37
    ctx:command("wait", "0.2, killme") -- DP2DRAGONDEAD.scr:38
    do return ctx:exit("") end -- DP2DRAGONDEAD.scr:41
end

script.labels["OnMonsterDead"] = function(ctx)
    -- DP2DRAGONDEAD.scr:44
    ctx:command("debugout", "OnMonsterDead!!!!!") -- DP2DRAGONDEAD.scr:47
    ctx:getParam(0, "g_hObject") -- DP2DRAGONDEAD.scr:49
    if ctx:condition("g_hObject!=NULL") then -- DP2DRAGONDEAD.scr:51
        ctx:command("getobjectname", "g_hObject, g_sTemp") -- DP2DRAGONDEAD.scr:52
        if ctx:condition("g_sTemp==DragonAzure0") then -- DP2DRAGONDEAD.scr:54
            if ctx:condition("Counter==0") then -- DP2DRAGONDEAD.scr:55
                -- Inform DragonAzure1 that DragonAzure0 is dead...
                -- (But only if DragonAzure1 is still alive!!!)
                ctx:command("getobjecthandle", "DragonAzure1, g_hObject") -- DP2DRAGONDEAD.scr:58
                if ctx:condition("g_hObject!=NULL") then -- DP2DRAGONDEAD.scr:60
                    ctx:trigger("g_hObject", "DragonAzure0Dead") -- DP2DRAGONDEAD.scr:61
                end -- DP2DRAGONDEAD.scr:62
            end -- DP2DRAGONDEAD.scr:63
        end -- DP2DRAGONDEAD.scr:64
    end -- DP2DRAGONDEAD.scr:66
    mm9.gosub(script, ctx, "CheckAllMonsters") -- DP2DRAGONDEAD.scr:68
    do return ctx:exit("") end -- DP2DRAGONDEAD.scr:70
end

script.labels["killme"] = function(ctx)
    -- DP2DRAGONDEAD.scr:73
    ctx:command("exitscript", "") -- DP2DRAGONDEAD.scr:76
end

script.labels["Main"] = function(ctx)
    -- DP2DRAGONDEAD.scr:80
    -- TraceOn
    ctx:getParam(0, "DeadCount") -- DP2DRAGONDEAD.scr:84
    ctx:addTrigger("MonsterDead", "OnMonsterDead") -- DP2DRAGONDEAD.scr:86
    do return ctx:exit("") end -- DP2DRAGONDEAD.scr:88
end

return script
