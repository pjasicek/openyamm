-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "STURMGUARD.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- Sturmguard.scr
-- 10/4
-- timmy
-- gives party specific item
-- Parameters
-- P0 Item number of item to give
script.labels["OnUse"] = function(ctx)
    -- STURMGUARD.scr:26
    ctx:giveKey(5008) -- STURMGUARD.scr:29
    ctx:doRude(425) -- STURMGUARD.scr:30
    do return ctx:exit("") end -- STURMGUARD.scr:31
end

script.labels["OnRude"] = function(ctx)
    -- STURMGUARD.scr:34
    ctx:takeKey(5008) -- STURMGUARD.scr:37
    if ctx:hasKey(5019) then -- STURMGUARD.scr:39-40
        ctx:takeKey(5018) -- STURMGUARD.scr:41
        ctx:takeKey(5019) -- STURMGUARD.scr:42
        ctx:command("getobjecthandle", "Jaildoor g_hobject") -- STURMGUARD.scr:43
        ctx:trigger("g_hobject", "close") -- STURMGUARD.scr:44
        ctx:trigger("g_hobject", "lock") -- STURMGUARD.scr:45
    end -- STURMGUARD.scr:46
    if ctx:hasKey(5018) then -- STURMGUARD.scr:48-49
        ctx:command("getobjecthandle", "Jaildoor g_hobject") -- STURMGUARD.scr:50
        ctx:trigger("g_hobject", "unlock") -- STURMGUARD.scr:51
        ctx:trigger("g_hobject", "open") -- STURMGUARD.scr:52
    end -- STURMGUARD.scr:53
    if ctx:hasKey(5009) then -- STURMGUARD.scr:57-58
        do return ctx:exit("") end -- STURMGUARD.scr:59
    end -- STURMGUARD.scr:60
    -- open the door for hatlati
    if ctx:hasKey(154) then -- STURMGUARD.scr:63-64
        ctx:command("getobjecthandle", "Hatlati g_hobject") -- STURMGUARD.scr:65
        ctx:trigger("g_hobject", "GotoJail") -- STURMGUARD.scr:66
        ctx:command("getobjecthandle", "Jaildoor g_hobject") -- STURMGUARD.scr:67
        ctx:trigger("g_hobject", "unlock") -- STURMGUARD.scr:68
        ctx:trigger("g_hobject", "open") -- STURMGUARD.scr:69
        do return ctx:exit("") end -- STURMGUARD.scr:70
    end -- STURMGUARD.scr:71
    do return ctx:exit("") end -- STURMGUARD.scr:72
end

script.labels["Main"] = function(ctx)
    -- STURMGUARD.scr:75
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Use", "OnUse") -- STURMGUARD.scr:80
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- STURMGUARD.scr:81
    do return ctx:exit("") end -- STURMGUARD.scr:82
end

return script
