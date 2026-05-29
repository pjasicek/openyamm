-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC241.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "NPCBase.Inc" }

-- NPC241.scr
-- timmy
-- handles Ea;isaid A'Norta voice and quest stuff
-- #include globals.inc
script.labels["OnRUDEExit"] = function(ctx)
    -- NPC241.scr:13
    mm9.gosub(script, ctx, "BlackOrb") -- NPC241.scr:16
    mm9.gosub(script, ctx, "OnRUDEExit") -- NPC241.scr:17
    do return ctx:exit("") end -- NPC241.scr:18
end

script.labels["BlackOrb"] = function(ctx)
    -- NPC241.scr:22
    -- BlackOrb Quest
    if not ctx:hasKey(315) then -- NPC241.scr:27-28
        if ctx:hasKey(314) then -- NPC241.scr:29-30
            ctx:giveKey(315) -- NPC241.scr:31
            ctx:giveExp(50000) -- NPC241.scr:32
            ctx:giveGold(10000) -- NPC241.scr:33
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC241.scr:34
            ctx:takeItem(250) -- NPC241.scr:35
            do return ctx:exit("") end -- NPC241.scr:36
        end -- NPC241.scr:37
    end -- NPC241.scr:38
    do return ctx:exit("") end -- NPC241.scr:39
    -- End BlackOrb quest
    do return ctx:exit("") end -- NPC241.scr:44
end

script.labels["OnUse"] = function(ctx)
    -- NPC241.scr:49
    ctx:playSound("voices\\NPC\\NPC_241.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC241.scr:52
    do return ctx:exit("") end -- NPC241.scr:53
end

script.labels["OnExit"] = function(ctx)
    -- NPC241.scr:56
    do return ctx:exit("") end -- NPC241.scr:59
end

script.labels["Main"] = function(ctx)
    -- NPC241.scr:62
    -- traceon
    -- OnRudeExit OnRude
    ctx:addTrigger("Use", "OnUse") -- NPC241.scr:69
    mm9.gosub(script, ctx, "NPCBaseInit") -- NPC241.scr:71
    do return ctx:exit("") end -- NPC241.scr:73
end

return script
