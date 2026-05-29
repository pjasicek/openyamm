-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "PIGRACERAI.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "ListTraverse.inc" }

-- PigRacer.scr
-- by SJR
-- 12-11-01
-- Purpose:player races against this pig
-- during Thjorgard races.
script.labels["Main"] = function(ctx)
    -- PIGRACERAI.scr:17
    ctx:getParam(0, "LISTNAME") -- PIGRACERAI.scr:19
    ctx:getParam(1, "LISTFIRST") -- PIGRACERAI.scr:20
    ctx:getParam(2, "LISTLAST") -- PIGRACERAI.scr:21
    ctx:wait(0, 3, "InitPigRacerAI") -- PIGRACERAI.scr:23
    do return ctx:exit("TRUE") end -- PIGRACERAI.scr:25
end

script.labels["InitPigRacerAI"] = function(ctx)
    -- PIGRACERAI.scr:28
    ctx:randomInt(5, 8, "nRandom") -- PIGRACERAI.scr:32
    ctx:state().nTemp = ctx:self():getStat("RunVel") -- PIGRACERAI.scr:33
    ctx:set("nTemp", "nTemp * nRandom") -- PIGRACERAI.scr:34
    ctx:self():setStat("RunVel", "nTemp") -- PIGRACERAI.scr:35
    mm9.gosub(script, ctx, "SetTraverseRun") -- PIGRACERAI.scr:37
    mm9.gosub(script, ctx, "SetTraverseOnce") -- PIGRACERAI.scr:38
    ctx:state().TRAVERSERADIUS = 64 -- PIGRACERAI.scr:39
    ctx:addTrigger("Start", "TraverseBegin") -- PIGRACERAI.scr:41
    ctx:self():setIdle() -- PIGRACERAI.scr:43
    do return ctx:exit("TRUE") end -- PIGRACERAI.scr:45
end

script.labels["OnTraverseDone"] = function(ctx)
    -- PIGRACERAI.scr:48
    if ctx:condition("LISTINDEX==LISTLAST") then -- PIGRACERAI.scr:50
        mm9.gosub(script, ctx, "TraversePause") -- PIGRACERAI.scr:51
        mm9.gosub(script, ctx, "ReversePath") -- PIGRACERAI.scr:52
        mm9.gosub(script, ctx, "TraverseResume") -- PIGRACERAI.scr:53
    end -- PIGRACERAI.scr:54
    do return ctx:exit("TRUE") end -- PIGRACERAI.scr:56
end

return script
