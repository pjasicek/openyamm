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
    ctx:state().Counter = (tonumber(ctx:state().Counter) or 0) + 1 -- DP2DRAGONDEAD.scr:27
    if ctx:condition("counter<DeadCount") then -- DP2DRAGONDEAD.scr:29
        do return ctx:exit("") end -- DP2DRAGONDEAD.scr:30
    end -- DP2DRAGONDEAD.scr:31
    -- ---Monsters are dead, now do this!!---
    ctx:object("Door12"):trigger("Open") -- DP2DRAGONDEAD.scr:35-36
    ctx:state().BeenDone = true -- DP2DRAGONDEAD.scr:37
    ctx:wait(0.2, 0.2, "killme") -- DP2DRAGONDEAD.scr:38
    do return ctx:exit("") end -- DP2DRAGONDEAD.scr:41
end

script.labels["OnMonsterDead"] = function(ctx)
    -- DP2DRAGONDEAD.scr:44
    ctx:debugOut("OnMonsterDead!!!!!") -- DP2DRAGONDEAD.scr:47
    ctx:getParam(0, "g_hObject") -- DP2DRAGONDEAD.scr:49
    if ctx:condition("g_hObject!=NULL") then -- DP2DRAGONDEAD.scr:51
        ctx:state().g_sTemp = ctx:object("g_hObject"):name() -- DP2DRAGONDEAD.scr:52
        if ctx:condition("g_sTemp==DragonAzure0") then -- DP2DRAGONDEAD.scr:54
            if ctx:condition("Counter==0") then -- DP2DRAGONDEAD.scr:55
                -- Inform DragonAzure1 that DragonAzure0 is dead...
                -- (But only if DragonAzure1 is still alive!!!)
                ctx:state().g_hObject = ctx:objectOrNil("DragonAzure1") -- DP2DRAGONDEAD.scr:58
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
    ctx:exitScript() -- DP2DRAGONDEAD.scr:76
end

script.labels["Main"] = function(ctx)
    -- DP2DRAGONDEAD.scr:80
    -- TraceOn
    ctx:getParam(0, "DeadCount") -- DP2DRAGONDEAD.scr:84
    ctx:addTrigger("MonsterDead", "OnMonsterDead") -- DP2DRAGONDEAD.scr:86
    do return ctx:exit("") end -- DP2DRAGONDEAD.scr:88
end

return script
