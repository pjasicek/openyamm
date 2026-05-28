-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "PLEDGE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "pledge.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "basewander.inc" }

-- Pledge.scr
-- timmy
-- handles NPCs who give green man pledge
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- PLEDGE.scr:20
    mm9.gosub(script, ctx, "pledge") -- PLEDGE.scr:23
    do return ctx:exit("") end -- PLEDGE.scr:24
end

script.labels["Main"] = function(ctx)
    -- PLEDGE.scr:28
    -- traceon
    -- Don't Forget to Delete this!
    mm9.gosub(script, ctx, "basewanderinit") -- PLEDGE.scr:33
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- PLEDGE.scr:35
    do return ctx:exit("") end -- PLEDGE.scr:36
end

return script
