# main.jl: a figure you can pan, zoom and orbit, drawn with JulixPlot (Makie's API, no GPU).
# JulixPlot is in this folder's environment (Project.toml, Manifest.toml), pinned; Julix shows a figure
# whenever a cell's last value is one, or a script calls display(fig).
# 2D axes pan (drag), zoom (wheel, or a box), read values (hover), compare two cursors (A/B);
# the 3D axis orbits (drag), zooms (wheel) and snaps to a side from its view cube.

## Data: a first-order step response, measured with ripple
using JulixPlot
t = range(0, 60; length = 300)
response(K, τ) = @. K * (1 - exp(-max(t - 5, 0) / τ))
h = response(4.97, 14.2) .+ 0.05 .* sin.(37 .* t .+ cos.(11 .* t))   # deterministic "noise"

## The fit and its cost surface
J(K, τ) = sum(abs2, h .- response(K, τ))
Ks = range(3, 7; length = 41)
τs = range(8, 30; length = 45)
C = [J(K, τ) for K in Ks, τ in τs]
i = argmin(C)
K̂, τ̂ = Ks[i[1]], τs[i[2]]

## The figure: run this cell (Ctrl Enter) to see it
fig = Figure(; size = (900, 680))
ax1 = Axis(fig[1, 1:2]; title = "Step at 5 s", xlabel = "t [s]", ylabel = "level [cm]")
scatter!(ax1, t, h; label = "measured", markersize = 4)
lines!(ax1, t, response(K̂, τ̂); label = "fit", linewidth = 2)
axislegend(ax1; position = :rb)
ax2 = Axis(fig[2, 1]; title = "residual", xlabel = "t [s]")
lines!(ax2, t, h .- response(K̂, τ̂))
ax3 = Axis3(fig[2, 2]; title = "J(K, τ)", xlabel = "K", ylabel = "τ")
surface!(ax3, Ks, τs, log.(C); colormap = :viridis)
fig

## Save it: SVG, PNG, PDF, EPS or HTML, by the file's extension
mkpath("out")
save("out/step.svg", fig)

## Results, for the golden test (examples' `out/` is not checked in)
using TOML
open("out/results.toml", "w") do io
    TOML.print(io, Dict("K" => K̂, "tau" => τ̂, "J_min" => C[i],
                        "axes" => axes_count(fig), "plots" => plot_count(fig),
                        "svg_saved" => filesize("out/step.svg") > 0))
end
