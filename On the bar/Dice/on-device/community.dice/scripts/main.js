const APP_ID = "community.dice";
const DRAW_URL = "http://127.0.0.1/api/display/draw";
const SETTINGS_URL =
    "http://127.0.0.1/api/storage/read?path=/ext/apps_data/jsrunner/community.dice.settings.json";

const FACES = 6;
const MIN_DICE = 1;
const MAX_DICE = 4;
const ROLL_SETTLE = 1000;
const INPUT_GRACE_MS = 400;
const BACKGROUND_OPACITY = 100;
const BACK_CENTRE_X = 72;
const FRONT_WIDTH = 72;
const DIE_WIDTH = 18;

const IDLE = "idle";
const ROLLING = "rolling";
const SETTLED = "settled";

const COLOR_TEXT = "#FFFFFFFF";
const COLOR_DIM = "#909090FF";

const IMG_LOGO = "images/logo.png";
const IMG_BG = "images/background.png";

let diceCount = 1;
let faces = [1];
let fromFaces = [1];
let phase = IDLE;
let rolls = 0;
let sentRoll = -1;
let unbindInput = null;
let settleTimer = null;
let drawing = false;
let dirty = true;
let lastBody = "";
let sentIds = [];
let inputReady = false;

function animPath(first, second) {
    return "animations/d" + first + second + ".anim";
}

function randomFace() {
    return 1 + Math.floor(Math.random() * FACES);
}

function clampDiceCount(value) {
    const count = Math.floor(Number(value));
    if (!(count >= MIN_DICE && count <= MAX_DICE)) {
        return MIN_DICE;
    }
    return count;
}

function dieX(index) {
    const leftover = FRONT_WIDTH - DIE_WIDTH * diceCount;
    const gap = Math.floor(leftover / (diceCount + 1));
    const extra = leftover - gap * (diceCount + 1);
    return gap + Math.floor(extra / 2) + index * (DIE_WIDTH + gap);
}

function dieId(index) {
    return "die" + index;
}

function isDieId(id) {
    return id.indexOf("die") === 0;
}

function textElement(id, text, font, color, y) {
    return {
        id: id,
        type: "text",
        x: BACK_CENTRE_X,
        y: y,
        align: "center",
        text: text,
        font: font,
        color: color,
        display: "back",
    };
}

function facesLabel() {
    let text = String(faces[0]);
    for (let i = 1; i < diceCount; i++) {
        text += "  " + String(faces[i]);
    }
    return text;
}

function settledFont() {
    if (diceCount === 1) {
        return "extra_large";
    }
    if (diceCount === 2) {
        return "large";
    }
    return "normal";
}

function currentElements() {
    const elements = [];

    elements.push({
        id: "bg",
        type: "image",
        path: IMG_BG,
        x: 0,
        y: 0,
        z_index: 0,
        display: "front",
        opacity: BACKGROUND_OPACITY,
    });

    if (phase === IDLE) {
        elements.push({
            id: "logo",
            type: "image",
            path: IMG_LOGO,
            x: 0,
            y: 0,
            z_index: 20,
            display: "front",
        });
    } else if (rolls !== sentRoll) {
        for (let i = 0; i < diceCount; i++) {
            elements.push({
                id: dieId(i),
                type: "animation",
                path: animPath(fromFaces[i], faces[i]),
                x: dieX(i),
                y: 0,
                z_index: 10,
                loop: false,
                display: "front",
            });
        }
    }

    let headline;
    let hint;
    let headlineFont;
    if (phase === IDLE) {
        headline = diceCount === 1 ? "DICE" : String(diceCount) + " DICE";
        hint = "PRESS START TO ROLL";
        headlineFont = "normal";
    } else if (phase === ROLLING) {
        headline = "ROLLING";
        hint = "...";
        headlineFont = "normal";
    } else {
        headline = facesLabel();
        hint = "PRESS START TO ROLL";
        headlineFont = settledFont();
    }

    elements.push(textElement("headline", headline, headlineFont, COLOR_TEXT, 34));
    elements.push(textElement("hint", hint, "small", COLOR_DIM, 68));
    return elements;
}

function postDraw(payload) {
    return fetch(
        new Request(DRAW_URL, {
            method: "POST",
            body: JSON.stringify(payload),
        })
    );
}

function staleIds(nextIds) {
    const stale = [];
    for (let i = 0; i < sentIds.length; i++) {
        const id = sentIds[i];
        if (nextIds.indexOf(id) !== -1) {
            continue;
        }
        if (isDieId(id) && phase !== IDLE) {
            continue;
        }
        stale.push(id);
    }
    return stale;
}

function deleteStale(ids) {
    if (!ids.length) {
        return Promise.resolve();
    }
    return fetch(
        new Request(DRAW_URL, {
            method: "DELETE",
            body: JSON.stringify({
                application_name: APP_ID,
                element_ids: ids,
            }),
        })
    ).catch(function () {
        return undefined;
    });
}

async function pushFrame() {
    const elements = currentElements();
    const payload = {
        application_name: APP_ID,
        priority: 100,
        elements: elements,
    };
    const body = JSON.stringify(payload);
    if (body === lastBody) {
        return;
    }
    const nextIds = [];
    for (let i = 0; i < elements.length; i++) {
        nextIds.push(elements[i].id);
    }
    const stale = staleIds(nextIds);
    try {
        await deleteStale(stale);
        await postDraw(payload);
        lastBody = body;
        sentIds = nextIds.concat(
            sentIds.filter(function (id) {
                return nextIds.indexOf(id) === -1 && stale.indexOf(id) === -1;
            })
        );
        if (phase !== IDLE) {
            sentRoll = rolls;
        }
    } catch (error) {
        console.error("Draw failed:", error);
        lastBody = "";
        sentRoll = -1;
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

function finishRoll() {
    settleTimer = null;
    if (phase !== ROLLING) {
        return;
    }
    phase = SETTLED;
    console.info("Rolled " + facesLabel());
    requestDraw();
}

function rollDice() {
    if (phase === ROLLING) {
        return;
    }
    for (let i = 0; i < diceCount; i++) {
        fromFaces[i] = faces[i];
        faces[i] = randomFace();
    }
    rolls += 1;
    phase = ROLLING;
    if (settleTimer !== null) {
        clearTimeout(settleTimer);
        settleTimer = null;
    }
    settleTimer = setTimeout(finishRoll, ROLL_SETTLE);
    requestDraw();
}

function stopApp() {
    if (settleTimer !== null) {
        clearTimeout(settleTimer);
        settleTimer = null;
    }
    if (unbindInput) {
        const unbind = unbindInput;
        unbindInput = null;
        unbind();
    }
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
        console.info("Leaving Dice.");
        stopApp();
        return;
    }
    if (event.action !== "release") {
        return;
    }
    if (event.key === "ok" || event.key === "start") {
        rollDice();
    }
}

async function loadDiceCount() {
    try {
        const response = await fetch(SETTINGS_URL);
        const data = await response.json();
        if (data && data.values) {
            return clampDiceCount(data.values.dice_count);
        }
    } catch (error) {
        console.info("Using 1 die (no Setup value yet).");
    }
    return MIN_DICE;
}

async function main() {
    diceCount = await loadDiceCount();
    faces = [];
    fromFaces = [];
    for (let i = 0; i < diceCount; i++) {
        faces.push(1);
        fromFaces.push(1);
    }
    console.info("Dice count " + diceCount);
    unbindInput = listen("input", onInput);
    requestDraw();
    setTimeout(function () {
        inputReady = true;
    }, INPUT_GRACE_MS);
}

main().catch(console.error);
