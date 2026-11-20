#include "engine/AssetFileSystem.h"
#include "game/data/GameDataLoader.h"
#include "game/ui/screens/NewGameScreen.h"

#include <doctest/doctest.h>

#include <algorithm>
#include <filesystem>

namespace OpenYAMM::Game
{
struct NewGameScreenTestAccess
{
    static void checkAllContinents(NewGameScreen &screen, const GameDataRepository &data,
                                   std::vector<Character> &createdParty, uint32_t &startingContinentId)
    {
        std::vector<uint32_t> expectedCharacterIds;
        for (const auto &[id, entry] : data.characterDollTable().characters())
        {
            if (entry.availableAtStart)
            {
                expectedCharacterIds.push_back(id);
            }
        }
        std::sort(expectedCharacterIds.begin(), expectedCharacterIds.end());
        const std::vector<uint32_t> dragonClassIds = {10};
        const std::vector<uint32_t> expectedDragonIds = {25, 26, 72, 75};

        for (const MergedCharacterSelectionContinent &continent : data.mergedCharacterSelectionTable().continents())
        {
            CAPTURE(continent.key);
            screen.selectContinent(continent.key);
            const uint32_t clericClassId = continent.key == "jadame" ? 5 : 4;
            const uint32_t mageClassId = continent.key == "enroth" || continent.key == "antagarich" ? 42 : 44;
            const std::vector<uint32_t> humanClassIds = {0, clericClassId, 12, 16, 22, 26, 30, 34, mageClassId};
            std::vector<uint32_t> characterIds;
            std::vector<size_t> dragonIndices;
            bool foundHuman = false;
            for (size_t index = 0; index < screen.m_candidates.size(); ++index)
            {
                const NewGameScreen::CreationCandidate &candidate = screen.m_candidates[index];
                CHECK(std::find(candidate.availableClassIds.begin(), candidate.availableClassIds.end(),
                                clericClassId == 4 ? 5u : 4u)
                      == candidate.availableClassIds.end());
                CHECK(std::find(candidate.availableClassIds.begin(), candidate.availableClassIds.end(),
                                mageClassId == 42 ? 44u : 42u)
                      == candidate.availableClassIds.end());
                REQUIRE(std::find(candidate.availableClassIds.begin(), candidate.availableClassIds.end(),
                                  candidate.classId) != candidate.availableClassIds.end());
                const CharacterDollEntry *entry = data.characterDollTable().getCharacter(candidate.characterDataId);
                REQUIRE(entry != nullptr);
                if (entry->defaultClassId == 4 || entry->defaultClassId == 5)
                {
                    CHECK_EQ(candidate.classId, clericClassId);
                }
                if (entry->defaultClassId == 42 || entry->defaultClassId == 44)
                {
                    CHECK_EQ(candidate.classId, mageClassId);
                }
                characterIds.push_back(candidate.characterDataId);
                if (candidate.raceName == "Human")
                {
                    CHECK(candidate.availableClassIds == humanClassIds);
                    foundHuman = true;
                }
                if (candidate.raceName == "Dragon")
                {
                    CHECK(candidate.availableClassIds == dragonClassIds);
                    dragonIndices.push_back(index);
                }
            }
            CHECK(std::search(characterIds.begin(), characterIds.end(),
                              expectedDragonIds.begin(), expectedDragonIds.end()) != characterIds.end());
            std::sort(characterIds.begin(), characterIds.end());
            CHECK(characterIds == expectedCharacterIds);
            CHECK(foundHuman);
            REQUIRE_EQ(dragonIndices.size(), expectedDragonIds.size());

            const auto human = std::find_if(screen.m_candidates.begin(), screen.m_candidates.end(),
                [](const NewGameScreen::CreationCandidate &candidate) { return candidate.raceName == "Human"; });
            REQUIRE(human != screen.m_candidates.end());
            const size_t humanIndex = static_cast<size_t>(human - screen.m_candidates.begin());
            for (uint32_t classId : {clericClassId, mageClassId})
            {
                screen.resetStateForCandidate(humanIndex);
                screen.m_state.selectedClassId = classId;
                screen.refreshSkillChoices(false);
                createdParty.clear();
                screen.confirmCreation();
                REQUIRE_EQ(createdParty.size(), 1);
                CHECK_EQ(createdParty.front().className,
                         classId == clericClassId ? (clericClassId == 5 ? "Priest" : "Cleric")
                                                 : (mageClassId == 44 ? "Necromancer" : "Sorcerer"));
                CHECK_EQ(startingContinentId, continent.id);
                CHECK(createdParty.front().hasSkill(classId == clericClassId ? "BodyMagic"
                                                       : mageClassId == 44 ? "DarkMagic" : "FireMagic"));
            }

            // A Dark Elf by race of another class gets the race's ability as a fixed skill, not one of the two choices.
            const auto darkElf = std::find_if(screen.m_candidates.begin(), screen.m_candidates.end(),
                [](const NewGameScreen::CreationCandidate &candidate) { return candidate.raceName == "DarkElf"; });
            REQUIRE(darkElf != screen.m_candidates.end());
            REQUIRE(std::find(darkElf->availableClassIds.begin(), darkElf->availableClassIds.end(), 0u)
                    != darkElf->availableClassIds.end());
            screen.resetStateForCandidate(static_cast<size_t>(darkElf - screen.m_candidates.begin()));
            screen.m_state.selectedClassId = 0;
            screen.refreshSkillChoices(false);
            const std::vector<std::string> &fixedSkills = screen.m_state.defaultSkills;
            const std::vector<std::string> &choices = screen.m_state.optionalSkills;
            CHECK(std::find(fixedSkills.begin(), fixedSkills.end(), "DarkElfAbility") != fixedSkills.end());
            CHECK(std::find(choices.begin(), choices.end(), "DarkElfAbility") == choices.end());
            createdParty.clear();
            screen.confirmCreation();
            REQUIRE_EQ(createdParty.size(), 1);
            CHECK_EQ(createdParty.front().className, "Archer");
            CHECK(createdParty.front().hasSkill("DarkElfAbility"));
            CHECK(createdParty.front().hasSkill("Bow"));
            CHECK(createdParty.front().hasSkill("AirMagic"));

            for (size_t dragonIndex : dragonIndices)
            {
                createdParty.clear();
                startingContinentId = 0;
                screen.resetStateForCandidate(dragonIndex);
                screen.confirmCreation();
                REQUIRE_EQ(createdParty.size(), 1);
                CHECK_EQ(createdParty.front().characterDataId, screen.m_candidates[dragonIndex].characterDataId);
                CHECK_EQ(createdParty.front().raceId, 5);
                CHECK_EQ(createdParty.front().className, "Dragon");
                CHECK_EQ(startingContinentId, continent.id);
            }
        }
    }

