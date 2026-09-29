# BUSY Bar Custom Apps

Community apps for the [BUSY Bar](https://busy.bar/).

There are two kinds. They do not work the same way.

## Runs on your computer

Your computer stays connected and updates the bar. These work with normal
BUSY Bar firmware. Leave the mode switch in **Off**.

| App | What it does |
|-----|----------------|
| [Network](Python%20Apps/network/) | Live download and upload speeds |
| [Social Battery](Python%20Apps/social-battery/) | Dial to show your social-energy level |

These live in [`Python Apps/`](Python%20Apps/).

## Runs on the bar

Install once. After that the bar runs the app from **Apps**. The computer
does not need to stay connected.

| App | What it does |
|-----|----------------|
| [Chess Clock](apps/chess-clock/) | Two-player game clock. Set the times in **Setup**, then **Start** |

These live in [`apps/`](apps/).

**This kind needs extra firmware.** Official BUSY docs still say installing
your own apps on the bar is coming soon. Chess Clock only shows up if your
bar already has the JavaScript runner. If it does not, use a computer app
above instead.

## AI lessons and skills

Plain Markdown for any AI assistant:

- Paste this into a chat: [ai-skills/BUSY-BAR-CORE.md](ai-skills/BUSY-BAR-CORE.md)
- Skills: [ai-skills/](ai-skills/)
- Longer lessons: [ai-lessons/](ai-lessons/)
- How to use: [ai-lessons/00-use-with-any-ai.md](ai-lessons/00-use-with-any-ai.md)

## Before you start

You need:

- a BUSY Bar;
- a Windows, macOS, or Linux computer;
- Python 3.10 or newer;
- either a USB connection or the BUSY Bar's Wi-Fi IP address.

Open an app's folder and follow its README.

## Safety and privacy

- Apps communicate directly with your BUSY Bar over your local network.
- A protected Wi-Fi access password is sent directly to the BUSY Bar when
  needed. It is not saved by the app.
- These are community projects and are not official BUSY Bar applications.

## License

Code and included artwork are released under the [MIT License](LICENSE).
