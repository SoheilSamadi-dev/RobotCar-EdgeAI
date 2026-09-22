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

const connection = document.querySelector("#connection");
const connectionLabel = document.querySelector("#connection-label");
const connectionDetail = document.querySelector("#connection-detail");
const motionState = document.querySelector("#motion-state");
const eventLog = document.querySelector("#event-log");

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
  const atBottom =
    eventLog.scrollHeight - eventLog.scrollTop - eventLog.clientHeight < 35;
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
  eventLog.append(row);

  while (eventLog.children.length > 150) {
    eventLog.firstElementChild.remove();
  }
  if (atBottom) eventLog.scrollTop = eventLog.scrollHeight;
}

async function sendCommand(command, quiet = false) {
  if (!controllerAvailable) {
    if (!quiet) addClientEvent("warning", "Controller is not connected");
    return false;
  }

  try {
    const response = await fetch("/api/command", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command }),
      keepalive: command === "x",
    });
    if (!response.ok) {
      const result = await response.json().catch(() => ({}));
      throw new Error(result.error || `HTTP ${response.status}`);
    }
    return true;
  } catch (error) {
    controllerAvailable = false;
    setConnection(false, "Command failed");
    addClientEvent("error", `Cannot send command: ${error.message}`);
    stopLocally();
    return false;
  }
}

function setConnection(connected, detail = "") {
  controllerAvailable = connected;
  connection.classList.toggle("connected", connected);
  connection.classList.toggle("error", !connected);
  connectionLabel.textContent = connected ? "UNO connected" : "Disconnected";
  connectionDetail.textContent = detail || "No serial connection";
}

function setKeyActive(command, active) {
  document
    .querySelectorAll(`[data-command="${CSS.escape(command)}"]`)
    .forEach((element) => element.classList.toggle("active", active));
}

function beginMovement(command) {
  if (!movementKeys.has(command)) return;
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
  motionState.textContent = "Motors stopped";
}

function stopDriving() {
  stopLocally();
  sendCommand("x");
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
    stopDriving();
    return;
  }
  sendCommand(command);
  setKeyActive(command, true);
}

document.addEventListener("keydown", (event) => {
  const key = normalizeKey(event);
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
    else sendOneShot(command);
  });
  const release = () => {
    if (movementKeys.has(command)) endMovement(command);
    else setKeyActive(command, false);
  };
  button.addEventListener("pointerup", release);
  button.addEventListener("pointercancel", release);
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
  navigator.sendBeacon(
    "/api/command",
    new Blob([JSON.stringify({ command: "x" })], { type: "application/json" }),
  );
});

document.querySelector("#clear-log").addEventListener("click", () => {
  eventLog.replaceChildren();
});

async function pollStatus() {
  try {
    const response = await fetch(`/api/status?after=${lastEventId}`, {
      cache: "no-store",
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const status = await response.json();
    setConnection(
      status.connected,
      status.connected ? `${status.port} · ${status.baud} baud` : "Serial port closed",
    );
    for (const event of status.events) {
      appendEvent(event);
      lastEventId = Math.max(lastEventId, event.id);
    }
  } catch (error) {
    if (controllerAvailable) {
      addClientEvent("error", `Controller server unavailable: ${error.message}`);
    }
    setConnection(false, "Local server unavailable");
    stopLocally();
  }
}

pollStatus();
setInterval(pollStatus, 500);
