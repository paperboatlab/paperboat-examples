// Draws the runner's world from the engine's entities: the runner (id "runner"), crates
// and bars ("obstacle-N"; a bar hangs above the ground). Positions are metres; the view
// follows the same window the built-in 2D scene would (centre [5, 2.5], 8 m high).
"use strict";

const canvas = document.getElementById("view");
const status = document.getElementById("status");
const ctx = canvas.getContext("2d");
const VIEW = { cx: 5, cy: 2.5, height: 8 };
let started = 0; // wall-clock start of the current run, for the scrolling ground

function resize() {
  canvas.width = canvas.clientWidth * devicePixelRatio;
  canvas.height = canvas.clientHeight * devicePixelRatio;
}
addEventListener("resize", resize);
resize();

// World metres → canvas pixels.
function scale() {
  return canvas.height / VIEW.height;
}
function px(x, y) {
  const s = scale();
  return [canvas.width / 2 + (x - VIEW.cx) * s, canvas.height / 2 - (y - VIEW.cy) * s];
}

function paperRect(x, y, w, h, fill, fold) {
  // A cut-paper box: flat fill, a darker folded corner and a soft shadow.
  const [left, top] = px(x - w / 2, y + h / 2);
  const s = scale();
  ctx.fillStyle = "rgba(68, 64, 60, 0.12)";
  ctx.fillRect(left + 4, top + 4, w * s, h * s);
  ctx.fillStyle = fill;
  ctx.fillRect(left, top, w * s, h * s);
  const f = Math.min(w, h) * s * 0.3;
  ctx.fillStyle = fold;
  ctx.beginPath();
  ctx.moveTo(left + w * s - f, top);
  ctx.lineTo(left + w * s, top + f);
  ctx.lineTo(left + w * s - f, top + f);
  ctx.fill();
}

function drawGround(time) {
  const [, groundY] = px(0, 0);
  ctx.fillStyle = "#d6cbb8";
  ctx.fillRect(0, groundY, canvas.width, canvas.height - groundY);
  // Dashes that scroll at the obstacles' speed (6 m/s) while a run goes.
  ctx.fillStyle = "#b8ab94";
  const s = scale();
  const offset = ((time * 6) % 1.5) * s;
  for (let x = -offset; x < canvas.width; x += 1.5 * s) ctx.fillRect(x, groundY + 0.25 * s, 0.6 * s, 0.06 * s);
}

function drawHills(time) {
  // Far paper hills drift slower than the ground (parallax).
  const s = scale();
  const [, groundY] = px(0, 0);
  ctx.fillStyle = "#e7dccb";
  const offset = ((time * 1.2) % 9) * s;
  for (let x = -offset - 2 * s; x < canvas.width + 9 * s; x += 9 * s) {
    ctx.beginPath();
    ctx.moveTo(x, groundY);
    ctx.quadraticCurveTo(x + 4.5 * s, groundY - 3.2 * s, x + 9 * s, groundY);
    ctx.fill();
  }
}

function drawRunner(e, time) {
  // A folded-paper runner: a triangle body that squashes when ducking, two stick legs.
  const s = scale();
  const h = e.size[1] * (e.scale ? e.scale[1] : 1);
  const w = e.size[0];
  const [cx, cy] = px(e.pos[0], e.pos[1]);
  const top = cy - (h / 2) * s;
  const bottom = cy + (h / 2) * s;
  const stride = Math.sin(time * 18) * 0.12 * s;
  ctx.strokeStyle = "#292524";
  ctx.lineWidth = 0.05 * s;
  ctx.beginPath();
  ctx.moveTo(cx - 0.08 * s, bottom - 0.05 * s);
  ctx.lineTo(cx - 0.08 * s + stride, bottom + 0.0 * s);
  ctx.moveTo(cx + 0.08 * s, bottom - 0.05 * s);
  ctx.lineTo(cx + 0.08 * s - stride, bottom + 0.0 * s);
  ctx.stroke();
  ctx.fillStyle = "#1e3a5f";
  ctx.beginPath();
  ctx.moveTo(cx - (w / 2) * s, bottom - 0.1 * s);
  ctx.lineTo(cx + (w / 2) * s, bottom - 0.1 * s);
  ctx.lineTo(cx + 0.1 * s, top);
  ctx.closePath();
  ctx.fill();
  ctx.fillStyle = "#3b5f8a"; // the fold
  ctx.beginPath();
  ctx.moveTo(cx + 0.1 * s, top);
  ctx.lineTo(cx + (w / 2) * s, bottom - 0.1 * s);
  ctx.lineTo(cx + 0.05 * s, bottom - 0.1 * s);
  ctx.closePath();
  ctx.fill();
  ctx.fillStyle = "#fef3c7"; // an eye
  ctx.beginPath();
  ctx.arc(cx + 0.12 * s, top + (h * 0.35) * s, 0.045 * s, 0, Math.PI * 2);
  ctx.fill();
}

function draw() {
  const time = paperboat.state.running ? (performance.now() - started) / 1000 : 0;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#f4efe6";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  drawHills(time);
  drawGround(time);
  for (const e of paperboat.entities.values()) {
    if (!e.id.startsWith("obstacle-")) continue;
    const bar = e.pos[1] - e.size[1] / 2 > 0.1;
    if (bar) {
      paperRect(e.pos[0], e.pos[1], e.size[0], e.size[1], "#9ca3af", "#6b7280");
      // the bar's strings up to the sky
      const [l, t] = px(e.pos[0] - e.size[0] / 2 + 0.05, e.pos[1] + e.size[1] / 2);
      const [r] = px(e.pos[0] + e.size[0] / 2 - 0.05, 0);
      ctx.strokeStyle = "#a8a29e";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(l, t);
      ctx.lineTo(l, 0);
      ctx.moveTo(r, t);
      ctx.lineTo(r, 0);
      ctx.stroke();
    } else {
      paperRect(e.pos[0], e.pos[1], e.size[0], e.size[1], "#c2703d", "#9a4f22");
    }
  }
  const runner = paperboat.entities.get("runner");
  if (runner) drawRunner(runner, time);
  requestAnimationFrame(draw);
}

paperboat
  .on("run.started", () => {
    started = performance.now();
    status.textContent = "running";
    status.className = "";
  })
  .on("log", (m) => {
    if (m.text.startsWith("crashed")) {
      status.textContent = m.text;
      status.className = "crashed";
    } else if (m.text.startsWith("made it")) {
      status.textContent = m.text;
      status.className = "won";
    }
  })
  .on("run.finished", (m) => {
    if (m.status !== "done") status.textContent = m.status;
  });

requestAnimationFrame(draw);
