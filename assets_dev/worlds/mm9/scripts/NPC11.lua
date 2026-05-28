-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC11.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC11.scr
-- timmy
-- handles shopkeeper voice and anims
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["Off"] = function(ctx)
    -- NPC11.scr:18
    ctx:command("debugout", "Done!!") -- NPC11.scr:22
    do return ctx:exit("") end -- NPC11.scr:23
end

-- Delete this when the script works the way it's supposed to!!!
script.labels["OnUse"] = function(ctx)
    -- NPC11.scr:28
    if ctx:hasItem(399) then -- NPC11.scr:31-32
        ctx:giveKey(1023) -- NPC11.scr:33
    end -- NPC11.scr:34
    ctx:command("playsound", "sound, DoNothing, 100, 240, FALSE, 100") -- NPC11.scr:35
    do return ctx:exit("") end -- NPC11.scr:36
end

script.labels["OnStart"] = function(ctx)
    -- NPC11.scr:39
    ctx:command("getobjecthandle", "CommonerDwarfMaleB4 g_hobject") -- NPC11.scr:42
    ctx:command("faceobject", "g_hobject 200 DoNothing") -- NPC11.scr:43
    -- LoopAnim conv1, 0 Donothing
    do return ctx:exit("") end -- NPC11.scr:45
end

script.labels["OnExit"] = function(ctx)
    -- NPC11.scr:49
    ctx:takeKey(1023) -- NPC11.scr:52
    do return ctx:exit("") end -- NPC11.scr:53
end

script.labels["Main"] = function(ctx)
    -- NPC11.scr:56
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnExit", script.labels["OnExit"]) -- NPC11.scr:61
    ctx:addTrigger("Use", "OnUse") -- NPC11.scr:62
    ctx:addTrigger("Talk", "OnStart") -- NPC11.scr:63
    ctx:getParam(0, "sound") -- NPC11.scr:64
    ctx:getParam(1, "Params") -- NPC11.scr:65
    ctx:getParam(2, "g_ntemp") -- NPC11.scr:66
    ctx:command("loopanim", "Params,g_ntemp Off") -- NPC11.scr:67
    do return ctx:exit("") end -- NPC11.scr:68
end

return script
