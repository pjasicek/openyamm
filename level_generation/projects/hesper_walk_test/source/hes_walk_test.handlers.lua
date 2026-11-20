-- Authored walkability test room behaviour. build_walk_test.py embeds this file after its generated tables and before
-- the registrations. The room's own events: the map load, and the engine checks of engine_calls.yml (events 101-106,
-- each recording its result in a named map variable).
local handlers = {}

handlers[1] = function()
end

local function record(name, value)
    evt.SetMapVar(name, value and 1 or 0)
end

-- A 500 gold heap on the platform (evt.SummonGold).
RegisterEvent(101, "Engine check: gold", function()
    record("check.gold", evt.SummonGold(500, 1000, 1700, 96))
end, "Engine check: gold")

-- The room's first actor turned to the party's side for good (evt.TurnActor).
RegisterEvent(102, "Engine check: turn", function()
    record("check.turn", evt.TurnActor(0))
end, "Engine check: turn")

-- Sight across the open floor, none through the floor (evt.LineOfSight), and the first actor seeing the party.
RegisterEvent(103, "Engine check: sight", function()
    local across = evt.LineOfSight(500, 500, 60, 1500, 500, 60)
    local throughFloor = evt.LineOfSight(500, 500, 60, 500, 500, -600)
    record("check.sight", across and not throughFloor)
    record("check.sees", evt.ActorSeesParty(0))
end, "Engine check: sight")

-- The active character spends an action (evt.SpendAction) and the first actor's position is read.
RegisterEvent(104, "Engine check: action", function()
    record("check.action", evt.SpendAction(3))
    local x = evt.GetMapActorPosition(0)
    record("check.position", x ~= nil)
end, "Engine check: action")

-- A world missile from the room's west end to its east end (evt.FireMissile) kills nothing it is not near.
RegisterEvent(105, "Engine check: missile", function()
    record("check.missile", evt.FireMissile("KrDart", 200, 800, 100, 2800, 800, 100, 50, "Energy", 300, 0.3))
end, "Engine check: missile")

-- A choice box (AskChoiceWithAnswerSteps): one dialog button per answer; Yes continues at step 1.
RegisterEvent(106, "Engine check: choice", function(step)
    if step == 1 or step == 2 then
        record("check.choice", step == 1)
        return
    end
    AskChoiceWithAnswerSteps(106, 0, "Open every collar?", {{Answer = "Yes", Step = 1}, {Answer = "No", Step = 2}})
end, "Engine check: choice")
