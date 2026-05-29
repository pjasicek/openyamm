-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC189.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC189.scr
-- timmy
-- handles Fland de Allasan A'Lanth a'ryshar voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC189.scr:19
    mm9.gosub(script, ctx, "GreenMan") -- NPC189.scr:22
    do return ctx:exit("") end -- NPC189.scr:25
end

script.labels["GreenMan"] = function(ctx)
    -- NPC189.scr:29
    ctx:hasKey(263, "g_hobject") -- NPC189.scr:32
    if ctx:condition("g_hobject==FALSE") then -- NPC189.scr:33
        do return ctx:exit("") end -- NPC189.scr:34
    end -- NPC189.scr:35
    ctx:state().g_hobject = ctx:objectOrNil("GreenMan0") -- NPC189.scr:36
    ctx:self():walkTo(ctx:object("g_hobject"), 256, "DoNothing") -- NPC189.scr:37
    do return ctx:exit("") end -- NPC189.scr:38
end

script.labels["OnUse"] = function(ctx)
    -- NPC189.scr:44
    ctx:playSound("voices\\NPC\\NPC_189.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC189.scr:47
    do return ctx:exit("") end -- NPC189.scr:48
end

script.labels["OnExit"] = function(ctx)
    -- NPC189.scr:51
    do return ctx:exit("") end -- NPC189.scr:54
end

script.labels["Main"] = function(ctx)
    -- NPC189.scr:57
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC189.scr:64
    ctx:addTrigger("Use", "OnUse") -- NPC189.scr:66
    do return ctx:exit("") end -- NPC189.scr:68
end

return script
