# 07 — Setup, settings, and launch UX

Lessons from putting Chess Clock on the bar.

The launcher always shows **Start** and **Setup**. You cannot rename or remove
those rows. Put choices users make *before* play into **Setup**, not into a
second in-app menu.

## `appmeta/settings.json`

Drives the Setup screen. Example (Chess Clock):

```json
{
  "format_version": 1,
  "version": 1,
  "fields": {
    "minutes": {
      "label": "Minutes",
      "description": "Time each player starts with",
      "type": "integer",
      "default": 5,
      "min": 1,
      "max": 180,
      "step": 1
    }
  }
}
```

Useful editable types for Setup today: `boolean`, `integer`, `enum`
(also `string`, `color`, `time`, `geolocation`, `group` in the schema).

Field ids: lowercase letters, digits, underscore; must start with a letter.

Chess Clock puts **Minutes** and **Increment** here so Start can open the
clocks immediately.

## Where values are saved

`/ext/apps_data/jsrunner/<app-id>.settings.json`

Shape:

```json
{
  "version": 1,
  "values": {
    "minutes": 15,
    "increment": 10
  }
}
```

Integers are numbers. Enums are the option `value` strings.

There is **no** native “get settings” API in JerryScript. Read the file:

```js
const response = await fetch(
  "http://127.0.0.1/api/storage/read?path=/ext/apps_data/jsrunner/community.chess_clock.settings.json"
);
const data = await response.json();
const minutes = data.values.minutes;
```

`localStorage` is a **different** file (`<id>.localstorage.json`). Use it for
script-only state, not for Setup fields.

## Launch patterns that work well

| Pattern | When |
|---------|------|
| Start → straight into the app | Chess Clock: clocks appear paused; times come from Setup |
| Start → idle title, press again to act | Wait on a title until the player acts |
| In-app Setup / title card before play | Avoid when the launcher already has Setup |

Ignore input for ~400 ms after launch so the Start that opened the app does
not also trigger the first action.

**Back** while playing should leave the app (`unbind()` only). Do not send a
display clear after that.

## Side-by-side elements on the front (72×16)

1. Crop sprites so empty canvas does not steal the whole width.
2. Place with different `x` (and optional `z_index`).
3. Keep wash / background **behind** sprites (`z_index` lower, or draw order).
4. If sprites are RGB-on-black, punch black to transparent or the wash only
   shows in gaps between opaque boxes.

Example: crop each sprite (such as 18×16) so several can sit side by side,
with the background full-bleed behind them.

## Checklist for a new ported app

1. Package under `apps/<Name>/on-device/<id>/`.
2. `"debug": false` unless it should stay hidden.
3. Prefer Setup for user preferences; open Start into the real UI.
4. Read settings via `/api/storage/read` on the jsrunner settings path.
5. `install_on_bar.py` + enable `js_apps_enabled`.
6. Document Install in `apps/…`. Keep computer apps under `Python Apps/`.

## See also

- [06-js-apps-on-device.md](06-js-apps-on-device.md)
- `ai-skills/busy-bar-js-apps/SKILL.md`
- Example: `apps/chess-clock/`
