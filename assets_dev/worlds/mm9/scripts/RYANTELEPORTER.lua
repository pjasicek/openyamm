-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "RYANTELEPORTER.scr"
script.includes = {}
script.labels = {}


-- ryanteleporter.scr
-- By Timmy
-- sets damage for water
script.labels["OnTele1"] = function(ctx)
    -- RYANTELEPORTER.scr:13
    ctx:self():setStringProperty("TeleportDestination", "tele1") -- RYANTELEPORTER.scr:16
    do return ctx:exit("") end -- RYANTELEPORTER.scr:17
end

script.labels["OnTele2"] = function(ctx)
    -- RYANTELEPORTER.scr:21
    ctx:self():setStringProperty("TeleportDestination", "tele2") -- RYANTELEPORTER.scr:24
    do return ctx:exit("") end -- RYANTELEPORTER.scr:25
end

script.labels["OnTele3"] = function(ctx)
    -- RYANTELEPORTER.scr:29
    ctx:self():setStringProperty("TeleportDestination", "tele3") -- RYANTELEPORTER.scr:32
    do return ctx:exit("") end -- RYANTELEPORTER.scr:33
end

script.labels["OnTele4"] = function(ctx)
    -- RYANTELEPORTER.scr:36
    ctx:self():setStringProperty("TeleportDestination", "tele4") -- RYANTELEPORTER.scr:39
    do return ctx:exit("") end -- RYANTELEPORTER.scr:40
end

script.labels["Main"] = function(ctx)
    -- RYANTELEPORTER.scr:45
    -- TRACEON
    ctx:addTrigger("tele1", "OnTele1") -- RYANTELEPORTER.scr:53
    ctx:addTrigger("tele2", "OnTele2") -- RYANTELEPORTER.scr:54
    ctx:addTrigger("tele3", "OnTele3") -- RYANTELEPORTER.scr:55
    ctx:addTrigger("tele4", "OnTele4") -- RYANTELEPORTER.scr:56
    do return ctx:exit("") end -- RYANTELEPORTER.scr:57
end

return script
