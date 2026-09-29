const movementKeys = new Set(["w", "a", "s", "d", "q", "e", "z", "c"]);
const oneShotKeys = new Set(["+", "-", "1", "2", "3", "4", "5", "6", "7", "8", "9"]);
const labels = {
  w: "Forward",
  s: "Backward",
  a: "Pivoting left",
  d: "Pivoting right",
  q: "Curving forward left",
  e: "Curving forward right",
  z: "Curving backward left",
  c: "Curving backward right",
};

const heldMovements = [];
const pressedOneShot = new Set();
let activeMotion = null;
let heartbeat = null;
let lastEventId = 0;
let controllerAvailable = false;
let controlToken = null;
let commandSequence = 0;
let commandInFlight = false;
let controlGeneration = 0;

async function post(path, payload, keepalive = false) {
  const abort = new AbortController();
  const timeout = setTimeout(() => abort.abort(), 250);
  try {
    const response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-RobotCar": "1" },
      body: JSON.stringify(payload),
      signal: abort.signal,
      keepalive,
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || `HTTP ${response.status}`);
    return result;
  } finally {
    clearTimeout(timeout);
  }
}

function releaseControl(emergency = false) {
  const token = controlToken;
  controlToken = null;
  controlGeneration += 1;
  if (token || emergency) {
    // A token-specific release cannot interrupt a subsequent owner's session.
    post("/api/stop", emergency ? {} : { token }, true).catch(() => {});
  }
}

const connection = document.querySelector("#connection");
const connectionLabel = document.querySelector("#connection-label");
const connectionDetail = document.querySelector("#connection-detail");
const motionState = document.querySelector("#motion-state");
const eventLog = document.querySelector("#event-log");
const curveSlider = document.querySelector("#curve-strength");
const curveValue = document.querySelector("#curve-value");
const curveDetail = document.querySelector("#curve-detail");
const speedValue = document.querySelector("#speed-value");
let pendingCurve = false;

function describeCurve(strength) {
  curveValue.textContent = `${strength}%`;
  curveDetail.textContent = strength === 100
    ? "Inside wheels released; outside wheels use selected PWM."
    : `Inside wheels: ${100 - strength}% of selected PWM. Actual turn depends on grip and load.`;
}

function showConfiguration(config) {
  speedValue.textContent = config ? config.speed : "—";
  curveSlider.disabled = !controllerAvailable || !config;
  if (config && !pendingCurve && document.activeElement !== curveSlider) {
    curveSlider.value = config.curve;
    describeCurve(config.curve);
  }
  document.querySelectorAll(".number-keys [data-command]").forEach(button => {
    const pwm = 195 + Math.floor(60 * (Number(button.dataset.command) - 1) / 8);
    button.title = `PWM ${pwm}`;
    button.classList.toggle("selected", Boolean(config && config.speed === pwm));
  });
}

curveSlider.addEventListener("input", () => describeCurve(Number(curveSlider.value)));
curveSlider.addEventListener("change", async () => {
  pendingCurve = true;
  const applied = await sendCommand(`@c${curveSlider.value}`);
  pendingCurve = false;
  if (!applied) addClientEvent("warning", "Curve setting not sent; release controls and try again.");
});

function normalizeKey(event) {
  if (event.code === "Space") return " ";
  if (event.key === "=" && event.shiftKey) return "+";
  return event.key.toLowerCase();
}

