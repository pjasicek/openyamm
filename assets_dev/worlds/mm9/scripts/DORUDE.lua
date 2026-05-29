-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DORUDE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "basemelee.inc" }

-- DoRude.scr
-- timmy
-- Does NPC Rude
-- 10/23
-- parameters:
-- p0 number of NPC to do
-- p1 the name of the sound to play.
-- p0 Whether they will turn hostile if attacked
script.labels["OnUse"] = function(ctx)
    -- DORUDE.scr:22
    if ctx:condition("attacked==false") then -- DORUDE.scr:25
        if ctx:condition("NPC_ID!=NULL") then -- DORUDE.scr:26
            ctx:self():stop() -- DORUDE.scr:27
            mm9.gosub(script, ctx, "BaseWanderStop") -- DORUDE.scr:28
            ctx:getParam(0, "g_hobject") -- DORUDE.scr:29
            ctx:self():faceObject(ctx:object("g_hobject"), 200, "DoNothing") -- DORUDE.scr:30
            ctx:doRude("NPC_ID") -- DORUDE.scr:31
            if ctx:condition("top_Blurb!=NULL") then -- DORUDE.scr:32
                ctx:playSound("Top_Blurb", "DoNothing", 100, 240, "FALSE", 100) -- DORUDE.scr:33
            end -- DORUDE.scr:34
            do return ctx:exit("") end -- DORUDE.scr:35
        end -- DORUDE.scr:37
    end -- DORUDE.scr:38
    do return ctx:exit("") end -- DORUDE.scr:39
end

script.labels["OnRude"] = function(ctx)
    -- DORUDE.scr:43
    mm9.gosub(script, ctx, "BaseWanderStart") -- DORUDE.scr:47
    do return ctx:exit("") end -- DORUDE.scr:48
end

script.labels["OnDamage"] = function(ctx)
    -- DORUDE.scr:52
    if ctx:condition("hostile==true") then -- DORUDE.scr:56
        ctx:state().Attacked = true -- DORUDE.scr:57
        mm9.gosub(script, ctx, "BaseInit") -- DORUDE.scr:58
    end -- DORUDE.scr:59
    do return ctx:exit("") end -- DORUDE.scr:60
end

script.labels["Main"] = function(ctx)
    -- DORUDE.scr:63
    -- TraceON
    mm9.gosub(script, ctx, "BaseWanderInit") -- DORUDE.scr:67
    ctx:getParam(0, "NPC_ID") -- DORUDE.scr:68
    ctx:getParam(1, "Top_Blurb") -- DORUDE.scr:69
    ctx:getParam(2, "Hostile") -- DORUDE.scr:70
    ctx:addTrigger("Use", "Onuse") -- DORUDE.scr:71
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- DORUDE.scr:72
    ctx:onEvent("OnDamage", "OnDamage") -- DORUDE.scr:73
    do return ctx:exit("") end -- DORUDE.scr:74
end

return script
