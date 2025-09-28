# Leftoff – 2025-09-27

## Current State
- Player, pane, and HUD timing refactors are stable (dual-clock). Tests cover play→pause→reset loops.
- Debug panel dock works in single view (View → Show Debug Panel). Compare view dock not yet added.
- Transport wrappers (`_transport_play`/`_transport_toggle_pause`/`_transport_step_*`) implemented in `AlgorithmVisualizerBase`, but pane/transport wiring is mid-transition.
- Tests currently failing because `_on_step_item_activated` was removed/renamed during refactor; we must restore or adjust its binding in `AlgorithmVisualizerBase` when rewriting the transport layer.
- Roadmap items pending: shortcut unification (in progress), compare debug dock, splitter persistence/detachable panes.

## Next Actions Needed (ordered)
1. **Restore `_on_step_item_activated` or adjust step-list binding** so current tests (export, compare) pass.
2. **Finish transport rewrite:**
   - Phase 1 (in progress): move compare window/controller onto transport abstraction, ensure pane/transport signals align.
   - Once consistent, update compare controller instantiation to use transports c (already partially done) and ensure buttons check capabilities on transports.
3. **Compare Debug Dock:** replicate single-view debug toggle after transport rewrite is stable.
4. **UI/UX Splitter work (start with single view):** implement snap-able panes, splitter persistence, etc., then mirror in compare view.
5. **Testing:** add tests for start-after-finish behaviour (already added), plus targeted tests for new layout features when implemented.

## Audit Reference
- `docs/audit.md` needs an update once transport unify tasks and debug dock additions ship.

## Outstanding Visual QA
- Manual testing still required for latest fixes (e.g., start/pause behavior, debug panel, transport changes) once current test failures are resolved.
