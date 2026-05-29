-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "HATENPC.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "basemelee.inc" }

-- Hate.scr
-- timmy
-- Makes things hate things and then runs BaseMelee
script.labels["Main"] = function(ctx)
    -- HATENPC.scr:12
    -- traceon
    -- Don't Forget to Delete this!
    ctx:self():addEnemy("NPC") -- HATENPC.scr:17
    ctx:self():addEnemy("ClanSoldier") -- HATENPC.scr:18
    ctx:self():addEnemy("KiratheCold") -- HATENPC.scr:19
    mm9.gosub(script, ctx, "BaseInit") -- HATENPC.scr:20
    do return ctx:exit("") end -- HATENPC.scr:21
end

return script
