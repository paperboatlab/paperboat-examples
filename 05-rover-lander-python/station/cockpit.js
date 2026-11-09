// LZ-1 cockpit: a phosphor CRT drawn from the engine's entities and signals.
//
// The page is a Station view only: it draws what the backend sends and forwards key
// presses. The GNC law and the vehicle are in the backend; nothing here decides.
"use strict";

const canvas = document.getElementById("view");
const ctx = canvas.getContext("2d");
const altEl = document.getElementById("alt");
const vyEl = document.getElementById("vy");
const vxEl = document.getElementById("vx");
const targetEl = document.getElementById("target");
const fuelEl = document.getElementById("fuel");
const fuelBar = document.getElementById("fuel-bar");
const modeEl = document.getElementById("mode");
const statusEl = document.getElementById("status");

const readings = { alt: 70, vy: -2, vx: 0.5, fuel: 90, ap: 1, target: 0 };
const VIEW = { centerX: 0, centerY: 18, height: 46 };

function resize() {
  canvas.width = canvas.clientWidth * devicePixelRatio;
  canvas.height = canvas.clientHeight * devicePixelRatio;
}
addEventListener("resize", resize);
resize();
canvas.focus();

const fullscreenButton = document.getElementById("fullscreen");
fullscreenButton.addEventListener("click", async () => {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else await document.documentElement.requestFullscreen();
  } catch {
    /* the host may refuse fullscreen; the cockpit still works inline */
  }
});
addEventListener("fullscreenchange", resize);
canvas.addEventListener("pointerdown", () => canvas.focus());

function scale() {
  return canvas.height / VIEW.height;
}
function px(x, y) {
  const s = scale();
  return [canvas.width / 2 + (x - VIEW.centerX) * s, canvas.height / 2 - (y - VIEW.centerY) * s];
}

function drawRadarGrid() {
  const s = scale();
  ctx.save();
  ctx.strokeStyle = "rgba(70, 255, 160, 0.12)";
  ctx.lineWidth = 1;
  for (let x = -16; x <= 16; x += 2) {
    const [left] = px(x, 0);
    ctx.beginPath();
    ctx.moveTo(left, 0);
    ctx.lineTo(left, canvas.height);
    ctx.stroke();
  }
  for (let y = 0; y <= 70; y += 10) {
    const [, top] = px(0, y);
    ctx.beginPath();
    ctx.moveTo(0, top);
    ctx.lineTo(canvas.width, top);
    ctx.stroke();
  }
  // The horizon and the LZ-1 beam.
  const [, ground] = px(0, 0);
  ctx.fillStyle = "rgba(70, 255, 160, 0.18)";
  ctx.fillRect(0, ground, canvas.width, canvas.height - ground);
  ctx.strokeStyle = "rgba(250, 204, 21, 0.75)";
  ctx.setLineDash([6, 6]);
  const [padLeft] = px(-1.1, 0);
  const [padRight] = px(1.1, 0);
  ctx.beginPath();
  ctx.moveTo(padLeft, ground);
  ctx.lineTo(padLeft, 0);
  ctx.moveTo(padRight, ground);
  ctx.lineTo(padRight, 0);
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.restore();
}

function drawTerrain() {
  const s = scale();
  for (const e of paperboat.entities.values()) {
    if (!e.id.startsWith("terrain-")) continue;
    const [left, top] = px(e.pos[0] - e.size[0] / 2, e.pos[1] + e.size[1] / 2);
    ctx.fillStyle = "rgba(52, 211, 153, 0.28)";
    ctx.fillRect(left, top, e.size[0] * s, e.size[1] * s);
  }
}

