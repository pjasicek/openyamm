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
askPasswordDoor(61, 61, darkPrompt, {
    "dark", "darkness",
    "тьма", "Тьма", "ТЬМА",
    "темнота", "Темнота", "ТЕМНОТА",
    "тёмнота", "Тёмнота", "ТЁМНОТА",
})

askPasswordDoor(
    62,
    62,
    "\"I go through an apple, or point out your way, I fit in a bow, then a target, to stay. What am I?\"",
    {"arrow", "an arrow", "стрела", "Стрела", "СТРЕЛА"})

local timePrompt =
    "\"What consumes rocks, levels mountains, destroys wood, pushes the clouds across the sky, " ..
    "and can make a young one old?\""
askPasswordDoor(63, 63, timePrompt, {"time", "время", "Время", "ВРЕМЯ"})

local fishPrompt =
    "\"Alive without breath, as cold as death, never thirsty ever drinking, all in mail never clinking, " ..
    "ever travelling, never walking, mouth ever moving, never talking.  What am I? \""
askPasswordDoor(64, 64, fishPrompt, {"fish", "a fish", "рыба", "Рыба", "РЫБА"})
