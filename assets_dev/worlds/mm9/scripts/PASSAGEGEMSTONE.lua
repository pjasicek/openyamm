-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "PASSAGEGEMSTONE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "ListMaker.inc" }

-- PassageGemstone.scr
-- by SJR
-- 11-07-01
-- Purpose:shoot the light that
-- fuels the mirror puzzle
script.labels["Main"] = function(ctx)
    -- PASSAGEGEMSTONE.scr:16
    ctx:getParam(0, "LISTNAME") -- PASSAGEGEMSTONE.scr:18
    ctx:getParam(1, "LISTFIRST") -- PASSAGEGEMSTONE.scr:19
    ctx:getParam(2, "LISTLAST") -- PASSAGEGEMSTONE.scr:20
    ctx:onEvent("OnPostStartWorld", "InitPassageGemstone") -- PASSAGEGEMSTONE.scr:22
    ctx:onEvent("OnCacheFiles", "CacheFiles") -- PASSAGEGEMSTONE.scr:23
    do return ctx:exit("TRUE") end -- PASSAGEGEMSTONE.scr:25
end

script.labels["CacheFiles"] = function(ctx)
    -- PASSAGEGEMSTONE.scr:28
    ctx:cacheSound("sounds\\spells\\enchantitem.wav") -- PASSAGEGEMSTONE.scr:30
    ctx:cacheSound("sounds\\door\\doorslidestone.wav") -- PASSAGEGEMSTONE.scr:31
    do return ctx:exit("TRUE") end -- PASSAGEGEMSTONE.scr:33
end

script.labels["InitPassageGemstone"] = function(ctx)
    -- PASSAGEGEMSTONE.scr:36
    ctx:addTrigger("use", "ShineLight") -- PASSAGEGEMSTONE.scr:38
    ctx:addTrigger("trigger", "ReleaseMonsters") -- PASSAGEGEMSTONE.scr:39
    ctx:state().hMirror = ctx:objectOrNil("Mirror0") -- PASSAGEGEMSTONE.scr:41
    ctx:state().hLaser = ctx:objectOrNil("GemLight0") -- PASSAGEGEMSTONE.scr:42
    do return ctx:exit("TRUE") end -- PASSAGEGEMSTONE.scr:44
end

script.labels["ReleaseMonsters"] = function(ctx)
    -- PASSAGEGEMSTONE.scr:47
    ctx:removeTrigger("release") -- PASSAGEGEMSTONE.scr:49
    ctx:playSound("sounds\\spells\\enchantitem.wav", "SoundCallback", 1, 1000, "FALSE", 100) -- PASSAGEGEMSTONE.scr:51
    mm9.gosub(script, ctx, "GetFirstObject") -- PASSAGEGEMSTONE.scr:53
    while ctx:condition("LISTINDEX<LISTLAST") do -- PASSAGEGEMSTONE.scr:54
        ctx:trigger("LISTOBJECT", "go") -- PASSAGEGEMSTONE.scr:55
        mm9.gosub(script, ctx, "GetNextObject") -- PASSAGEGEMSTONE.scr:56
    end -- PASSAGEGEMSTONE.scr:57
    ctx:trigger("LISTOBJECT", "go") -- PASSAGEGEMSTONE.scr:58
    local object = ctx:object("DesertDoor0") -- PASSAGEGEMSTONE.scr:60
    object:trigger("unlock") -- PASSAGEGEMSTONE.scr:61
    object:trigger("open") -- PASSAGEGEMSTONE.scr:62
    do return ctx:exit("TRUE") end -- PASSAGEGEMSTONE.scr:64
end

script.labels["SoundCallback"] = function(ctx)
    -- PASSAGEGEMSTONE.scr:67
    ctx:playSound("sounds\\door\\doorslidestone.wav", "DoNothing", 1, 1000, "FALSE", 100) -- PASSAGEGEMSTONE.scr:69
    do return ctx:exit("TRUE") end -- PASSAGEGEMSTONE.scr:71
end

script.labels["ShineLight"] = function(ctx)
    -- PASSAGEGEMSTONE.scr:74
    mm9.gosub(script, ctx, "RemoveInterface") -- PASSAGEGEMSTONE.scr:76
    if ctx:condition("hLight!=0") then -- PASSAGEGEMSTONE.scr:78
        ctx:trigger("hLaser", "shoot") -- PASSAGEGEMSTONE.scr:79
    end -- PASSAGEGEMSTONE.scr:80
    if ctx:condition("hMirror!=0") then -- PASSAGEGEMSTONE.scr:82
        ctx:trigger("hMirror", "trigger") -- PASSAGEGEMSTONE.scr:83
    end -- PASSAGEGEMSTONE.scr:84
    ctx:wait(0, 1, "RestoreInterface") -- PASSAGEGEMSTONE.scr:86
    do return ctx:exit("TRUE") end -- PASSAGEGEMSTONE.scr:88
end

script.labels["RemoveInterface"] = function(ctx)
    -- PASSAGEGEMSTONE.scr:91
    ctx:removeTrigger("use") -- PASSAGEGEMSTONE.scr:93
    do return ctx:exit("TRUE") end -- PASSAGEGEMSTONE.scr:95
end

script.labels["RestoreInterface"] = function(ctx)
    -- PASSAGEGEMSTONE.scr:98
    ctx:addTrigger("use", "ShineLight") -- PASSAGEGEMSTONE.scr:100
    do return ctx:exit("TRUE") end -- PASSAGEGEMSTONE.scr:102
end

return script
