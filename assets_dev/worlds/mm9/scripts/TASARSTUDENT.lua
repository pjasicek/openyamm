-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TASARSTUDENT.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "baseMelee.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "Range.inc" }

-- TaSarStudent.scr
-- 10/4
-- timmy + SJR
-- handles the students going to the combat arena
script.labels["OnHate"] = function(ctx)
    -- TASARSTUDENT.scr:16
    ctx:self():addEnemy("L_Enemy") -- TASARSTUDENT.scr:18
    do return ctx:exit(1) end -- TASARSTUDENT.scr:20
end

script.labels["Main"] = function(ctx)
    -- TASARSTUDENT.scr:24
    ctx:addTrigger("Hate", "OnHate") -- TASARSTUDENT.scr:26
    ctx:getParam(0, "L_Enemy") -- TASARSTUDENT.scr:27
    ctx:self():addFriend("L_Enemy") -- TASARSTUDENT.scr:28
    mm9.gosub(script, ctx, "RangeInit") -- TASARSTUDENT.scr:29
    mm9.gosub(script, ctx, "BaseInit") -- TASARSTUDENT.scr:30
    do return ctx:exit(1) end -- TASARSTUDENT.scr:32
end

return script
