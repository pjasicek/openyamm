-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BARREL.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 22, path = "globals.inc" }

-- NPC88.scr
-- timmy
-- handles colored barrel bonuses.
-- Barrel	Large or small
-- 40% Empty
-- 10% Red liquid, +1 Might perm
-- 10% Yellow liquid, +1 Accuracy perm
-- 10% Blue liquid, +1 Personality perm
-- 10% Green liquid, +1 Endurance perm
-- 10% Purple liquid, +1 Speed perm
-- 10% White liquid, +1 Luck perm
script.labels["Main"] = function(ctx)
    -- BARREL.scr:29
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- BARREL.scr:36
    ctx:addTrigger("Use", "OnUse") -- BARREL.scr:38
    do return ctx:exit("") end -- BARREL.scr:40
end

return script
