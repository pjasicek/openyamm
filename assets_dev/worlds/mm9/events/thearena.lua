-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "thearena"
map.scripts = {}

map.scripts["arena.scr"] = {
    source = "ARENA.scr",
    registered_triggers = {
        { line = 621, message = "Arrive", callback = "OnArrive" },
        { line = 622, message = "Pick", callback = "Init" },
        { line = 623, message = "MonsterA", callback = "OnMonsterA" },
        { line = 624, message = "MonsterB", callback = "OnMonsterB" },
        { line = 625, message = "WinMonsterA", callback = "OnMonsterAWin" },
        { line = 626, message = "WinMonsterB", callback = "OnMonsterBWin" },
        { line = 627, message = "Fight", callback = "OnWatch" },
        { line = 628, message = "Lord", callback = "OnLord" },
        { line = 629, message = "IDied", callback = "OnMonsterDead" },
    },
    movement_commands = {
    },
}
map.scripts["arenafight.scr"] = {
    source = "ARENAFIGHT.scr",
    registered_triggers = {
        { line = 556, message = "Dead", callback = "OnDead" },
        { line = 557, message = "Hello", callback = "OnHello" },
        { line = 558, message = "Page", callback = "OnPage" },
        { line = 559, message = "Squire", callback = "OnSquire" },
        { line = 560, message = "Knight", callback = "OnKnight" },
        { line = 561, message = "Lord", callback = "OnLord" },
        { line = 562, message = "PlayerInTheHouse", callback = "OnPlayerInTheHouse" },
    },
    movement_commands = {
    },
}
map.scripts["npc245.scr"] = {
    source = "NPC245.scr",
    registered_triggers = {
        { line = 88, message = "Use", callback = "OnUse" },
        { line = 89, message = "Enter", callback = "OnEnter" },
    },
    movement_commands = {
    },
}
map.scripts["propanim.scr"] = {
    source = "PROPANIM.scr",
    registered_triggers = {
        { line = 42, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["svenarena.scr"] = {
    source = "SVENARENA.scr",
    registered_triggers = {
        { line = 150, message = "Walk", callback = "OnWalk" },
        { line = 151, message = "use", callback = "OnUse" },
        { line = 152, message = "Guard", callback = "OnGuard" },
    },
    movement_commands = {
    },
}

function map.register(ctx)
    if ctx == nil or ctx.registerMm9MapEvents == nil then
        return
    end
    ctx:registerMm9MapEvents(map)
end

return map
