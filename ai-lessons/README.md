# BUSY Bar AI Lessons

Up-to-date teaching materials for building apps and widgets against **official
BUSY Bar release firmware**.

These replace the older **BSB-AI Lessons** pack. That pack used outdated font
names (`medium`, `big`), the old `app_id` field, and mixed up Wi-Fi passwords
with cloud API tokens.

## Use with any AI

Start here: [00-use-with-any-ai.md](00-use-with-any-ai.md)

Skills (paste or upload):
[`../ai-skills/`](../ai-skills/) — especially [`BUSY-BAR-CORE.md`](../ai-skills/BUSY-BAR-CORE.md)

## Lessons

| Lesson | Topic |
|--------|--------|
| [00-use-with-any-ai.md](00-use-with-any-ai.md) | How to use this pack in any AI |
| [01-getting-started.md](01-getting-started.md) | USB address, first connection |
| [02-auth-password-vs-api-token.md](02-auth-password-vs-api-token.md) | **Wi-Fi HTTP password vs cloud API token** |
| [03-http-api-basics.md](03-http-api-basics.md) | Base URLs, key endpoints, busylib |
| [04-fonts-and-displays.md](04-fonts-and-displays.md) | Front/back sizes and current font names |
| [05-draw-and-assets.md](05-draw-and-assets.md) | Draw JSON, assets, layout recipes |

## Current sources of truth

- Official docs: https://docs.busy.app/bar/dev
- Interactive API: https://api.busy.app/busybar/docs
- Python client: https://pypi.org/project/busylib/
- TypeScript client: https://github.com/busy-app/busylib-ts

## Suggested order

1. Use with any AI  
2. Getting started  
3. Auth (password vs token)  
4. HTTP API basics  
5. Fonts and displays  
6. Draw and assets  

Then open an example app such as [`apps/social-battery/`](../apps/social-battery/).
