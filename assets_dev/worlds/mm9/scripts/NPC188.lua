-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC188.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC188.scr
-- timmy
-- handles Nathi A'Mor voice and quest stuff
script.labels["OnRude"] = function(ctx)
    -- NPC188.scr:13
    mm9.gosub(script, ctx, "ritual") -- NPC188.scr:16
    do return ctx:exit("") end -- NPC188.scr:19
end

script.labels["ritual"] = function(ctx)
    -- NPC188.scr:23
    -- ritual Quest
    if not ctx:hasKey(258) then -- NPC188.scr:29-30
        if ctx:hasKey(257) then -- NPC188.scr:31-32
            ctx:giveItem(430) -- NPC188.scr:33
            ctx:giveExp(5000) -- NPC188.scr:34
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC188.scr:35
            ctx:giveKey(258) -- NPC188.scr:36
            do return ctx:exit("") end -- NPC188.scr:37
        end -- NPC188.scr:38
    end -- NPC188.scr:39
    do return ctx:exit("") end -- NPC188.scr:40
end

-- End ritual quest
script.labels["OnUse"] = function(ctx)
    -- NPC188.scr:50
    ctx:playSound("voices\\NPC\\NPC_188.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC188.scr:53
    do return ctx:exit("") end -- NPC188.scr:54
end

script.labels["OnExit"] = function(ctx)
    -- NPC188.scr:57
    do return ctx:exit("") end -- NPC188.scr:60
end

script.labels["Main"] = function(ctx)
    -- NPC188.scr:63
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC188.scr:70
    ctx:addTrigger("Use", "OnUse") -- NPC188.scr:72
    do return ctx:exit("") end -- NPC188.scr:74
end

return script
