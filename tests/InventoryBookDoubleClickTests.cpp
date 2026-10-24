#include "game/ui/InventoryBookDoubleClick.h"

#include <doctest/doctest.h>

namespace OpenYAMM::Game
{
TEST_CASE("inventory book double click accepts nearby clicks within 500 milliseconds")
{
    InventoryBookDoubleClick gesture;
    CHECK_FALSE(gesture.pending());
    gesture.arm(2, 1000, 100.0f, 200.0f, 6.0f);
    gesture.update(2, 1500, 103.0f, 204.0f);
    CHECK(gesture.pending());
}

TEST_CASE("inventory book double click expires and does not rearm on a later click")
{
    InventoryBookDoubleClick gesture;
    gesture.arm(2, 1000, 100.0f, 200.0f, 6.0f);
    gesture.update(2, 1501, 100.0f, 200.0f);
    CHECK_FALSE(gesture.pending());
    gesture.update(2, 1510, 100.0f, 200.0f);
    CHECK_FALSE(gesture.pending());
}

TEST_CASE("inventory book double click cancels when moving away even if the pointer returns")
{
    InventoryBookDoubleClick gesture;
    gesture.arm(2, 1000, 100.0f, 200.0f, 6.0f);
    gesture.update(2, 1100, 105.0f, 205.0f);
    CHECK_FALSE(gesture.pending());
    gesture.update(2, 1200, 100.0f, 200.0f);
    CHECK_FALSE(gesture.pending());
}

TEST_CASE("inventory book double click cancels on a character change including a return to the owner")
{
    InventoryBookDoubleClick gesture;
    gesture.arm(2, 1000, 100.0f, 200.0f, 6.0f);
    gesture.update(1, 1100, 100.0f, 200.0f);
    gesture.update(2, 1200, 100.0f, 200.0f);
    CHECK_FALSE(gesture.pending());
}

TEST_CASE("inventory book double click clears with item replacement or explicit cancellation")
{
    InventoryBookDoubleClick gesture;
    gesture.arm(2, 1000, 100.0f, 200.0f, 6.0f);
    SUBCASE("another action cancels the gesture")
    {
        gesture.cancel();
    }
    SUBCASE("replacing or consuming the held item resets its gesture")
    {
        gesture = {};
    }
    gesture.update(2, 1200, 100.0f, 200.0f);
    CHECK_FALSE(gesture.pending());
}

TEST_CASE("inventory book double click scales its movement tolerance with the inventory")
{
    InventoryBookDoubleClick gesture;
    gesture.arm(2, 1000, 100.0f, 200.0f, 12.0f);
    gesture.update(2, 1200, 110.0f, 200.0f);
    CHECK(gesture.pending());
    gesture.update(2, 1250, 113.0f, 200.0f);
    CHECK_FALSE(gesture.pending());
}
} // namespace OpenYAMM::Game
