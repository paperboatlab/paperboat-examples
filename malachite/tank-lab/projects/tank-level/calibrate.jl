# calibrate.jl: the level sensor against a ruler, 0 to 12 cm (notes/sensor-drift.md: it reads high above
# 8 cm, by 1.5 mm at 12 cm). A straight line can't follow that; a line with a hinge can. Least squares with `\`.

## The calibration table: the ruler, and what the sensor said [cm]
using LinearAlgebra, JulixPlot
ruler   = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0]
reading = [0.008, 0.492, 1.004, 1.500, 1.998, 2.503, 2.997, 3.503, 3.996, 4.505, 4.996, 5.500, 6.005, 6.491, 7.008, 7.495, 7.999, 8.524, 9.031, 9.561, 10.072, 10.595, 11.111, 11.632, 12.151]
err = reading .- ruler

## A straight line, then a line with a hinge at k (k scanned; each fit is one solve)
line = [ones(length(ruler)) ruler] \ reading
hinge(k) = [ones(length(ruler)) ruler max.(ruler .- k, 0)]
sse(k) = norm(hinge(k) * (hinge(k) \ reading) - reading)^2
ks = range(6, 10; length = 81)
k̂ = ks[argmin(sse.(ks))]
β = hinge(k̂) \ reading
rms_line = norm([ones(length(ruler)) ruler] * line - reading) / sqrt(length(ruler))
rms_hinge = sqrt(sse(k̂) / length(ruler))

## The correction: what to subtract from a reading
correct(x) = x - (β[1] + (β[2] - 1) * x + β[3] * max(x - k̂, 0))
x = range(0, 12; length = 200)

## Plot
fig = Figure(; size = (960, 420))
ax1 = Axis(fig[1, 1]; title = "sensor − ruler", xlabel = "ruler [cm]", ylabel = "[cm]")
scatter!(ax1, ruler, err; label = "calibration")
lines!(ax1, x, (line[1] .+ line[2] .* x) .- x; label = "line")
lines!(ax1, x, β[1] .+ (β[2] - 1) .* x .+ β[3] .* max.(x .- k̂, 0); label = "hinge at $(round(k̂; digits = 2)) cm")
axislegend(ax1; position = :lt)
ax2 = Axis(fig[1, 2]; title = "corrected − ruler", xlabel = "ruler [cm]", ylabel = "[cm]")
scatter!(ax2, ruler, correct.(reading) .- ruler)
fig
