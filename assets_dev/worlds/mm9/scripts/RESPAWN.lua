-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "RESPAWN.scr"
script.includes = {}
script.labels = {}


-- Auto-spawn...
script.labels["DoSpawn"] = function(ctx)
    -- RESPAWN.scr:7
    ctx:object("AISpawn0"):trigger("Trigger") -- RESPAWN.scr:9-10
    ctx:object("AISpawn1"):trigger("Trigger") -- RESPAWN.scr:12-13
    ctx:object("AISpawn2"):trigger("Trigger") -- RESPAWN.scr:15-16
    do return ctx:exit("") end -- RESPAWN.scr:18
end

script.labels["SpawnCheck"] = function(ctx)
    -- RESPAWN.scr:20
    ctx:getObjects("AIBase", 5000, 50, "array", "count") -- RESPAWN.scr:22
    if ctx:condition("count==0") then -- RESPAWN.scr:24
        mm9.gosub(script, ctx, "DoSpawn") -- RESPAWN.scr:25
        ctx:wait(0, 5, "SpawnCheck") -- RESPAWN.scr:26
        do return ctx:exit("") end -- RESPAWN.scr:27
    end -- RESPAWN.scr:28
    ctx:wait(0, 0.1, "SpawnCheck") -- RESPAWN.scr:30
    do return ctx:exit("") end -- RESPAWN.scr:32
end

script.labels["Main"] = function(ctx)
    -- RESPAWN.scr:35
    ctx:wait(0, 0.1, "SpawnCheck") -- RESPAWN.scr:36
    do return ctx:exit("") end -- RESPAWN.scr:39
end

return script
