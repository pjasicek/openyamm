-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC377.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "Basewander.inc" }

-- NPC337.scr
-- timmy
-- handles Fre voice and quest stuff
script.labels["OnUse"] = function(ctx)
    -- NPC377.scr:15
    ctx:doRude(377) -- NPC377.scr:18
    do return ctx:exit("") end -- NPC377.scr:19
end

script.labels["Main"] = function(ctx)
    -- NPC377.scr:23
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Use", "OnUse") -- NPC377.scr:31
    mm9.gosub(script, ctx, "basewanderinit") -- NPC377.scr:32
    do return ctx:exit("") end -- NPC377.scr:33
end

return script
