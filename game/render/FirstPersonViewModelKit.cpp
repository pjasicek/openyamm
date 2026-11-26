#include "game/render/FirstPersonViewModel.h"

#include <cmath>

// The first-person arms' pure rules (which kit the hands hold, the combo's blows), apart from the renderer so the unit
// tests compile them alone.
namespace OpenYAMM::Game
{
namespace
{
// Party speed (units per second, smoothed) above which a power attack follows the direction of movement; as
// FirstPersonViewModel.cpp's walk threshold.
constexpr float DirectionalPowerSpeed = 60.0f;
}

FirstPersonViewModel::Kit FirstPersonViewModel::kitFor(const std::string &skillGroup, bool twoHanded)
{
    Kit kit;
    if (skillGroup == "Sword")
    {
        kit.set = twoHanded ? WeaponSet::TwoHand : WeaponSet::OneHand;
        kit.weapon = twoHanded ? "w_claymore.glb" : "w_longsword.glb";
    }
    else if (skillGroup == "Axe")
    {
        kit.set = twoHanded ? WeaponSet::TwoHand : WeaponSet::OneHand;
        kit.weapon = twoHanded ? "w_battleaxe.glb" : "w_waraxe.glb";
    }
    else if (skillGroup == "Mace")
    {
        kit.set = twoHanded ? WeaponSet::TwoHand : WeaponSet::OneHand;
        kit.weapon = twoHanded ? "w_warhammer.glb" : "w_mace.glb";
    }
    else if (skillGroup == "Dagger")
    {
        kit.set = WeaponSet::OneHand;
        kit.weapon = "w_dagger.glb";
    }
    else if (skillGroup == "Club")
    {
        // A two-handed club (U-16: Xeen's Slayer Sword is a Weapon2 Club) is swung as a two-handed mace.
        kit.set = twoHanded ? WeaponSet::TwoHand : WeaponSet::OneHand;
        kit.weapon = twoHanded ? "w_warhammer.glb" : "w_mace.glb";
    }
    else if (skillGroup == "Blaster" || skillGroup == "Misc")
    {
        // A blaster or a wand: held in the right hand (our model only; Oblivion has none, so the template is bare).
        kit.set = WeaponSet::OneHand;
    }
    else if (skillGroup == "Spear" || skillGroup == "Staff")
    {
        // Oblivion's staff clips cast spells; a staff fights with the two-handed (blunt) set, held near its butt like
        // a claymore's hilt (w_staff_grip.glb: the staff moved 55 units up its shaft; gripped at the middle the shaft
        // ran back through the camera). A spear whose held.yml kind is known gets the pole set (kitForHeldKind);
        // without one it is held as a staff.
        kit.set = WeaponSet::TwoHand;
        kit.weapon = "w_staff_grip.glb";
    }
    else if (skillGroup == "Bow")
    {
        kit.set = WeaponSet::Bow;
        kit.weapon = "w_bow.glb";
    }
    return kit;
}

bool FirstPersonViewModel::dualWieldable(const std::string &skillGroup)
{
    return skillGroup == "Sword" || skillGroup == "Dagger" || skillGroup == "Axe" || skillGroup == "Mace"
        || skillGroup == "Club";
}

FirstPersonViewModel::Kit FirstPersonViewModel::kitForHands(const std::string &mainSkillGroup, bool mainTwoHanded,
    bool mainLarge, const std::string &offSkillGroup, bool offLarge)
{
    if (mainTwoHanded || !dualWieldable(mainSkillGroup) || !dualWieldable(offSkillGroup))
    {
        return kitFor(mainSkillGroup, mainTwoHanded);
    }
    // Each hand its own template; a two-handed weapon held in one hand (a Minotaur's battle axe) keeps its larger one.
    Kit kit;
    kit.set = WeaponSet::Dual;
    kit.weapon = kitFor(mainSkillGroup, mainLarge).weapon;
    kit.offWeapon = kitFor(offSkillGroup, offLarge).weapon;
    kit.heavy = mainLarge || offLarge;
    return kit;
}

FirstPersonViewModel::Kit FirstPersonViewModel::kitForBow(const std::string &heldKind)
{
    Kit kit = kitFor("Bow", false);
    if (heldKind == "crossbow")
    {
        // Both hands on the crossbow, the stock in the right fist: its own set and template (held_tiers.yml
        // kind_templates draws the same file for the kind).
        kit.set = WeaponSet::Crossbow;
        kit.weapon = "w_crossbow.glb";
    }
    return kit;
}

bool FirstPersonViewModel::poleKind(const std::string &heldKind)
{
    return heldKind == "spear" || heldKind == "trident" || heldKind == "polearm" || heldKind == "poleaxe";
}

FirstPersonViewModel::Kit FirstPersonViewModel::kitForHeldKind(const Kit &kit, const std::string &mainHeldKind)
{
    if (kit.set == WeaponSet::Dual || !poleKind(mainHeldKind))
    {
        return kit;
    }
    // Both hands on the shaft, low, the head in view: the pole set, whatever the skill group's kit (a spear's staff
    // grip, a poleaxe's battle axe, a Spear Master's one hand). held_tiers.yml kind_templates draws each
    // kind's own template (spear, trident, halberd); the spear is the fallback without those rules.
    Kit pole = kit;
    pole.set = WeaponSet::Pole;
    pole.weapon = "w_spear.glb";
    pole.heavy = false;
    return pole;
}

FirstPersonViewModel::Kit FirstPersonViewModel::dragonKit()
{
    Kit kit;
    kit.set = WeaponSet::Claws;
    return kit;
}

std::string FirstPersonViewModel::packagedModelPath(const Kit &kit)
{
    return kit.set == WeaponSet::Claws ? "engine/view_model/dragon_forelegs.glb" : "engine/view_model/arms.glb";
}

std::string FirstPersonViewModel::clawsAction(uint32_t step, char side)
{
    // Five blows a round as comboAction's: the claws have no chops or directional power attacks, so the fifth is the
    // bite, and the next round starts again from the right.
    if (step % 5 == 4)
    {
        return "bite";
    }
    return side == 'L' ? "attackleft" : "attackright";
}

std::string FirstPersonViewModel::comboAction(uint32_t step, char side, float forward, float left)
{
    // A round is five blows: right, left, right chop, left chop, then a power attack in the direction of movement
    // (Oblivion's directional power attacks: a lunge forward, a sweep to the side, a step-back cut, the overhead
    // blow standing; with a weapon in each hand the standing one is the cross slash of both blades).
    const uint32_t round = step % 5;
    if (round == 4)
    {
        const float speed = std::hypot(forward, left);
        return speed <= DirectionalPowerSpeed ? "attackpower"
            : std::abs(forward) >= std::abs(left) ? (forward >= 0.0f ? "attackforwardpower" : "attackbackpower")
            : (left >= 0.0f ? "attackleftpower" : "attackrightpower");
    }
    const std::string base = side == 'L' ? "attackleft" : "attackright";
    return round == 2 || round == 3 ? base + "_chop" : base;
}
}
