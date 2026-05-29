-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ATLIWAGON.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- atliwagon.scr
-- timmy
-- handles The wagon appearing and summoning monsters when on the quest.
script.labels["summonatli"] = function(ctx)
    -- ATLIWAGON.scr:25
    if ctx:hasKey(197) then -- ATLIWAGON.scr:29-30
        ctx:object("atli"):trigger("summon") -- ATLIWAGON.scr:31-32
        ctx:giveKey(126) -- ATLIWAGON.scr:33
        do return ctx:exit("") end -- ATLIWAGON.scr:34
    end -- ATLIWAGON.scr:35
    do return ctx:exit("") end -- ATLIWAGON.scr:36
end

script.labels["Summonbandit"] = function(ctx)
    -- ATLIWAGON.scr:41
    if ctx:condition("bSpawned==TRUE") then -- ATLIWAGON.scr:44
        do return ctx:exit("") end -- ATLIWAGON.scr:45
    end -- ATLIWAGON.scr:46
    if not ctx:hasKey(197) then -- ATLIWAGON.scr:48-49
        do return ctx:exit("") end -- ATLIWAGON.scr:50
    end -- ATLIWAGON.scr:51
    -- spawn bandits at marker
    ctx:state().SCRIPT = " ScriptName BanditAttack.scr" -- ATLIWAGON.scr:55
    ctx:state().bSpawned = true -- ATLIWAGON.scr:56
    ctx:set("sMonsterA", "sMonsterA + Script") -- ATLIWAGON.scr:58
    ctx:set("sMonsterB", "sMonsterB + Script") -- ATLIWAGON.scr:59
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("SpawnMarker"):pos() -- ATLIWAGON.scr:61-62
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterA") -- ATLIWAGON.scr:63
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterA") -- ATLIWAGON.scr:64
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterA") -- ATLIWAGON.scr:65
    ctx:state().hMonsterB = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterB") -- ATLIWAGON.scr:66
    ctx:state().hMonsterB = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterB") -- ATLIWAGON.scr:67
    ctx:state().hMonsterB = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterB") -- ATLIWAGON.scr:68
    do return ctx:exit("") end -- ATLIWAGON.scr:69
end

script.labels["Init"] = function(ctx)
    -- ATLIWAGON.scr:72
    if ctx:hasKey(127) then -- ATLIWAGON.scr:77-78
        ctx:self():remove() -- ATLIWAGON.scr:82
    else -- ATLIWAGON.scr:85
        ctx:atTime(6, 0, "summonatli", "summonatli") -- ATLIWAGON.scr:88
        ctx:atTime(3, 30, "Summonbandit", "summonbandit") -- ATLIWAGON.scr:89
    end -- ATLIWAGON.scr:92
    do return ctx:exit("") end -- ATLIWAGON.scr:93
end

script.labels["Main"] = function(ctx)
    -- ATLIWAGON.scr:97
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onEvent("OnPostStartWorld", "Init") -- ATLIWAGON.scr:104
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- ATLIWAGON.scr:105
    ctx:onEvent("OnPostSaveLoad", "Init") -- ATLIWAGON.scr:106
    ctx:wait(1, .5, "Init") -- ATLIWAGON.scr:107
    do return ctx:exit("") end -- ATLIWAGON.scr:108
end

return script
