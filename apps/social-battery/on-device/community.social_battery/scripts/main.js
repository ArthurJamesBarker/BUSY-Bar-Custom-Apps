const APP_ID = "community.social_battery";
const API = "http://127.0.0.1/api";
const DRAW_URL = API + "/display/draw";
const STORAGE_KEY = "community.social_battery.level";

const STATES = [
    { file: "images/critical.png", label: "CRITICAL" },
    { file: "images/very_low.png", label: "VERY LOW" },
    { file: "images/low.png", label: "LOW" },
    { file: "images/medium.png", label: "MEDIUM" },
    { file: "images/good.png", label: "GOOD" },
    { file: "images/high.png", label: "HIGH" },
    { file: "images/full.png", label: "FULL" },
];

const DEFAULT_LEVEL = 3;
const BACK_CENTRE_X = 72;

let level = DEFAULT_LEVEL;
let unbindInput = null;
let drawing = false;
let dirty = true;
let lastBody = "";

function clamp(value, min, max) {
    if (value < min) {
        return min;
    }
    if (value > max) {
        return max;
    }
    return value;
}

function loadLevel() {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (raw === null) {
            return;
        }
        const parsed = parseInt(raw, 10);
        if (!isNaN(parsed)) {
            level = clamp(parsed, 0, STATES.length - 1);
        }
    } catch (error) {
        console.error("Could not load social battery level:", error);
    }
}

function saveLevel() {
    try {
        localStorage.setItem(STORAGE_KEY, String(level));
    } catch (error) {
        console.error("Could not save social battery level:", error);
    }
}

function setLevel(next) {
    const clamped = clamp(next, 0, STATES.length - 1);
    if (clamped === level) {
        return false;
    }
    level = clamped;
    saveLevel();
    return true;
}

function currentElements() {
    const state = STATES[level];
    return [
        {
            id: "social_battery_state",
            type: "image",
            path: state.file,
            x: 0,
            y: 0,
            display: "front",
            opacity: 100,
        },
        {
            id: "label",
            type: "text",
            text: state.label,
            font: "extra_large",
            color: "#FFFFFFFF",
            x: BACK_CENTRE_X,
            y: 34,
            align: "center",
            display: "back",
        },
        {
            id: "hint",
            type: "text",
            text: "TURN DIAL",
            font: "small",
            color: "#909090FF",
            x: BACK_CENTRE_X,
            y: 68,
            align: "center",
            display: "back",
        },
    ];
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
    const payload = {
        application_name: APP_ID,
        priority: 100,
        elements: currentElements(),
    };
    const body = JSON.stringify(payload);
    if (body === lastBody) {
        return;
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
    if (unbindInput) {
        const unbind = unbindInput;
        unbindInput = null;
        unbind();
    }
}

function onInput(event) {
    if (event.key === "encoder") {
        if (event.delta && setLevel(level + event.delta)) {
            requestDraw();
        }
        return;
    }
    if (event.key === "back") {
        console.info("Leaving Social Battery.");
        stopApp();
        return;
    }
    if (event.action !== "release") {
        return;
    }
    if (event.key === "ok" || event.key === "start") {
        if (setLevel(level + 1)) {
            requestDraw();
        }
    }
}

function main() {
    loadLevel();
    unbindInput = listen("input", onInput);
    requestDraw();
}

main();
