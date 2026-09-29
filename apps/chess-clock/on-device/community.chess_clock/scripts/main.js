const APP_ID = "community.chess_clock";
const API = "http://127.0.0.1/api";
const DRAW_URL = API + "/display/draw";
const CLEAR_URL = DRAW_URL + "?application_name=" + APP_ID;
const SETTINGS_URL =
    "http://127.0.0.1/api/storage/read?path=/ext/apps_data/jsrunner/community.chess_clock.settings.json";

const WHITE = 0;
const BLACK = 1;
const SIDE_NAMES = ["WHITE", "BLACK"];

const RUNNING = "running";
const PAUSED = "paused";
const FLAGGED = "flagged";

const MIN_MINUTES = 1;
const MAX_MINUTES = 180;
const MIN_INCREMENT = 0;
const MAX_INCREMENT = 180;
const DEFAULT_MINUTES = 5;
const DEFAULT_INCREMENT = 0;
const INPUT_GRACE_MS = 400;

const TICK_MS = 50;
const LOW_BELOW_MS = 30000;
const FLAG_BLINK_MS = 500;
const FLAG_LED_MS = 2800;

const BACK_WIDTH = 145;
const BACK_HEIGHT = 80;
const FRONT_WIDTH = 72;
const FRONT_HEIGHT = 16;
const BACK_CENTRE_X = 72;
const BACK_MID_Y = 40;
const FRONT_CENTRE_X = 36;
const FRONT_MID_Y = 8;
const BACK_PARTITION = [3, 18];
const FRONT_PARTITION = [2, 12];
const BACK_GAP = 8;
const FRONT_GAP = 3;

const FRONT_FONT = "bold";
const BACK_FONT = "extra_large";

const COLOR_ACTIVE = "#FFFFFFFF";
const COLOR_IDLE = "#808080FF";
const COLOR_BLANK = "#000000FF";
const FRONT_ACTIVE = "#FFFFFFFF";
const FRONT_IDLE = "#4A4A4AFF";
const FRONT_LOW = "#FF2020FF";
const FRONT_LOW_IDLE = "#701010FF";
const LED_FLAG_COLOR = "#FF0000FF";
const LED_OFF_COLOR = "#000000FF";

const IMG_BG = "images/background.png";
const IMG_PART = "images/partition.png";

let phase = PAUSED;
let turn = WHITE;
let moves = [0, 0];
let remaining = [0, 0];
let turnStartedAt = 0;
let flaggedSide = -1;
let flagBlinkOn = true;
let flagLedAt = 0;
let setupMinutes = DEFAULT_MINUTES;
let setupIncrement = DEFAULT_INCREMENT;

let unbindInput = null;
let tickTimer = null;
let drawing = false;
let dirty = true;
let pendingLed = null;
let screenKind = "";
let lastBody = "";
let inputReady = false;

function pad2(value) {
    return (value < 10 ? "0" : "") + value;
}

function clamp(value, min, max) {
    if (value < min) {
        return min;
    }
    if (value > max) {
        return max;
    }
    return value;
}

function formatClock(ms) {
    let seconds = ms / 1000;
    if (seconds < 0) {
        seconds = 0;
    }
    let total = Math.ceil(seconds - 0.000001);
    if (total < 0) {
        total = 0;
    }
    const minutes = Math.floor(total / 60);
    return pad2(minutes) + ":" + pad2(total % 60);
}

function baseMs() {
    return setupMinutes * 60 * 1000;
}

function resetGame() {
    phase = PAUSED;
    turn = WHITE;
    moves = [0, 0];
    remaining = [baseMs(), baseMs()];
    turnStartedAt = 0;
    flaggedSide = -1;
    flagBlinkOn = true;
    flagLedAt = 0;
}

function remainingFor(side, now) {
    let value = remaining[side];
    if (phase === RUNNING && side === turn) {
        value -= now - turnStartedAt;
    }
    return value < 0 ? 0 : value;
}

function settle(now) {
    if (phase === RUNNING) {
        remaining[turn] = remainingFor(turn, now);
    }
    turnStartedAt = now;
}

function handOver(now) {
    if (phase !== RUNNING) {
        return;
    }
    const side = turn;
    settle(now);
    remaining[side] += setupIncrement * 1000;
    moves[side] += 1;
    turn = side === WHITE ? BLACK : WHITE;
}

function togglePause(now) {
    if (phase === RUNNING) {
        settle(now);
        phase = PAUSED;
    } else if (phase === PAUSED) {
        turnStartedAt = now;
        phase = RUNNING;
    }
}

