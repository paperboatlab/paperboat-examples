# lqr.jl: the balance controller. The model linearized about the upright, discretized at the loop's
# 2 ms, and an LQR gain for it, from the datasheet's parameters (notes/e1-baseline-lqr.md) or the
# identified ones (notes/e4-lqr-identified.md). Ctrl Enter runs the cell at the cursor (a cell starts
# at ##), F5 the whole file. Writes design/out/lqr-<which>.toml, which flows/lqr.psf reads.

## The model and the parameters
include(joinpath(@__DIR__, "..", "model", "furuta.jl"))
which = get(ENV, "LQR_PARAMS", "datasheet")     # or "identified"
file = which == "datasheet" ? joinpath(@__DIR__, "datasheet.toml") : joinpath(@__DIR__, "..", "flows", "out", "identified.toml")
p = merge(load_params(file), (fc = 0.0,))       # Coulomb friction has no linearization: left to the loop

## Linearize about the upright: ẋ = A x + B u
A, B = linearize(p)
poles = eigvals(A)                              # one unstable pole: the pendulum falling

## Discretize at the loop's sample time
Ts = 0.002
Ad, Bd = c2d(A, B, Ts)

## The weights: 1.7° of arm costs as much as 1° of pendulum; rates lightly
Q = Diagonal([100.0, 300.0, 0.3, 0.3])
R = fill(1.0, 1, 1)
K = dlqr(Ad, Bd, Q, R)
closed = abs.(eigvals(Ad - Bd * K))             # all inside the unit circle

## Write the gain for the flow
out = joinpath(@__DIR__, "out", "lqr-$which.toml")
open(out, "w") do io
    println(io, "# design/lqr.jl with $(relpath(file, joinpath(@__DIR__, ".."))): u = -K (x - x_ref), x = [θ, α, θ̇, α̇], Ts = $Ts s")
    println(io, "K = ", repr(round.(vec(K), sigdigits = 5)))
    println(io, "Ts = $Ts")
    println(io, "open_loop_poles = ", repr(round.(real.(poles), digits = 2)))
    println(io, "closed_loop_radius = ", round(maximum(closed), digits = 5))
end
K
