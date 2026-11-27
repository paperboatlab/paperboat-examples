# main.jl: a notebook. In Julix a script is a notebook: a line that starts with ## opens a cell.
#   Ctrl Enter   runs the cell at the cursor, Shift Enter the line (or the selection), F5 the file
#   the console  (Ctrl J) runs an expression in the same session; ↑ recalls, Tab completes
# Run the cells top to bottom and watch Variables fill in; a cell's last value shows beside it, and
# anything that shows itself as SVG or PNG becomes a figure. Errors point at this file and line,
# wherever the code ran from.

## A step response, "measured"
# A tank's level after a step at t = 5 s: first order, gain K and time constant τ, plus some
# deterministic ripple standing in for sensor noise (so the fit below is the same on every run).
t = collect(range(0, 60; length = 200))
response(K, τ) = @. K * (1 - exp(-max(t - 5, 0) / τ))
h = response(4.97, 14.2) .+ 0.05 .* sin.(37 .* t .+ cos.(11 .* t))

## A coarse fit on a grid
J(K, τ) = sum(abs2, h .- response(K, τ))
Ks, τs = range(3, 7; length = 41), range(8, 30; length = 45)
i = argmin([J(K, τ) for K in Ks, τ in τs])
K₀, τ₀ = Ks[i[1]], τs[i[2]]

## Refine it with Gauss-Newton
# The residual's Jacobian by hand: ∂r/∂K and ∂r/∂τ for r = response(K, τ) - h
function gauss_newton(K, τ; steps = 10)
    for _ in 1:steps
        s = @. max(t - 5, 0)
        e = @. exp(-s / τ)
        r = response(K, τ) .- h
        Jm = [(1 .- e) (@. -K * s / τ^2 * e)]
        K, τ = [K, τ] .- (Jm' * Jm) \ (Jm' * r)
    end
    K, τ
end
K̂, τ̂ = gauss_newton(K₀, τ₀)
rms = sqrt(J(K̂, τ̂) / length(t))

## A figure without a package: a type that draws itself as SVG
struct Line
    x::Vector{Float64}
    y::Vector{Float64}
    title::String
end
Base.show(io::IO, l::Line) = print(io, "Line(\"", l.title, "\")")   # how it prints in the console

function Base.show(io::IO, ::MIME"image/svg+xml", l::Line)
    w, ht, m = 480, 300, 40
    sx(v) = m + (v - minimum(l.x)) / (maximum(l.x) - minimum(l.x)) * (w - 2m)
    sy(v) = ht - m - (v - minimum(l.y)) / (maximum(l.y) - minimum(l.y)) * (ht - 2m)
    pts = join(("$(round(sx(a); digits = 1)),$(round(sy(b); digits = 1))" for (a, b) in zip(l.x, l.y)), " ")
    print(io, """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 $w $ht" width="$w" height="$ht">
      <rect width="$w" height="$ht" fill="#0d0d0d"/>
      <path d="M$m $m V$(ht - m) H$(w - m)" stroke="#555" fill="none"/>
      <text x="$(w ÷ 2)" y="24" fill="#eee" font-family="sans-serif" font-size="14" text-anchor="middle">$(l.title)</text>
      <polyline points="$pts" fill="none" stroke="#cdbbf6" stroke-width="2"/>
    </svg>""")
end

## The fit, as a figure: run this cell alone (Ctrl Enter); its last value is shown
Line(t, response(K̂, τ̂), "Fit: K = $(round(K̂; digits = 2)), τ = $(round(τ̂; digits = 1)) s")

## display() makes a figure too, mid-cell
for τ in (5.0, 20.0)
    display(Line(t, response(K̂, τ), "τ = $τ s"))
end

## A slow loop you can interrupt (Stop in the bar, or Ctrl C in the console)
total = 0.0
for k in 1:5
    global total += k^2
    println("step ", k, ": total = ", total)
    sleep(0.2)
end

## An error, to see where it points: uncomment the call and run this cell
f(x) = x > 2 ? error("x is too large: $x") : x
# f(3)

## Results, for the golden test (examples' `out/` is not checked in)
using TOML
mkpath("out")
open("out/results.toml", "w") do io
    TOML.print(io, Dict("K_grid" => K₀, "tau_grid" => τ₀, "K" => K̂, "tau" => τ̂, "rms" => rms,
                        "draws_svg" => length(repr(MIME"image/svg+xml"(), Line(t, h, "measured"))) > 0,
                        "total" => total))
end