function tickFlag(now) {
    if (phase !== RUNNING) {
        return;
    }
    if (remainingFor(turn, now) > 0) {
        return;
    }
    remaining[turn] = 0;
    flaggedSide = turn;
    phase = FLAGGED;
    flagBlinkOn = true;
    flagLedAt = 0;
    console.info(SIDE_NAMES[flaggedSide] + " flagged.");
}

function statusElement(text, color, font) {
    return {
        id: "b.status",
        type: "text",
        x: BACK_CENTRE_X,
        y: BACK_HEIGHT - 1,
        align: "bottom_mid",
        text: text,
        font: font,
        color: color,
        display: "back",
        z_index: 3,
    };
}

function blankBack() {
    return {
        id: "b.bg",
        type: "rectangle",
        x: 0,
        y: 0,
        width: BACK_WIDTH,
        height: BACK_HEIGHT,
        display: "back",
        fill: "solid",
        fill_colors: [COLOR_BLANK],
        border_width: 0,
        z_index: 1,
    };
}

function clockFace(display, texts, colors, partitionColor) {
    const isBack = display === "back";
    const centre = isBack ? BACK_CENTRE_X : FRONT_CENTRE_X;
    const mid = isBack ? BACK_MID_Y : FRONT_MID_Y;
    const bar = isBack ? BACK_PARTITION : FRONT_PARTITION;
    const gap = isBack ? BACK_GAP : FRONT_GAP;
    const font = isBack ? BACK_FONT : FRONT_FONT;
    const tag = display[0];
    const leftEdge = centre - Math.floor(bar[0] / 2);
    const rightEdge = leftEdge + bar[0];
    const elements = [];

    if (isBack) {
        elements.push(blankBack());
        elements.push({
            id: tag + ".part",
            type: "rectangle",
            x: leftEdge,
            y: mid - Math.floor(bar[1] / 2),
            width: bar[0],
            height: bar[1],
            display: display,
            fill: "solid",
            fill_colors: [partitionColor],
            border_width: 0,
            z_index: 2,
        });
    } else {
        elements.push({
            id: "f.bg",
            type: "image",
            x: 0,
            y: 0,
            align: "top_left",
            path: IMG_BG,
            display: "front",
            opacity: 100,
            z_index: 1,
        });
        elements.push({
            id: "f.part",
            type: "image",
            x: leftEdge,
            y: mid - Math.floor(bar[1] / 2),
            align: "top_left",
            path: IMG_PART,
            display: "front",
            opacity: 100,
            z_index: 2,
        });
    }

    for (let side = 0; side < 2; side++) {
        const onLeft = side === WHITE;
        elements.push({
            id: tag + ".t" + side,
            type: "text",
            x: onLeft ? leftEdge - gap : rightEdge + gap,
            y: mid,
            align: onLeft ? "mid_right" : "mid_left",
            text: texts[side],
            font: font,
            color: colors[side],
            display: display,
            z_index: 3,
        });
    }
    return elements;
}

function frontColor(ms, active) {
    if (ms < LOW_BELOW_MS) {
        return active ? FRONT_LOW : FRONT_LOW_IDLE;
    }
    return active ? FRONT_ACTIVE : FRONT_IDLE;
}

function gameElements(now) {
    const times = [remainingFor(WHITE, now), remainingFor(BLACK, now)];
    const texts = [formatClock(times[WHITE]), formatClock(times[BLACK])];
    const flagged = phase === FLAGGED;

    function sideColor(side, activeColor, idleColor, blankColor) {
        if (flagged && side === flaggedSide) {
            return flagBlinkOn ? activeColor : blankColor;
        }
        if (flagged) {
            return activeColor;
        }
        return side === turn ? activeColor : idleColor;
    }

    const backColors = [
        sideColor(WHITE, COLOR_ACTIVE, COLOR_IDLE, COLOR_BLANK),
        sideColor(BLACK, COLOR_ACTIVE, COLOR_IDLE, COLOR_BLANK),
    ];
    const frontColors = [
        sideColor(WHITE, frontColor(times[WHITE], true), FRONT_IDLE, COLOR_BLANK),
        sideColor(BLACK, frontColor(times[BLACK], true), FRONT_IDLE, COLOR_BLANK),
    ];
    const partition = phase === RUNNING ? COLOR_ACTIVE : COLOR_IDLE;
    const frontPartition = phase === RUNNING ? FRONT_ACTIVE : FRONT_IDLE;

    const elements = clockFace("back", texts, backColors, partition).concat(
        clockFace("front", texts, frontColors, frontPartition)
    );

    if (phase === PAUSED) {
        elements.push(statusElement("PAUSED  -  START TO PLAY", COLOR_ACTIVE, "tiny"));
    } else if (flagged) {
        const winner = SIDE_NAMES[1 - flaggedSide];
        elements.push(statusElement(winner + " WINS", COLOR_ACTIVE, "normal"));
    }
    return elements;
}

