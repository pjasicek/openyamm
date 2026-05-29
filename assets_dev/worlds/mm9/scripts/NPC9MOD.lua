-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC9MOD.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 6, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 7, path = "ListTraverse.inc" }

-- NPC9.scr
-- sean
-- handles Ketil Strongpick's voice and quest stuff.
script.labels["Main"] = function(ctx)
    -- NPC9MOD.scr:18
    ctx:getParam(0, "LISTNAME") -- NPC9MOD.scr:20
    ctx:getParam(1, "LISTFIRST") -- NPC9MOD.scr:21
    ctx:getParam(2, "LISTLAST") -- NPC9MOD.scr:22
    ctx:wait(0, 1, "InitNPC9") -- NPC9MOD.scr:24
    do return ctx:exit("TRUE") end -- NPC9MOD.scr:26
end

script.labels["InitNPC9"] = function(ctx)
    -- NPC9MOD.scr:29
    ctx:self():attachProp("models\\MonkHammer.ABC", "skins\\MonkHammer.dtx", "RHand1", ctx:object("hDummy")) -- NPC9MOD.scr:31
    mm9.gosub(script, ctx, "SetTraverseWalk") -- NPC9MOD.scr:33
    mm9.gosub(script, ctx, "SetTraverseOnce") -- NPC9MOD.scr:34
    ctx:state().TRAVERSERADIUS = 10 -- NPC9MOD.scr:35
    ctx:onRudeExit("OnRudeExit", script.labels["OnRudeExit"]) -- NPC9MOD.scr:37
    ctx:onEvent("OnDamage", "OnDamage") -- NPC9MOD.scr:38
    do return ctx:exit("TRUE") end -- NPC9MOD.scr:40
end

script.labels["OnTargetWithinDist"] = function(ctx)
    -- NPC9MOD.scr:43
    mm9.gosub(script, ctx, "TraverseResume") -- NPC9MOD.scr:45
    ctx:self():setTarget(ctx:player()) -- NPC9MOD.scr:46
    ctx:onEvent("OnTargetBeyondDist", "WAIT_DISTANCE", "OnTargetBeyondDist") -- NPC9MOD.scr:47
    do return ctx:exit("TRUE") end -- NPC9MOD.scr:49
end

script.labels["OnTargetBeyondDist"] = function(ctx)
    -- NPC9MOD.scr:52
    mm9.gosub(script, ctx, "TraversePause") -- NPC9MOD.scr:54
    ctx:self():setTarget(ctx:player()) -- NPC9MOD.scr:55
    ctx:onEvent("OnTargetWithinDist", "RESUME_DISTANCE", "OnTargetWithinDist") -- NPC9MOD.scr:56
    do return ctx:exit("TRUE") end -- NPC9MOD.scr:58
end

script.labels["OnRudeExit"] = function(ctx)
    -- NPC9MOD.scr:61
    ctx:hasKey(9509, "bHasKey") -- NPC9MOD.scr:63
    if ctx:condition("bHasKey==TRUE") then -- NPC9MOD.scr:64
        ctx:self():setTarget(ctx:player()) -- NPC9MOD.scr:66
        ctx:addTrigger("use", "TraverseResume") -- NPC9MOD.scr:67
        mm9.gosub(script, ctx, "TraverseBegin") -- NPC9MOD.scr:68
    end -- NPC9MOD.scr:69
    do return ctx:exit("TRUE") end -- NPC9MOD.scr:71
end

script.labels["OnTraverseDone"] = function(ctx)
    -- NPC9MOD.scr:74
    if ctx:condition("LISTINDEX==LISTLAST") then -- NPC9MOD.scr:76
        mm9.gosub(script, ctx, "TraversePause") -- NPC9MOD.scr:77
    end -- NPC9MOD.scr:78
    do return ctx:exit("TRUE") end -- NPC9MOD.scr:80
end

script.labels["OnDamage"] = function(ctx)
    -- NPC9MOD.scr:83
    mm9.gosub(script, ctx, "TraversePause") -- NPC9MOD.scr:85
    do return ctx:exit("TRUE") end -- NPC9MOD.scr:87
end

return script
