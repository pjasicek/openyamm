-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TASARTEACHER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "baseMelee.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "range.inc" }

-- TaSarTeacher.scr
-- 10/4
-- timmy + SJR
-- handles the students going to the combat arena
script.labels["OnSpawn"] = function(ctx)
    -- TASARTEACHER.scr:20
    -- Spawn monster to fight
    ctx:command("playanim", "Hattack2 OnMonsterSpawn") -- TASARTEACHER.scr:24
    do return ctx:exit(1) end -- TASARTEACHER.scr:25
end

script.labels["OnMonsterSpawn"] = function(ctx)
    -- TASARTEACHER.scr:29
    -- Spawn monster to fight
    ctx:command("getobjecthandle", "Student0 g_hobject") -- TASARTEACHER.scr:33
    ctx:trigger("g_Hobject", "Hate") -- TASARTEACHER.scr:34
    ctx:command("getobjecthandle", "Student1 g_hobject") -- TASARTEACHER.scr:36
    ctx:trigger("g_Hobject", "Hate") -- TASARTEACHER.scr:37
    ctx:command("getobjecthandle", "Student2 g_hobject") -- TASARTEACHER.scr:39
    ctx:trigger("g_Hobject", "Hate") -- TASARTEACHER.scr:40
    ctx:command("getobjecthandle", "Student3 g_hobject") -- TASARTEACHER.scr:42
    ctx:trigger("g_Hobject", "Hate") -- TASARTEACHER.scr:43
    ctx:command("getobjecthandle", "DooksGuardCaptain0 g_hobject") -- TASARTEACHER.scr:45
    ctx:trigger("g_Hobject", "Hate") -- TASARTEACHER.scr:46
    ctx:command("getobjecthandle", "DooksGuardCaptain1 g_hobject") -- TASARTEACHER.scr:48
    ctx:trigger("g_Hobject", "Hate") -- TASARTEACHER.scr:49
    do return ctx:exit("") end -- TASARTEACHER.scr:51
end

script.labels["Main"] = function(ctx)
    -- TASARTEACHER.scr:55
    -- traceon
    -- Don't Forget to Delete this!
    mm9.gosub(script, ctx, "RangeInit") -- TASARTEACHER.scr:61
    mm9.gosub(script, ctx, "BaseInit") -- TASARTEACHER.scr:62
    ctx:addTrigger("Fight", "OnSpawn") -- TASARTEACHER.scr:64
    do return ctx:exit("") end -- TASARTEACHER.scr:65
end

return script
