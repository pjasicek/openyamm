# Plan

## Objective

Reach the shared gameplay runtime boundary defined in:

- `docs/indoor_outdoor_shared_gameplay_extraction_plan.md`

That document is the only authoritative refactor target.

The goal is not thinner adapters. The goal is that gameplay owns input,
decisions, UI/screens, party actions, item flow, spell flow, combat rules, and
shared presentation. Indoor/outdoor provide only the active world
representation through `IGameplayWorldRuntime`.

## Target Frame Shape

The refactor is complete when the frame flow is structurally equivalent to:

```cpp
void GameApplication::renderFrame(int width, int height, float mouseWheelDelta, float deltaSeconds)
{
    m_gameInputSystem.updateFromEngineInput(width, height, mouseWheelDelta);

    m_gameSession.updateGameplay(m_gameInputSystem.frame(), deltaSeconds);

    if (IGameplayWorldRuntime *pWorld = m_gameSession.activeWorldRuntime())
    {
        pWorld->renderWorld(width, height, deltaSeconds);
    }

    m_gameSession.gameplayUiRuntime().render(width, height);
}
```

Exact names may differ. Ownership must not.

## Current Reality

- Shared controllers exist, but shared gameplay still receives a large
  callback-heavy `WorldInteractionFrameInput`.
- Outdoor still assembles gameplay/world interaction callbacks in
  `OutdoorGameView::render`.
- Indoor still has no-op callback seams for world interaction.
- Outdoor and indoor still participate in input sampling or raw input passing
  for shared gameplay paths.
- `IGameplayWorldRuntime` exists, but it is not yet the cohesive active-world
  interaction/render boundary.

## Required Migration Order

1. Introduce `GameInputSystem` and `GameplayInputFrame`.
2. Add `GameplaySession::updateGameplay`.
3. Replace `WorldInteractionFrameInput` callback bag with direct
   `GameSession` state access and direct active-world calls.
4. Move outdoor callback bodies into `OutdoorWorldRuntime` or cohesive outdoor
   world services implementing the active-world seam.
5. Implement indoor active-world seam methods.
6. Move world rendering behind the active-world boundary.
7. Continue shared-system extraction under this boundary.

## Anti-Goals

- Do not add a second authoritative plan.
- Do not introduce another adapter that hides the same ownership leak.
- Do not let `OutdoorGameView` or `IndoorGameView` own shared gameplay
  semantics.
- Do not pass callbacks for state already owned by `GameSession`.
- Do not sample SDL input in indoor/outdoor for shared gameplay behavior.

## Rules

- Use `TASK_QUEUE.md` as the executable queue.
- Finish one ownership transfer path before starting another.
- Keep behavior unchanged unless fixing a clear bug.
- Keep the repository buildable after each meaningful slice.
- Update `PROGRESS.md` after each meaningful slice.
