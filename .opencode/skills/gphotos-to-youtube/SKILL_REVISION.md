Skill Revision: gphotos-to-youtube (Stability Update)

Problem Addressed
- Google Photos uses dynamic overlays and layered DOM elements.
- Accessibility refs frequently invalidate between interactions.
- Year slider navigation is unreliable.

Design Changes

1. Remove Year Slider Dependency
- Do NOT use right-side year slider.
- Do NOT depend on scrolling to reach a year boundary.

2. Deterministic Year + Video Navigation
Primary URL pattern:
https://photos.google.com/search/_vid_<YEAR>

Fallback URL pattern:
https://photos.google.com/search/year:<YEAR>%20video

Only proceed once the URL contains the year token.

3. UI Stabilization Phase (NEW – Required Before Any Interaction)
Before every major action:
- Press Escape twice
- Take fresh snapshot
- Verify no expanded combobox
- Verify no modal dialogs
- Verify target element is clickable

If element is covered:
- Press Escape
- Retry once
- If still blocked → mark step error

4. Interaction Rules
- Never reuse refs after navigation.
- Always snapshot before click.
- Always validate element role before acting.
- Never rely on previous state.

5. Video Enumeration Strategy
- Work only inside year-scoped video search page.
- Scroll until no new items load.
- Extract only items prefixed with "Video –".
- Deduplicate by unique ID in link URL.

6. Failure Policy
- Max 2 retries per action.
- If overlay persists after 2 Escape attempts → mark error.
- Do not attempt heuristic DOM dragging.

Result
- Deterministic navigation
- Overlay-safe execution
- No slider fragility
- Reduced ref invalidation risk

This revision supersedes slider-based year navigation in the original skill.
