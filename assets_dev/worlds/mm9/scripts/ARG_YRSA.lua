-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ARG_YRSA.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "basemelee.inc" }

-- arg_Yrsa.inc
-- By Timmy
-- 11/16
-- spawns Yrsa when she's supposed to appear
-- edited by Bones 7/16/02
-- TELP Patch 1.3 -- Makes dialog with Yrsa unavoidable.
-- flag variables
script.labels["OnAppear"] = function(ctx)
    -- ARG_YRSA.scr:25
    ctx:wait(1, 5, "Appear2") -- ARG_YRSA.scr:28
    do return ctx:exit("") end -- ARG_YRSA.scr:29
end

script.labels["Appear2"] = function(ctx)
    -- ARG_YRSA.scr:32
    ctx:self():doClientFx("GreaterDemon") -- ARG_YRSA.scr:35
    ctx:playSound("\\Sounds\\magic\\Windup10.wav", "DoNothing", 100, 24000, "FALSE", 100) -- ARG_YRSA.scr:36
    ctx:wait(1, 2, "Appear2b") -- ARG_YRSA.scr:37
    do return ctx:exit("") end -- ARG_YRSA.scr:38
end

script.labels["Appear2b"] = function(ctx)
    -- ARG_YRSA.scr:41
    -- play appear effect here
    ctx:playSound("\\Sounds\\spells\\TownPortal.wav", "DoNothing", 100, 24000, "FALSE", 100) -- ARG_YRSA.scr:45
    ctx:self():setFlag("visible", true) -- ARG_YRSA.scr:46
    ctx:self():playAnimation("fidget1", "DoRude") -- ARG_YRSA.scr:47
    do return ctx:exit("") end -- ARG_YRSA.scr:48
end

script.labels["DoRude"] = function(ctx)
    -- ARG_YRSA.scr:51
    -- shouldn't be needed
    ctx:giveKey(93) -- ARG_YRSA.scr:55
    ctx:state().g_hplayer = ctx:player() -- ARG_YRSA.scr:57
    ctx:self():setTarget(ctx:player()) -- ARG_YRSA.scr:58
    ctx:playSound("voices\\NPC\\NPC_001.wav", "DoNothing", 100, 24000, "FALSE", 100) -- ARG_YRSA.scr:59
    ctx:doRude(1) -- ARG_YRSA.scr:60
    do return ctx:exit("") end -- ARG_YRSA.scr:61
end

script.labels["OnRude"] = function(ctx)
    -- ARG_YRSA.scr:64
    -- this is for Yrsa after the arguement
    if not ctx:hasKey(185) then -- ARG_YRSA.scr:68-69
        if ctx:hasKey(93) then -- ARG_YRSA.scr:70-71
            -- this is where Forad is removed from the party
            -- GiveExp 16000
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- ARG_YRSA.scr:74
            ctx:giveKey(185) -- ARG_YRSA.scr:75
            ctx:wait(1, 1, "Vanish") -- ARG_YRSA.scr:76
            do return ctx:exit("") end -- ARG_YRSA.scr:77
        end -- ARG_YRSA.scr:78
    end -- ARG_YRSA.scr:79
    ctx:doRude(1) -- ARG_YRSA.scr:81
    do return ctx:exit("") end -- ARG_YRSA.scr:83
end

script.labels["Vanish"] = function(ctx)
    -- ARG_YRSA.scr:87
    -- play vanish effect here
    ctx:self():doClientFx("GreaterDemon") -- ARG_YRSA.scr:92
    ctx:playSound("\\Sounds\\magic\\Windup10.wav", "DoNothing", 100, 24000, "FALSE", 100) -- ARG_YRSA.scr:93
    ctx:wait(1, 1, "Vanish2b") -- ARG_YRSA.scr:94
    do return ctx:exit("") end -- ARG_YRSA.scr:95
end

script.labels["Vanish2b"] = function(ctx)
    -- ARG_YRSA.scr:98
    ctx:self():setFlag("visible", false) -- ARG_YRSA.scr:101
    ctx:playSound("\\Sounds\\magic\\teleport.wav", "DoNothing", 100, 24000, "FALSE", 100) -- ARG_YRSA.scr:102
    ctx:wait(1, 1, "Vanish2c") -- ARG_YRSA.scr:103
    do return ctx:exit("") end -- ARG_YRSA.scr:104
end

script.labels["Vanish2c"] = function(ctx)
    -- ARG_YRSA.scr:108
    ctx:self():remove() -- ARG_YRSA.scr:110
    do return ctx:exit("") end -- ARG_YRSA.scr:111
end

script.labels["Main"] = function(ctx)
    -- ARG_YRSA.scr:115
    -- traceon
    ctx:addTrigger("Appear", "OnAppear") -- ARG_YRSA.scr:119
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- ARG_YRSA.scr:120
    do return ctx:exit("") end -- ARG_YRSA.scr:121
end

return script
