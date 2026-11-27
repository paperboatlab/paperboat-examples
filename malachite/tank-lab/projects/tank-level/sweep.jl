# sweep.jl: the level loop simulated (a gravity-drained tank, its pump on a PI controller) and swept
# over the gains: where is the overshoot small and the level settled soon? The gains in use come from
# notes/pump-check.md (kp 40, ki 2).

## The plant and the loop
const A, a, g = 600.0, 0.5, 981.0   # tank area [cm²], outlet area [cm²], gravity [cm/s²]
const qmax = 400.0                  # pump flow at 100 % [cm³/s]

# the level after the setpoint steps to `r` at 0 s: PI on the pump, limited to `umax` %
function simulate(kp, ki; r = 5.0, T = 120.0, dt = 0.05, umax = 60.0)
    n = round(Int, T / dt)
    t, h = collect(range(0, T; length = n + 1)), zeros(n + 1)
    integral = 0.0
    for k in 1:n
        e = r - h[k]
        u = kp * e + ki * integral
        if 0 < u < umax              # integrate only while the pump isn't saturated (anti-windup)
            integral += e * dt
        end
        q = qmax * clamp(u, 0, umax) / 100
        h[k + 1] = max(h[k] + dt * (q - a * sqrt(2g * h[k])) / A, 0)
    end
    t, h
end
overshoot_of(h; r = 5.0) = max(maximum(h) - r, 0) / r
settling_of(t, h; r = 5.0, band = 0.02) = t[something(findlast(x -> abs(x - r) > band * r, h), 1)]

## The sweep
kps = range(5, 80; length = 31)
kis = range(0.25, 5; length = 31)
OS = [overshoot_of(simulate(kp, ki)[2]) for kp in kps, ki in kis]
TS = [settling_of(simulate(kp, ki)...) for kp in kps, ki in kis]
best = argmin(ifelse.(OS .< 0.1, TS, Inf))   # the soonest settled with under 10 % overshoot
kp★, ki★ = kps[best[1]], kis[best[2]]

## Plot
fig = Figure(; size = (1000, 460))
ax1 = Axis(fig[1, 1]; title = "overshoot [%]", xlabel = "kp", ylabel = "ki")
hm = heatmap!(ax1, kps, kis, 100 .* OS; colormap = :viridis)
Colorbar(fig[1, 2], hm)
scatter!(ax1, [40.0, kp★], [2.0, ki★]; color = :white, markersize = 10)
ax2 = Axis(fig[1, 3]; title = "level at 5 cm", xlabel = "t [s]", ylabel = "[cm]")
for (kp, ki) in ((10.0, 0.5), (40.0, 2.0), (kp★, ki★))
    lines!(ax2, simulate(kp, ki)...; label = "kp $(round(kp; digits = 1)), ki $(round(ki; digits = 2))")
end
axislegend(ax2; position = :rb)
fig