function drawLander() {
  const lander = paperboat.entities.get("lander");
  if (!lander) return;
  const s = scale();
  const [cx, cy] = px(lander.pos[0], lander.pos[1]);

  // Thruster flame.
  const flame = paperboat.entities.get("flame");
  if (flame && flame.size[0] > 0.02) {
    const [fx, fy] = px(flame.pos[0], flame.pos[1] - flame.size[1] / 2);
    const width = flame.size[0] * s;
    const height = flame.size[1] * s;
    const gradient = ctx.createLinearGradient(fx, fy, fx, fy + height);
    gradient.addColorStop(0, "rgba(255, 196, 0, 0.95)");
    gradient.addColorStop(0.6, "rgba(255, 96, 0, 0.7)");
    gradient.addColorStop(1, "rgba(255, 96, 0, 0)");
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.moveTo(fx - width / 2, fy);
    ctx.lineTo(fx + width / 2, fy);
    ctx.lineTo(fx, fy + height * 1.5);
    ctx.closePath();
    ctx.fill();
  }

  // Body and cabin.
  ctx.fillStyle = "#cbd5e1";
  ctx.fillRect(cx - 0.31 * s, cy - 0.25 * s, 0.62 * s, 0.5 * s);
  ctx.fillStyle = "#94a3b8";
  ctx.fillRect(cx - 0.17 * s, cy - 0.55 * s, 0.34 * s, 0.24 * s);
  // Legs.
  ctx.strokeStyle = "#71717a";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(cx - 0.24 * s, cy + 0.2 * s);
  ctx.lineTo(cx - 0.46 * s, cy + 0.44 * s);
  ctx.moveTo(cx + 0.24 * s, cy + 0.2 * s);
  ctx.lineTo(cx + 0.46 * s, cy + 0.44 * s);
  ctx.stroke();
}

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#050a08";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  drawRadarGrid();
  drawTerrain();
  drawLander();
  // A small velocity vector at the lander.
  const [cx, cy] = px(paperboat.entities.get("lander")?.pos[0] ?? 0, paperboat.entities.get("lander")?.pos[1] ?? 0);
  ctx.strokeStyle = "rgba(125, 255, 176, 0.8)";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.lineTo(cx + readings.vx * 18, cy - readings.vy * 18);
  ctx.stroke();
  requestAnimationFrame(draw);
}

function setStatus(text, kind) {
  statusEl.textContent = text;
  statusEl.className = "status" + (kind ? " " + kind : "");
}

paperboat
  .on("signal", (m) => {
    const v = Number(m.v);
    if (!Number.isFinite(v)) return;
    if (m.node === "display-alt") readings.alt = v;
    else if (m.node === "display-vy") readings.vy = v;
    else if (m.node === "display-fuel") readings.fuel = v;
    else if (m.node === "ap-switch") readings.ap = v;
    else if (m.node === "display-target") readings.target = v;
    else if (m.node === "lander-1") {
      if (m.port === "vx") readings.vx = v;
      if (m.port === "x") readings.x = v;
    }
    altEl.textContent = readings.alt.toFixed(1);
    vyEl.textContent = `V/S ${readings.vy >= 0 ? "+" : ""}${readings.vy.toFixed(2)} m/s`;
    vxEl.textContent = `H/S ${readings.vx >= 0 ? "+" : ""}${readings.vx.toFixed(2)} m/s`;
    targetEl.textContent = `LZ X ${readings.target >= 0 ? "+" : ""}${readings.target.toFixed(1)} m`;
    fuelEl.textContent = `${readings.fuel.toFixed(1)} kg`;
    fuelBar.style.width = `${Math.max(0, Math.min(100, (readings.fuel / 90) * 100))}%`;
    modeEl.textContent = readings.ap > 0.5 ? "AP" : "MANUAL";
    modeEl.style.color = readings.ap > 0.5 ? "#7dffb0" : "#facc15";
  })
  .on("run.started", () => {
    setStatus("DESCENT", "");
    requestAnimationFrame(resize);
  })
  .on("log", (m) => {
    if (m.text.startsWith("Touchdown")) setStatus("TOUCHDOWN", "landed");
    else if (m.text.startsWith("CRASH")) setStatus("CRASH", "crashed");
  });

// On-screen keys: pointer down/up maps to the same input the bridge forwards for a keyboard.
for (const button of document.querySelectorAll(".keys button")) {
  const key = button.dataset.key;
  const send = (down) => paperboat.input(key, down);
  button.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    button.classList.add("held");
    send(true);
  });
  const release = () => {
    button.classList.remove("held");
    send(false);
  };
  button.addEventListener("pointerup", release);
  button.addEventListener("pointerleave", release);
  button.addEventListener("pointercancel", release);
}

addEventListener("keydown", (event) => {
  if (["KeyW", "KeyA", "KeyD", "KeyP"].includes(event.code)) setStatus("MANUAL INPUT", "");
});

requestAnimationFrame(draw);
