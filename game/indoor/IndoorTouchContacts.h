#pragma once

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace OpenYAMM::Game
{
// The walls the party has been pressed against, by movement step, so that a face of the touch kind runs its event
// once per new contact (scene `party_movement: {touch_faces: run}`), not on every step the party leans on it. A
// contact ends when the face has not stopped the party for GraceSteps steps (a slide along a wall can miss one).
class IndoorTouchContacts
{
public:
    static constexpr uint32_t GraceSteps = 16;

    // One movement step: the wall faces that stopped the party in it. Faces not in contact before are appended to
    // `newContacts`.
    void step(const std::vector<size_t> &touchedFaces, std::vector<size_t> &newContacts)
    {
        for (Contact &contact : m_contacts)
        {
            ++contact.stepsSinceTouched;
        }

        for (size_t face : touchedFaces)
        {
            const auto existing = std::find_if(m_contacts.begin(), m_contacts.end(),
                [face](const Contact &contact) { return contact.face == face; });

            if (existing != m_contacts.end())
            {
                existing->stepsSinceTouched = 0;
                continue;
            }

            m_contacts.push_back({face, 0});
            newContacts.push_back(face);
        }

        std::erase_if(m_contacts, [](const Contact &contact) { return contact.stepsSinceTouched > GraceSteps; });
    }

    void clear()
    {
        m_contacts.clear();
    }

private:
    struct Contact
    {
        size_t face = 0;
        uint32_t stepsSinceTouched = 0;
    };

    std::vector<Contact> m_contacts;
};
} // namespace OpenYAMM::Game
