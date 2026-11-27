# identify.jl: the closed-loop step at 5 cm (runs/2026-11-17_14-01, see notes/step-response-5cm.md)
# fitted with a damped second-order model. Ctrl Enter runs the cell at the cursor (a cell starts at ##),
# Shift Enter a line, F5 the whole file.

## Load the step test
using JulixPlot
csv = collect(eachline("runs/2026-11-17_14-01/level.csv"))[2:end]
t = [parse(Float64, split(l, ',')[1]) for l in csv]
h = [parse(Float64, split(l, ',')[2]) for l in csv]
peak, ipeak = findmax(h)
overshoot = (peak - 5) / 5

## The model: the setpoint moves to 5 cm at 10 s; the level follows θ seconds later
function response(t, K, ζ, ωn, θ)
    s = t - 10 - θ
    s <= 0 && return 0.0
    ωd = ωn * sqrt(1 - ζ^2)
    K * (1 - exp(-ζ * ωn * s) * (cos(ωd * s) + ζ / sqrt(1 - ζ^2) * sin(ωd * s)))
end
J(p) = 0 < p[2] < 0.99 && p[3] > 0 && p[4] >= 0 ? sum(abs2, h .- response.(t, p...)) : Inf

## Fit: Nelder–Mead, written out (no package needed)
function nelder_mead(f, x0; δ = 0.2 .* abs.(x0) .+ 0.05, iters = 5000, tol = 1e-12)
    n = length(x0)
    pts = [x0 .+ (i == 0 ? 0.0 : δ[i]) .* ((1:n) .== i) for i in 0:n]
    vals = f.(pts)
    for it in 1:iters
        o = sortperm(vals)
        pts, vals = pts[o], vals[o]
        vals[end] - vals[1] < tol && return (x = pts[1], J = vals[1], iterations = it)
        c = sum(pts[1:n]) ./ n
        xr = c .+ (c .- pts[end]); fr = f(xr)
        if fr < vals[1]
            xe = c .+ 2 .* (c .- pts[end]); fe = f(xe)
            pts[end], vals[end] = fe < fr ? (xe, fe) : (xr, fr)
        elseif fr < vals[n]
            pts[end], vals[end] = xr, fr
        else
            xc = c .+ 0.5 .* (pts[end] .- c); fc = f(xc)
            if fc < vals[end]
                pts[end], vals[end] = xc, fc
            else
                pts = [pts[1] .+ 0.5 .* (p .- pts[1]) for p in pts]
                vals = f.(pts)
            end
        end
    end
    (x = pts[1], J = vals[1], iterations = iters)
end
fit = nelder_mead(J, [5.0, 0.6, 0.15, 1.0])
K̂, ζ̂, ω̂, θ̂ = fit.x
r = h .- response.(t, fit.x...)

## The cost around the fit: ζ against ωn, with K and θ held at theirs
ζs = range(0.3, 0.9; length = 50)
ωs = range(0.06, 0.3; length = 50)
C = [J([K̂, ζ, ω, θ̂]) for ζ in ζs, ω in ωs]

## Plot
fig = Figure(; size = (960, 720))
ax1 = Axis(fig[1, 1:2]; title = "Step at 5 cm", xlabel = "t [s]", ylabel = "level [cm]")
scatter!(ax1, t, h; label = "measured", markersize = 3)
lines!(ax1, t, response.(t, fit.x...); label = "fit", linewidth = 2)
axislegend(ax1; position = :rb)
ax2 = Axis(fig[2, 1]; title = "residual", xlabel = "t [s]", ylabel = "[cm]")
lines!(ax2, t, r)
ax3 = Axis3(fig[2, 2]; title = "log J(ζ, ωn)", xlabel = "ζ", ylabel = "ωn")
surface!(ax3, ζs, ωs, log10.(C); colormap = :viridis)
fig
