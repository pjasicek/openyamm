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
    ctx:self():playAnimation("Hattack2", "OnMonsterSpawn") -- TASARTEACHER.scr:24
    do return ctx:exit(1) end -- TASARTEACHER.scr:25
end

script.labels["OnMonsterSpawn"] = function(ctx)
    -- TASARTEACHER.scr:29
    -- Spawn monster to fight
    ctx:object("Student0"):trigger("Hate") -- TASARTEACHER.scr:33-34
    ctx:object("Student1"):trigger("Hate") -- TASARTEACHER.scr:36-37
    ctx:object("Student2"):trigger("Hate") -- TASARTEACHER.scr:39-40
    ctx:object("Student3"):trigger("Hate") -- TASARTEACHER.scr:42-43
    ctx:object("DooksGuardCaptain0"):trigger("Hate") -- TASARTEACHER.scr:45-46
    ctx:object("DooksGuardCaptain1"):trigger("Hate") -- TASARTEACHER.scr:48-49
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