    static void checkPartySheet(NewGameScreen &screen)
    {
        screen.selectContinent("antagarich");
        REQUIRE(screen.m_partySize == 1);

        // New adventurers start from portraits nobody in the party has.
        screen.addPartySlot();
        screen.addPartySlot();
        REQUIRE(screen.m_partySize == 3);
        CHECK(screen.candidateForState(screen.m_partyStates[0]).characterDataId
              != screen.candidateForState(screen.m_partyStates[1]).characterDataId);
        CHECK(screen.candidateForState(screen.m_partyStates[1]).characterDataId
              != screen.candidateForState(screen.m_partyStates[2]).characterDataId);

        // Removing an adventurer above the selected one keeps the same adventurer selected.
        screen.switchActivePartySlot(2);
        const std::string selectedName = screen.m_state.name;
        screen.removePartySlotAt(0);
        CHECK(screen.m_partySize == 2);
        CHECK(screen.m_activePartySlot == 1);
        CHECK(screen.m_state.name == selectedName);

        // A typed name survives a new portrait; a generated one does not have to.
        screen.m_state.nameEditing = true;
        screen.m_state.nameEditBuffer = "Zed";
        screen.endNameEditing(true);
        CHECK(screen.m_state.nameTyped);
        const size_t otherCandidate = (screen.m_state.selectedCandidateIndex + 1) % screen.m_candidates.size();
        screen.chooseCandidateForActiveSlot(otherCandidate);
        CHECK(screen.m_state.selectedCandidateIndex == otherCandidate);
        CHECK(screen.m_state.name == "Zed");

        // The party board picks another adventurer's skills under the same two-choice rule.
        const NewGameScreen::CreationState &other = screen.m_partyStates[0];
        REQUIRE(other.optionalSkills.size() >= 3);
        const std::vector<std::string> options = other.optionalSkills;
        CHECK(screen.toggleOptionalSkillForSlot(0, options[0]));
        CHECK(screen.toggleOptionalSkillForSlot(0, options[1]));
        CHECK_FALSE(screen.toggleOptionalSkillForSlot(0, options[2]));
        CHECK(screen.m_partyStates[0].selectedOptionalSkills.size() == 2);
        CHECK(screen.m_state.selectedOptionalSkills.empty());
    }
};
}

TEST_CASE("party creation offers all starting characters with continent-specific caster classes")
{
    using namespace OpenYAMM::Game;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    OpenYAMM::Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "mm6"));
    GameDataLoader loader;
    REQUIRE(loader.loadForHeadlessGameplay(assets));
    GameDataRepository data;
    data.bind(loader);
    std::vector<Character> createdParty;
    uint32_t startingContinentId = 0;
    NewGameScreen screen(assets, nullptr, data, false, false, true,
        [&](const std::vector<Character> &characters, const NewGameOptions &options)
        {
            createdParty = characters;
            startingContinentId = options.continentId;
            CHECK_FALSE(options.preserveDebugLoadout);
            CHECK(options.ruleset.isStandard());
        }, {}, {});
    NewGameScreenTestAccess::checkAllContinents(screen, data, createdParty, startingContinentId);
}

TEST_CASE("party creation sheet adds, removes and edits adventurers")
{
    using namespace OpenYAMM::Game;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    OpenYAMM::Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "mm6"));
    GameDataLoader loader;
    REQUIRE(loader.loadForHeadlessGameplay(assets));
    GameDataRepository data;
    data.bind(loader);
    NewGameScreen screen(assets, nullptr, data, false, false, false, {}, {}, {});
    NewGameScreenTestAccess::checkPartySheet(screen);
}
