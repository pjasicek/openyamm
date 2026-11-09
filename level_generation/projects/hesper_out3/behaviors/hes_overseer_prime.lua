-- The Overseer Primes of the Brood Spires call hatchlings, not Drudges (BROOD_SPIRES.md section 7, MONSTERS' families
-- pass): at 66 % and 33 % health each summons two Hatchlings (10003) within 400. Bound per actor by the map's load
-- event, so the Primes elsewhere keep their own.
local function call(self)
    self:summon(10003, 2, 400)
    self:say('The Overseer shrieks; hatchlings answer from the creep.')
end
return Behavior.define{
    onHealthBelow = {[0.66] = call, [0.33] = call},
}
