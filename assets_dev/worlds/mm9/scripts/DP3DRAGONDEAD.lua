-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DP3DRAGONDEAD.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- DP3Monsterdead.scr
-- timmy
-- Checks to see if both Monsters are dead in MonsterPharaoh2
-- Parameters:
-- p0   amount of monsters you want to check for dead
-- #NumberArray			MonsterArray[20]
script.labels["CheckAllMonsters"] = function(ctx)
    -- DP3DRAGONDEAD.scr:21
    ctx:state().Counter = (tonumber(ctx:state().Counter) or 0) + 1 -- DP3DRAGONDEAD.scr:27
    if ctx:condition("counter<DeadCount") then -- DP3DRAGONDEAD.scr:29
        do return ctx:exit("") end -- DP3DRAGONDEAD.scr:30
    end -- DP3DRAGONDEAD.scr:31
    -- ---Monsters are dead, now do this!!---
    ctx:object("Door13"):trigger("Open") -- DP3DRAGONDEAD.scr:35-36
    ctx:state().BeenDone = true -- DP3DRAGONDEAD.scr:37
    ctx:wait(0.2, 0.2, "killme") -- DP3DRAGONDEAD.scr:38
    do return ctx:exit("") end -- DP3DRAGONDEAD.scr:41
end

script.labels["killme"] = function(ctx)
    -- DP3DRAGONDEAD.scr:44
    ctx:exitScript() -- DP3DRAGONDEAD.scr:47
end

script.labels["Main"] = function(ctx)
    -- DP3DRAGONDEAD.scr:51
    ctx:getParam(0, "DeadCount") -- DP3DRAGONDEAD.scr:54
    ctx:addTrigger("MonsterDead", "CheckAllMonsters") -- DP3DRAGONDEAD.scr:56
    do return ctx:exit("") end -- DP3DRAGONDEAD.scr:58
end

return script