function postJson(url, body) {
    return fetch(
        new Request(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        })
    );
}

async function pushFrame() {
    const now = Date.now();
    tickFlag(now);
    const elements = gameElements(now);
    const payload = {
        application_name: APP_ID,
        priority: 100,
        elements: elements,
    };
    if (phase === FLAGGED && now - flagLedAt >= FLAG_LED_MS) {
        pendingLed = LED_FLAG_COLOR;
        flagLedAt = now;
    }
    if (pendingLed) {
        payload.led_notification_color = pendingLed;
        pendingLed = null;
    }
    const body = JSON.stringify(payload);
    if (body === lastBody && screenKind === "game") {
        return;
    }

    if (screenKind !== "game") {
        try {
            await fetch(new Request(CLEAR_URL, { method: "DELETE" }));
        } catch (error) {
            console.error("Clear failed:", error);
        }
        screenKind = "game";
    }

    try {
        await postJson(DRAW_URL, payload);
        lastBody = body;
    } catch (error) {
        console.error("Draw failed:", error);
        lastBody = "";
    }
}

async function drawLoop() {
    if (drawing) {
        return;
    }
    drawing = true;
    try {
        while (dirty) {
            dirty = false;
            await pushFrame();
        }
    } catch (error) {
        console.error("Draw loop failed:", error);
    }
    drawing = false;
}

function requestDraw() {
    dirty = true;
    drawLoop();
}

function stopApp() {
    if (tickTimer !== null) {
        clearInterval(tickTimer);
        tickTimer = null;
    }
    if (unbindInput) {
        const unbind = unbindInput;
        unbindInput = null;
        unbind();
    }
}

function onButton(key) {
    const now = Date.now();
    if (phase === FLAGGED) {
        if (key === "start") {
            pendingLed = LED_OFF_COLOR;
            resetGame();
            requestDraw();
        }
        return;
    }
    if (key === "start") {
        if (phase === PAUSED) {
            togglePause(now);
        } else {
            handOver(now);
        }
    } else {
        togglePause(now);
    }
    requestDraw();
}

function onInput(event) {
    if (!inputReady) {
        return;
    }
    if (event.key === "encoder") {
        return;
    }
    if (event.key === "back") {
        if (event.action !== "release") {
            return;
        }
        console.info("Leaving Chess Clock.");
        stopApp();
        return;
    }
    if (event.action !== "release") {
        return;
    }
    if (event.key === "ok" || event.key === "start") {
        onButton(event.key);
    }
}

async function loadSettings() {
    try {
        const response = await fetch(SETTINGS_URL);
        const data = await response.json();
        const values = data && data.values ? data.values : {};
        const minutes = Math.floor(Number(values.minutes));
        const increment = Math.floor(Number(values.increment));
        setupMinutes = isNaN(minutes)
            ? DEFAULT_MINUTES
            : clamp(minutes, MIN_MINUTES, MAX_MINUTES);
        setupIncrement = isNaN(increment)
            ? DEFAULT_INCREMENT
            : clamp(increment, MIN_INCREMENT, MAX_INCREMENT);
    } catch (error) {
        setupMinutes = DEFAULT_MINUTES;
        setupIncrement = DEFAULT_INCREMENT;
        console.info("Using default time control.");
    }
}

async function main() {
    await loadSettings();
    resetGame();
    console.info("Time control " + setupMinutes + "+" + setupIncrement);
    unbindInput = listen("input", onInput);
    tickTimer = setInterval(function () {
        if (phase === RUNNING) {
            requestDraw();
            return;
        }
        if (phase !== FLAGGED) {
            return;
        }
        const on = Math.floor(Date.now() / FLAG_BLINK_MS) % 2 === 0;
        if (on !== flagBlinkOn || Date.now() - flagLedAt >= FLAG_LED_MS) {
            flagBlinkOn = on;
            requestDraw();
        }
    }, TICK_MS);
    requestDraw();
    setTimeout(function () {
        inputReady = true;
    }, INPUT_GRACE_MS);
}

main().catch(console.error);
