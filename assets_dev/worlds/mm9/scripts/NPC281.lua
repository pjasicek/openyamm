-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC281.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC281.scr
-- timmy
-- handles the retainer stuff
script.labels["OnRude"] = function(ctx)
    -- NPC281.scr:10
    do return ctx:exit("") end -- NPC281.scr:16
end

script.labels["OnUse"] = function(ctx)
    -- NPC281.scr:20
    ctx:playSound("voices\\NPC\\NPC_281.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC281.scr:23
    do return ctx:exit("") end -- NPC281.scr:24
end

script.labels["OnExit"] = function(ctx)
    -- NPC281.scr:27
    do return ctx:exit("") end -- NPC281.scr:30
end

script.labels["Main"] = function(ctx)
    -- NPC281.scr:33
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC281.scr:40
    ctx:addTrigger("Use", "OnUse") -- NPC281.scr:42
    do return ctx:exit("") end -- NPC281.scr:44
end

return script