function addClientEvent(level, message) {
  const now = new Date().toLocaleTimeString([], {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
  appendEvent({ time: now, level, message });
}

function appendEvent(event) {
  const atTop = eventLog.scrollTop < 35;
  const oldHeight = eventLog.scrollHeight;
  const oldTop = eventLog.scrollTop;
  const row = document.createElement("div");
  row.className = `event ${event.level}`;

  const time = document.createElement("span");
  time.className = "event-time";
  time.textContent = event.time;

  const level = document.createElement("span");
  level.className = "event-level";
  level.textContent = event.level;

  const message = document.createElement("span");
  message.textContent = event.message;
  row.append(time, level, message);
  eventLog.prepend(row);

  while (eventLog.children.length > 150) {
    eventLog.lastElementChild.remove();
  }
  eventLog.scrollTop = atTop ? 0 : oldTop + eventLog.scrollHeight - oldHeight;
}

async function sendCommand(command, quiet = false) {
  if (command === "x" || command === " ") {
    releaseControl(true);
    return true;
  }
  if (!controllerAvailable) {
    if (!quiet) addClientEvent("warning", "Controller is not connected");
    return false;
  }
  // Never queue heartbeats: delayed commands must not accumulate in the browser.
  if (commandInFlight) return false;
  commandInFlight = true;
  const generation = controlGeneration;
  try {
    if (!controlToken) {
      const result = await post("/api/control", {});
      if (generation !== controlGeneration) {
        post("/api/stop", { token: result.token }, true).catch(() => {});
        return false;
      }
      controlToken = result.token;
      commandSequence = 0;
    }
    if (generation !== controlGeneration) return false;
    // A changed/released key supersedes the command that began acquisition.
    if (movementKeys.has(command) && activeMotion !== command) return false;
    await post("/api/command", {
      token: controlToken, sequence: ++commandSequence, command,
    });
    if (generation === controlGeneration && !activeMotion) releaseControl();
    return true;
  } catch (error) {
    if (generation === controlGeneration) {
      releaseControl();
      setConnection(false, "Control interrupted; release and press again");
      addClientEvent("error", error.message);
      stopLocally();
    }
    return false;
  } finally {
    commandInFlight = false;
  }
}

function setConnection(connected, detail = "") {
  controllerAvailable = connected;
  connection.classList.toggle("connected", connected);
  connection.classList.toggle("error", !connected);
  connectionLabel.textContent = connected ? "UNO connected" : "Disconnected";
  connectionDetail.textContent = detail || "No serial connection";
  curveSlider.disabled = !connected;
}

function setKeyActive(command, active) {
  document
    .querySelectorAll(`[data-command="${CSS.escape(command)}"]`)
    .forEach((element) => element.classList.toggle("active", active));
}

function beginMovement(command) {
  if (!movementKeys.has(command) || !controllerAvailable) return;
  const existing = heldMovements.indexOf(command);
  if (existing >= 0) return;

  heldMovements.push(command);
  if (activeMotion) setKeyActive(activeMotion, false);
  activeMotion = command;
  setKeyActive(command, true);
  motionState.textContent = labels[command];
  sendCommand(command);
  restartHeartbeat();
}

function endMovement(command) {
  const index = heldMovements.indexOf(command);
  if (index < 0) return;
  heldMovements.splice(index, 1);
  setKeyActive(command, false);

  const next = heldMovements.at(-1) || null;
  activeMotion = next;
  if (next) {
    setKeyActive(next, true);
    motionState.textContent = labels[next];
    sendCommand(next);
    restartHeartbeat();
  } else {
    stopDriving();
  }
}

function restartHeartbeat() {
  clearInterval(heartbeat);
  if (!activeMotion) return;
  heartbeat = setInterval(() => {
    if (activeMotion) sendCommand(activeMotion, true);
  }, 100);
}

function stopLocally() {
  clearInterval(heartbeat);
  heartbeat = null;
  heldMovements.splice(0);
  activeMotion = null;
  document.querySelectorAll(".key.active").forEach((key) => {
    key.classList.remove("active");
  });
  motionState.textContent = "No movement requested";
  pressedOneShot.clear();
}

function stopDriving() {
  stopLocally();
  releaseControl();
  flashStopKeys();
}

function flashStopKeys() {
  document.querySelectorAll(".key.stop").forEach((key) => {
    key.classList.add("active");
    setTimeout(() => key.classList.remove("active"), 160);
  });
}

function sendOneShot(command) {
  if (command === "x" || command === " ") {
    stopLocally();
    releaseControl(true);
    flashStopKeys();
    return;
  }
  sendCommand(command);
  setKeyActive(command, true);
}

document.addEventListener("keydown", (event) => {
  const key = normalizeKey(event);
  if (event.target?.matches("input, select, textarea") && key !== " " && key !== "x") return;
  if (movementKeys.has(key) || oneShotKeys.has(key) || key === " " || key === "x") {
    event.preventDefault();
  }

  if (movementKeys.has(key)) {
    if (!event.repeat) beginMovement(key);
  } else if (oneShotKeys.has(key)) {
    if (!pressedOneShot.has(key)) {
      pressedOneShot.add(key);
      sendOneShot(key);
    }
  } else if ((key === "x" || key === " ") && !event.repeat) {
    sendOneShot(key);
  }
});

document.addEventListener("keyup", (event) => {
  const key = normalizeKey(event);
  if (movementKeys.has(key)) {
    endMovement(key);
  } else {
    pressedOneShot.delete(key);
    setKeyActive(key, false);
  }
});

document.querySelectorAll("[data-command]").forEach((button) => {
  const command = button.dataset.command;
  button.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    button.setPointerCapture(event.pointerId);
    if (movementKeys.has(command)) beginMovement(command);
    else if (command === "x" || command === " ") sendOneShot(command);
    else setKeyActive(command, true);
  });
  const release = () => {
    if (movementKeys.has(command)) endMovement(command);
    else setKeyActive(command, false);
  };
  if (!movementKeys.has(command)) {
    button.addEventListener("click", () => sendOneShot(command));
  }
  button.addEventListener("pointerup", release);
  button.addEventListener("pointercancel", release);
  button.addEventListener("lostpointercapture", release);
});

window.addEventListener("blur", () => {
  if (activeMotion) {
    stopDriving();
    addClientEvent("warning", "Window lost focus; stop command sent");
  }
});

document.addEventListener("visibilitychange", () => {
  if (document.hidden && activeMotion) stopDriving();
});

window.addEventListener("pagehide", () => {
  stopLocally();
  releaseControl();
});

document.querySelector("#clear-log").addEventListener("click", () => {
  eventLog.replaceChildren();
});

async function pollStatus() {
  try {
    const abort = new AbortController();
    const timeout = setTimeout(() => abort.abort(), 1000);
    let response;
    try {
      response = await fetch(`/api/status?after=${lastEventId}`, {
        cache: "no-store", signal: abort.signal,
      });
    } finally {
      clearTimeout(timeout);
    }
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const status = await response.json();
    const ready = status.connected && status.firmware_ready;
    if (!ready) {
      releaseControl();
      stopLocally();
    }
    setConnection(
      ready,
      status.connected && !status.firmware_ready
        ? "Upload updated UNO firmware, then restart controller"
        : status.connected ? `${status.port} · ${status.baud} baud` : "Serial port closed",
    );
    showConfiguration(ready ? status.configuration : null);
    for (const event of status.events) {
      appendEvent(event);
      lastEventId = Math.max(lastEventId, event.id);
    }
  } catch (error) {
    if (controllerAvailable) {
      addClientEvent("error", `Controller server unavailable: ${error.message}`);
    }
    releaseControl();
    setConnection(false, "Controller server unavailable");
    stopLocally();
    showConfiguration(null);
  } finally {
    setTimeout(pollStatus, 500);
  }
}

pollStatus();
