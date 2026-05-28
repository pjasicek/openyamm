-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC1.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC1.scr
-- timmy
-- handles Kira the Cold voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC1.scr:20
    mm9.gosub(script, ctx, "Loveletter") -- NPC1.scr:23
    mm9.gosub(script, ctx, "honkys") -- NPC1.scr:24
    mm9.gosub(script, ctx, "mountainpass") -- NPC1.scr:25
    mm9.gosub(script, ctx, "united") -- NPC1.scr:26
    mm9.gosub(script, ctx, "treaty") -- NPC1.scr:27
    do return ctx:exit("") end -- NPC1.scr:28
end

script.labels["treaty"] = function(ctx)
    -- NPC1.scr:32
    -- treaty Quest
    ctx:hasKey(181, "keycheck") -- NPC1.scr:39
    if ctx:condition("keycheck==0") then -- NPC1.scr:40
        ctx:hasKey(89, "keycheck") -- NPC1.scr:41
        if ctx:condition("keycheck==1") then -- NPC1.scr:42
            ctx:giveKey(181) -- NPC1.scr:43
            ctx:giveExp(2000) -- NPC1.scr:44
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC1.scr:45
            ctx:giveItem(401) -- NPC1.scr:46
            do return ctx:exit("") end -- NPC1.scr:47
        end -- NPC1.scr:48
    end -- NPC1.scr:49
    -- End treaty quest
    do return ctx:exit("") end -- NPC1.scr:53
end

script.labels["loveletter"] = function(ctx)
    -- NPC1.scr:56
    -- Love Letter Quest
    ctx:hasKey(147, "keycheck") -- NPC1.scr:63
    if ctx:condition("keycheck==0") then -- NPC1.scr:64
        ctx:hasKey(23, "keycheck") -- NPC1.scr:65
        if ctx:condition("keycheck==1") then -- NPC1.scr:66
            ctx:takeItem(247) -- NPC1.scr:67
            ctx:giveKey(147) -- NPC1.scr:68
            ctx:giveExp(2000) -- NPC1.scr:69
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC1.scr:70
            do return ctx:exit("") end -- NPC1.scr:71
        end -- NPC1.scr:72
    end -- NPC1.scr:73
    -- End Love Letter quest
    do return ctx:exit("") end -- NPC1.scr:78
end

script.labels["honkys"] = function(ctx)
    -- NPC1.scr:82
    -- Rid Thronheim of Honkies Quest
    ctx:hasKey(146, "keycheck") -- NPC1.scr:89
    if ctx:condition("keycheck==0") then -- NPC1.scr:90
        ctx:hasKey(78, "keycheck") -- NPC1.scr:91
        if ctx:condition("keycheck==1") then -- NPC1.scr:92
            ctx:giveExp(4000) -- NPC1.scr:93
            ctx:giveKey(146) -- NPC1.scr:94
            ctx:giveGold(6000) -- NPC1.scr:95
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC1.scr:96
            do return ctx:exit("") end -- NPC1.scr:97
        end -- NPC1.scr:98
    end -- NPC1.scr:99
    -- End Thronheim of Honkies Quest
    do return ctx:exit("") end -- NPC1.scr:103
end

script.labels["MountainPass"] = function(ctx)
    -- NPC1.scr:106
    -- Open Mountain Pass Quest
    ctx:hasKey(152, "keycheck") -- NPC1.scr:114
    if ctx:condition("keycheck==0") then -- NPC1.scr:115
        ctx:hasKey(81, "keycheck") -- NPC1.scr:116
        if ctx:condition("keycheck==1") then -- NPC1.scr:117
            ctx:giveExp(4000) -- NPC1.scr:118
            ctx:giveKey(152) -- NPC1.scr:119
            ctx:giveGold(6000) -- NPC1.scr:120
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC1.scr:121
            do return ctx:exit("") end -- NPC1.scr:122
        end -- NPC1.scr:123
    end -- NPC1.scr:124
    -- End Open Moutain Pass Quest
    do return ctx:exit("") end -- NPC1.scr:130
end

script.labels["OnUse"] = function(ctx)
    -- NPC1.scr:134
    ctx:command("playsound", "voices\\NPC\\NPC_239.wav, Onexit, 100, 240, FALSE, 100") -- NPC1.scr:137
    mm9.gosub(script, ctx, "OnCheck") -- NPC1.scr:138
    do return ctx:exit("") end -- NPC1.scr:139
end

script.labels["OnExit"] = function(ctx)
    -- NPC1.scr:142
    do return ctx:exit("") end -- NPC1.scr:145
end

script.labels["givekey"] = function(ctx)
    -- NPC1.scr:148
    if not ctx:hasKey(180) then -- NPC1.scr:150-151
        if ctx:hasKey(88) then -- NPC1.scr:152-153
            ctx:giveKey(180) -- NPC1.scr:154
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC1.scr:155
            do return ctx:exit("") end -- NPC1.scr:156
        end -- NPC1.scr:157
    end -- NPC1.scr:158
    do return ctx:exit("") end -- NPC1.scr:160
end

script.labels["Main"] = function(ctx)
    -- NPC1.scr:163
    -- traceon
    -- Don't Forget to Delete this!
    ctx:command("@m", "6 : 00 Givekey Givekey") -- NPC1.scr:169
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC1.scr:170
    ctx:addTrigger("Use", "OnUse") -- NPC1.scr:172
    ctx:command("set", "Jarl, Kira") -- NPC1.scr:173
    mm9.gosub(script, ctx, "UnitedInit") -- NPC1.scr:174
    do return ctx:exit("") end -- NPC1.scr:179
end

return script
