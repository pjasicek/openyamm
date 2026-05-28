-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BC_MONSTERFIGHT.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "BaseGlobals.inc" }

-- BC_MonsterFight.scr
-- by SJR
-- Purpose:two monsters duke it out
-- to show the player a fight
script.labels["Main"] = function(ctx)
    -- BC_MONSTERFIGHT.scr:14
    ctx:command("wait", "0, .1, InitMonsterFight") -- BC_MONSTERFIGHT.scr:16
    ctx:command("getmyhandle", "hMe") -- BC_MONSTERFIGHT.scr:18
    do return ctx:exit("TRUE") end -- BC_MONSTERFIGHT.scr:20
end

script.labels["InitMonsterFight"] = function(ctx)
    -- BC_MONSTERFIGHT.scr:23
    ctx:command("setstat", "hMe, GaveTreasure, TRUE") -- BC_MONSTERFIGHT.scr:25
    ctx:command("addfriend", "Player") -- BC_MONSTERFIGHT.scr:27
    ctx:command("addenemy", "AIBase") -- BC_MONSTERFIGHT.scr:28
    mm9.gosub(script, ctx, "SetupFighting") -- BC_MONSTERFIGHT.scr:30
    ctx:command("ondamage", "StartFighting") -- BC_MONSTERFIGHT.scr:32
    do return ctx:exit("TRUE") end -- BC_MONSTERFIGHT.scr:34
end

script.labels["SetupFighting"] = function(ctx)
    -- BC_MONSTERFIGHT.scr:37
    ctx:command("isclass", "hMe, \"EvilSorcerer\", bIsClass") -- BC_MONSTERFIGHT.scr:39
    if ctx:condition("bIsClass==TRUE") then -- BC_MONSTERFIGHT.scr:40
        ctx:command("facedir", "1,0,0, 180, StartFighting") -- BC_MONSTERFIGHT.scr:41
    else -- BC_MONSTERFIGHT.scr:42
        ctx:command("isclass", "hMe, \"Oculus\", bIsClass") -- BC_MONSTERFIGHT.scr:43
        if ctx:condition("bIsClass==TRUE") then -- BC_MONSTERFIGHT.scr:44
            ctx:command("facedir", "-1,0,0, 180, StartFighting") -- BC_MONSTERFIGHT.scr:45
        end -- BC_MONSTERFIGHT.scr:46
    end -- BC_MONSTERFIGHT.scr:47
    do return ctx:exit("TRUE") end -- BC_MONSTERFIGHT.scr:49
end

script.labels["StartFighting"] = function(ctx)
    -- BC_MONSTERFIGHT.scr:52
    ctx:command("isclass", "hMe, \"EvilSorcerer\", bIsClass") -- BC_MONSTERFIGHT.scr:54
    if ctx:condition("bIsClass==TRUE") then -- BC_MONSTERFIGHT.scr:55
        ctx:command("runscript", "\"EvilSorcerer.scr\"") -- BC_MONSTERFIGHT.scr:56
    else -- BC_MONSTERFIGHT.scr:57
        ctx:command("isclass", "hMe, \"Oculus\", bIsClass") -- BC_MONSTERFIGHT.scr:58
        if ctx:condition("bIsClass==TRUE") then -- BC_MONSTERFIGHT.scr:59
            ctx:command("runscript", "\"FlyRange.scr\"") -- BC_MONSTERFIGHT.scr:60
        end -- BC_MONSTERFIGHT.scr:61
    end -- BC_MONSTERFIGHT.scr:62
    do return ctx:exit("TRUE") end -- BC_MONSTERFIGHT.scr:64
end

return script
