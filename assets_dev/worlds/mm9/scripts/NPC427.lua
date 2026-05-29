-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC427.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "BaseDoor.inc" }

-- NPC427.scr
-- timmy
-- 10/30
-- handles rescuing from prison
script.labels["OnRude"] = function(ctx)
    -- NPC427.scr:13
    if ctx:hasKey(369) then -- NPC427.scr:16-17
        if not ctx:hasKey(370) then -- NPC427.scr:19-20
            ctx:giveKey(370) -- NPC427.scr:21
            ctx:giveExp(4000) -- NPC427.scr:22
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC427.scr:23
        end -- NPC427.scr:25
        ctx:wait(1, 1, "OnRunAway") -- NPC427.scr:26
    end -- NPC427.scr:27
    do return ctx:exit("") end -- NPC427.scr:29
end

script.labels["OnRunAway"] = function(ctx)
    -- NPC427.scr:32
    ctx:state().g_hobject = ctx:objectOrNil("AntoniMarker") -- NPC427.scr:35
    ctx:self():runTo(ctx:object("g_hobject"), 8, "OnVanish") -- NPC427.scr:36
    do return ctx:exit("") end -- NPC427.scr:37
end

script.labels["OnVanish"] = function(ctx)
    -- NPC427.scr:40
    ctx:self():remove() -- NPC427.scr:44
    do return ctx:exit("") end -- NPC427.scr:45
end

script.labels["DeleteCheck"] = function(ctx)
    -- NPC427.scr:48
    if ctx:hasKey(370) then -- NPC427.scr:51-52
        ctx:self():remove() -- NPC427.scr:54
        do return ctx:exit("") end -- NPC427.scr:55
    end -- NPC427.scr:56
    do return ctx:exit("") end -- NPC427.scr:57
end

script.labels["OnUse"] = function(ctx)
    -- NPC427.scr:60
    -- Playsound voices\NPC\NPC_090.wav, DoNothing, 100, 240, FALSE, 100
    do return ctx:exit("") end -- NPC427.scr:64
end

script.labels["Main"] = function(ctx)
    -- NPC427.scr:67
    -- traceon
    ctx:addTrigger("Use", "ONUse") -- NPC427.scr:73
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC427.scr:74
    mm9.gosub(script, ctx, "DeleteCheck") -- NPC427.scr:75
    mm9.gosub(script, ctx, "BaseDoorInit") -- NPC427.scr:76
    do return ctx:exit("") end -- NPC427.scr:77
end

return script
