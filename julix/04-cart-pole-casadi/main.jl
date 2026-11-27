# main.jl: a cart-pole swing-up, solved as a nonlinear program with CasADi and Ipopt.
# CasADiNative.jl is CasADi's own Julia binding (registered in General, binaries from CasADi_jll with
# Ipopt), installed in this folder's environment: Project.toml and Manifest.toml pin it. Its API is
# CasADi's Python one, 1-based, with Julia's [x; y] for vertcat.
#
# The problem (M. Kelly, "An introduction to trajectory optimization", 2017): a pole hangs under a
# cart; push the cart (force u) so that in T = 2 s it moves d = 1 m and the pole stands upright,
# with the least ∫u² dt. Direct collocation: the states and forces at N + 1 points are the unknowns,
# the dynamics hold between them by the trapezoid rule.

## The model
import CasADiNative as ca
m₁, m₂, ℓ, g = 1.0, 0.3, 0.5, 9.81            # cart [kg], pole [kg], pole length [m], gravity
T, d, umax, N = 2.0, 1.0, 20.0, 40            # time [s], distance [m], force bound [N], intervals

# s = [x, θ, ẋ, θ̇], θ = 0 hanging down, π upright
function dynamics(s, u)
    θ, θ̇ = s[2], s[4]
    sθ, cθ = sin(θ), cos(θ)
    ẍ = (ℓ * m₂ * sθ * θ̇^2 + u + m₂ * g * cθ * sθ) / (m₁ + m₂ * (1 - cθ^2))
    θ̈ = -(ℓ * m₂ * cθ * sθ * θ̇^2 + u * cθ + (m₁ + m₂) * g * sθ) / (ℓ * m₁ + ℓ * m₂ * (1 - cθ^2))
    [s[3]; s[4]; ẍ; θ̈]
end

## The nonlinear program
h = T / N
w = ca.SX.sym("w", 5 * (N + 1))                # per point k: x, θ, ẋ, θ̇, u
state(k) = w[5k+1:5k+4]
force(k) = w[5k+5]
gaps = [state(k + 1) - state(k) - h / 2 * (dynamics(state(k), force(k)) + dynamics(state(k + 1), force(k + 1)))
        for k in 0:N-1]
cost = sum(h / 2 * (force(k)^2 + force(k + 1)^2) for k in 0:N-1)
nlp = Dict("x" => w, "f" => cost, "g" => vcat(gaps...))
solver = ca.nlpsol("swingup", "ipopt", nlp, Dict("ipopt.print_level" => 0, "print_time" => false,
                                                  "ipopt.sb" => "yes", "expand" => true))

## Bounds and a first guess, then solve
lb, ub, w₀ = Float64[], Float64[], Float64[]
for k in 0:N
    s = k / N
    fix = k == 0 ? [0, 0, 0, 0] : k == N ? [d, π, 0, 0] : nothing
    append!(lb, something(fix, [-2d, -2π, -Inf, -Inf]), -umax)
    append!(ub, something(fix, [2d, 2π, Inf, Inf]), umax)
    append!(w₀, [s * d, s * π, 0, 0], 0)                   # a straight line from start to goal
end
sol = solver(x0 = w₀, lbx = lb, ubx = ub, lbg = 0, ubg = 0)
status = solver.stats()["return_status"]

## The trajectory
W = reshape(Vector{Float64}(sol["x"]), 5, N + 1)
t = range(0, T; length = N + 1)
x, θ, u = W[1, :], W[2, :], W[5, :]
J = Float64(sol["f"])
println(status, ": ∫u² dt = ", J, ", peak force ", maximum(abs, u), " N")

## The figure: run this cell (Ctrl Enter) to see it
using JulixPlot
fig = Figure(; size = (900, 640))
ax1 = Axis(fig[1, 1]; title = "Cart and pole", ylabel = "x [m], θ [rad]")
lines!(ax1, t, x; label = "x")
lines!(ax1, t, θ; label = "θ")
axislegend(ax1; position = :lt)
ax2 = Axis(fig[2, 1]; title = "Force", xlabel = "t [s]", ylabel = "u [N]")
stairs!(ax2, t, u)
fig

## Results, for the golden test (examples' `out/` is not checked in)
using TOML
mkpath("out")
open("out/results.toml", "w") do io
    TOML.print(io, Dict("status" => status, "cost" => J, "u_peak" => maximum(abs, u),
                        "x_max" => maximum(x), "theta_end" => θ[end], "x_end" => x[end]))
end
