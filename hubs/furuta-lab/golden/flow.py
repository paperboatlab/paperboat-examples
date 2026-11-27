"""The closed-loop flows' check (../example.toml): run the station headless on a flow and print, as JSON,
the figures of merit tools/make_runs.jl gives the bench (results.toml), from the flow's scopes (port a
the encoder, port b the plan). The voltage's last value alone says little: the arm hunts through the
amplifier's dead band (notes/issue-arm-hunting.md), so it depends on the phase of that cycle.

    python3 golden/flow.py <station> --run --psf <flow.psf>
"""

import json
import math
import subprocess
import sys

out = subprocess.run(sys.argv[1:], capture_output=True, text=True)
msgs = [json.loads(line) for line in out.stdout.splitlines() if line.startswith("{")]
status = msgs[-1].get("status") if msgs and msgs[-1].get("type") == "run.finished" else "no run.finished"
if out.returncode or status != "done":
    sys.exit(f"{status} (exit {out.returncode})\n{(out.stderr or out.stdout)[-600:]}")

trace = {}  # (node, port) -> {t: v}
for m in msgs:
    if m.get("type") == "signal" and isinstance(m.get("v"), (int, float)):
        trace.setdefault((m["node"], m.get("port")), {})[m["t"]] = m["v"]
arm, arm_ref = trace[("scope-arm", "a")], trace[("scope-arm", "b")]
pend, pend_ref = trace[("scope-pendulum", "a")], trace[("scope-pendulum", "b")]

after = [t for t in pend if t >= 0.5 and t in pend_ref and t in arm_ref]  # after the catch, as make_runs.jl
e_alpha = [math.degrees(pend[t] - pend_ref[t]) for t in after]
e_theta = [math.degrees(arm[t] - arm_ref[t]) for t in after]
rms = lambda xs: math.sqrt(sum(x * x for x in xs) / len(xs))
print(json.dumps({
    "status": status,
    "max_alpha_err_deg": round(max(map(abs, e_alpha)), 4),
    "rms_alpha_err_deg": round(rms(e_alpha), 4),
    "max_theta_deg": round(math.degrees(max(map(abs, arm.values()))), 4),
    "rms_track_deg": round(rms(e_theta), 4),
    "fell": max(map(abs, pend.values())) > math.radians(30),
}))
