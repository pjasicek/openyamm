-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DARKP_NPCDIE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 12, path = "Globals.inc" }

-- DarkP_NPCDie.scr
-- kd
-- 11-11-01
-- NPCAdventurer winces and dies
script.labels["Stop"] = function(ctx)
    -- DARKP_NPCDIE.scr:15
    do return ctx:exit("TRUE") end -- DARKP_NPCDIE.scr:17
end

script.labels["TakeHit"] = function(ctx)
    -- DARKP_NPCDIE.scr:19
    ctx:self():playAnimation("Wince1", "AnimateA") -- DARKP_NPCDIE.scr:21
    do return ctx:exit("TRUE") end -- DARKP_NPCDIE.scr:22
end

script.labels["AnimateA"] = function(ctx)
    -- DARKP_NPCDIE.scr:24
    ctx:self():playAnimation("Wince2", "Stop") -- DARKP_NPCDIE.scr:26
    do return ctx:exit("TRUE") end -- DARKP_NPCDIE.scr:27
end

script.labels["Main2"] = function(ctx)
    -- DARKP_NPCDIE.scr:29
    ctx:addTrigger("Wince", "TakeHit") -- DARKP_NPCDIE.scr:31
    ctx:addTrigger("destroy", "Die") -- DARKP_NPCDIE.scr:32
    -- SJR
    ctx:self():setStat("GaveTreasure", "TRUE") -- DARKP_NPCDIE.scr:36
    -- endSJR
    do return ctx:exit("TRUE") end -- DARKP_NPCDIE.scr:38
end

script.labels["Die"] = function(ctx)
    -- DARKP_NPCDIE.scr:40
    ctx:self():die() -- DARKP_NPCDIE.scr:42
    do return ctx:exit("tRUE") end -- DARKP_NPCDIE.scr:43
end

script.labels["Main"] = function(ctx)
    -- DARKP_NPCDIE.scr:45
    ctx:wait(0, 0.1, "Main2") -- DARKP_NPCDIE.scr:47
    do return ctx:exit("TRUE") end -- DARKP_NPCDIE.scr:48
end

return script
