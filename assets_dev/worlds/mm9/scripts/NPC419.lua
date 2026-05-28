-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC419.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC419.scr
-- timmy
-- handles Aymril Banito voice and quest stuff
script.labels["OnRude"] = function(ctx)
    -- NPC419.scr:14
    -- traceon
    if ctx:hasKey(5004) then -- NPC419.scr:19-20
        ctx:giveKey(5005) -- NPC419.scr:21
        ctx:command("wait", "1 1 StartUnlock") -- NPC419.scr:22
        -- goto unlock
        do return ctx:exit("") end -- NPC419.scr:24
    else -- NPC419.scr:25
        -- CALL GUARDS
        mm9.gosub(script, ctx, "Call") -- NPC419.scr:27
        ctx:command("traceoff", "") -- NPC419.scr:28
        do return ctx:exit("") end -- NPC419.scr:29
    end -- NPC419.scr:30
    do return ctx:exit("") end -- NPC419.scr:32
end

script.labels["StartUnlock"] = function(ctx)
    -- NPC419.scr:35
    ctx:command("getobjecthandle", "CookMarker g_hobject") -- NPC419.scr:38
    ctx:command("walkto", "g_hobject 32 Unlock") -- NPC419.scr:39
    do return ctx:exit("") end -- NPC419.scr:40
end

script.labels["Unlock"] = function(ctx)
    -- NPC419.scr:43
    ctx:command("getobjecthandle", "Celldoor29 g_hobject") -- NPC419.scr:47
    ctx:trigger("g_hobject", "unlock") -- NPC419.scr:48
    ctx:command("wait", "1 1 walkaway") -- NPC419.scr:49
end

script.labels["WalkAway"] = function(ctx)
    -- NPC419.scr:52
    ctx:command("getobjecthandle", "CookMarker0 g_hobject") -- NPC419.scr:55
    ctx:command("walkto", "g_hobject 32 DoNothing") -- NPC419.scr:56
    do return ctx:exit("") end -- NPC419.scr:57
end

script.labels["Call"] = function(ctx)
    -- NPC419.scr:60
    ctx:giveKey(5006) -- NPC419.scr:63
    ctx:command("getobjecthandle", "Help1 g_hobject") -- NPC419.scr:66
    ctx:trigger("g_hobject", "help") -- NPC419.scr:67
    ctx:command("getobjecthandle", "Help2 g_hobject") -- NPC419.scr:69
    ctx:trigger("g_hobject", "help") -- NPC419.scr:70
    ctx:command("getobjecthandle", "Help3 g_hobject") -- NPC419.scr:72
    ctx:trigger("g_hobject", "help") -- NPC419.scr:73
    do return ctx:exit("") end -- NPC419.scr:74
end

script.labels["OnExit"] = function(ctx)
    -- NPC419.scr:76
    do return ctx:exit("") end -- NPC419.scr:79
end

script.labels["DoRude"] = function(ctx)
    -- NPC419.scr:82
    ctx:command("stop", "") -- NPC419.scr:85
    ctx:doRude(419) -- NPC419.scr:86
    do return ctx:exit("") end -- NPC419.scr:87
end

script.labels["OnTarget"] = function(ctx)
    -- NPC419.scr:90
    ctx:getParam(0, "g_hplayer") -- NPC419.scr:93
    ctx:command("target", "g_hplayer") -- NPC419.scr:94
    ctx:command("ontargetwithindist", "16 DoRude") -- NPC419.scr:95
    if ctx:hasKey(5004) then -- NPC419.scr:96-97
        do return ctx:exit("") end -- NPC419.scr:98
    end -- NPC419.scr:99
    ctx:hasKey(5006, "g_btemp") -- NPC419.scr:100
    if ctx:condition("g_ntemp==TRUE") then -- NPC419.scr:101
        do return ctx:exit("") end -- NPC419.scr:102
    end -- NPC419.scr:103
    ctx:command("walkto", "g_hplayer 8 DoNothing") -- NPC419.scr:105
    do return ctx:exit("") end -- NPC419.scr:106
end

script.labels["Main"] = function(ctx)
    -- NPC419.scr:111
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC419.scr:118
    ctx:command("onfoundplayer", "OnTarget 256") -- NPC419.scr:119
    if ctx:hasKey(5005) then -- NPC419.scr:120-121
        ctx:command("getobjecthandle", "Celldoor29 g_hobject") -- NPC419.scr:122
        ctx:trigger("g_hobject", "unlock") -- NPC419.scr:123
    else -- NPC419.scr:124
        ctx:command("getobjecthandle", "Celldoor29 g_hobject") -- NPC419.scr:125
        ctx:trigger("g_hobject", "lock") -- NPC419.scr:126
        do return ctx:exit("") end -- NPC419.scr:127
    end -- NPC419.scr:128
    do return ctx:exit("") end -- NPC419.scr:130
end

return script
