-- MMMerge map supplement: Shadow Guild password doors.

local function askPasswordDoor(eventId, doorId, prompt, answers)
    ReplaceMapEvent(eventId, "Magic Door", function(continueStep)
        if continueStep == 2 then
            evt.StatusText("Incorrect")
            return
        end

        if continueStep == 4 then
            evt.SetDoorState(doorId, DoorAction.Close)
            return
        end

        if continueStep ~= nil then
            return
        end

        evt.SimpleMessage(prompt)
        evt.AskQuestion(eventId, 2, 21, 4, 0, 0, "Answer?  ", answers)
        return nil
    end, "Magic Door")
end

local darkPrompt =
    "\"You cannot see me, hear me or touch me.  I lie behind the stars and alter what is real, " ..
    "I am what you really fear, Close your eyes and come I near. What am I?\""
askPasswordDoor(61, 61, darkPrompt, {"dark", "darkness"})

askPasswordDoor(
    62,
    62,
    "\"I go through an apple, or point out your way, I fit in a bow, then a target, to stay. What am I?\"",
    {"arrow", "an arrow"})

local timePrompt =
    "\"What consumes rocks, levels mountains, destroys wood, pushes the clouds across the sky, " ..
    "and can make a young one old?\""
askPasswordDoor(63, 63, timePrompt, {"time"})

local fishPrompt =
    "\"Alive without breath, as cold as death, never thirsty ever drinking, all in mail never clinking, " ..
    "ever travelling, never walking, mouth ever moving, never talking.  What am I? \""
askPasswordDoor(64, 64, fishPrompt, {"fish", "a fish"})

-- The on-load reset (original OnLoadMap, event 2) runs on every load, saves included, and clears the puzzle and the
-- genie gate. The original saves no face textures, so its blue gate screen and lit switch fell back to the map's own
-- art on a reload; OpenYAMM saves them, and after a reload the screen looked open but did nothing (GitHub issue #45).
-- Keep the original reset and put those two faces back to their map textures with it.
ReplaceMapEvent(2, nil, function()
    for mapVar = 2, 18 do
        SetValue(MapVar(mapVar), 0)
    end
    evt.SetDoorState(3, DoorAction.Close)
    evt.SetDoorState(4, DoorAction.Open)
    evt.SetDoorState(8, DoorAction.Open)
    evt.SetDoorState(1, DoorAction.Open)
    evt.SetDoorState(2, DoorAction.Open)
    evt.SetDoorState(11, DoorAction.Open)
    evt.SetDoorState(9, DoorAction.Open)
    evt.SetDoorState(5, DoorAction.Open)
    evt.SetDoorState(61, DoorAction.Open)
    evt.SetDoorState(62, DoorAction.Open)
    evt.SetDoorState(63, DoorAction.Open)
    evt.SetDoorState(64, DoorAction.Open)
    evt.SetTexture(-832, "t3s1off")
    evt.SetTexture(-1078, "d5walba")
end)
AppendMapOnLoadEvent(2) -- ReplaceMapEvent drops the event from the on-load list.
