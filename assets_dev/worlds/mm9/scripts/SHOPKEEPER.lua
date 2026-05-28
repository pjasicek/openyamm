-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SHOPKEEPER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "BaseWander.inc" }

-- shopkeeper.scr
-- timmy
-- handles shopkeeper voice and anims
-- edited by Bones -- 6/10/03
-- TELP Patch 1.3 -- Thjorgard captain won't fall into water
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnUse"] = function(ctx)
    -- SHOPKEEPER.scr:25
    ctx:command("playsound", "sound, Onexit, 100, 240, FALSE, 100") -- SHOPKEEPER.scr:28
    do return ctx:exit("") end -- SHOPKEEPER.scr:29
end

script.labels["OnExit"] = function(ctx)
    -- SHOPKEEPER.scr:32
    do return ctx:exit("") end -- SHOPKEEPER.scr:35
end

script.labels["Main"] = function(ctx)
    -- SHOPKEEPER.scr:38
    -- traceon
    -- Don't Forget to Delete this!
    ctx:getParam(0, "sound") -- SHOPKEEPER.scr:44
    ctx:getParam(1, "Params") -- SHOPKEEPER.scr:45
    ctx:getParam(2, "g_ntemp") -- SHOPKEEPER.scr:46
    -- LoopAnim Params,g_ntemp DoNothing
    ctx:addTrigger("Use", "OnUse") -- SHOPKEEPER.scr:50
    -- jsl-->Wander if we're setup to..
    mm9.gosub(script, ctx, "BaseWanderInit") -- SHOPKEEPER.scr:53
    do return ctx:exit("") end -- SHOPKEEPER.scr:55
end

script.labels["BaseWanderInit"] = function(ctx)
    -- SHOPKEEPER.scr:58
    -- overloaded -- Bones
    ctx:command("getmyhandle", "g_hMyObject") -- SHOPKEEPER.scr:62
    ctx:command("getobjectname", "g_hMyObject g_sPad1") -- SHOPKEEPER.scr:63
    if ctx:condition("g_sPad1 == JohnGoodman") then -- SHOPKEEPER.scr:64
        if ctx:condition("g_nPad2 == 0") then -- SHOPKEEPER.scr:65
            ctx:command("onpostsaveload", "BaseWanderInit") -- SHOPKEEPER.scr:66
            ctx:command("onpostminisaveload", "BaseWanderInit") -- SHOPKEEPER.scr:67
            ctx:command("set", "g_nPad2 1") -- SHOPKEEPER.scr:68
        else -- SHOPKEEPER.scr:69
            ctx:command("setpos", "g_hMyObject -6415 544 4768") -- SHOPKEEPER.scr:70
            do return ctx:exit("") end -- SHOPKEEPER.scr:71
        end -- SHOPKEEPER.scr:72
    end -- SHOPKEEPER.scr:73
    do return mm9.gotoLabel(script, ctx, "BaseWanderInit") end -- SHOPKEEPER.scr:74
end

return script
