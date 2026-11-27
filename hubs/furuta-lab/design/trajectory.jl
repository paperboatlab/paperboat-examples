# trajectory.jl: the reference every closed-loop experiment follows. The arm out to 60°, a hold, and back,
# planned on the linear model through its flat output, so the plan holds the whole state (arm and
# pendulum, angles and rates) and the voltage that drives it: x_ref(t), u_ff(t). The loop then only
# corrects around it. As fast as the model allows with the feedforward within 6 V (4 V kept for the
# loop). Ctrl Enter runs a cell, F5 the file. Writes design/out/trajectory-<which>.csv for the flows.

## The model
include(joinpath(@__DIR__, "..", "model", "furuta.jl"))
which = get(ENV, "LQR_PARAMS", "datasheet")     # or "identified"
file = which == "datasheet" ? joinpath(@__DIR__, "datasheet.toml") : joinpath(@__DIR__, "..", "flows", "out", "identified.toml")
p = merge(load_params(file), (fc = 0.0,))
A, B = linearize(p)

## The flat output y = q x: the state and the input follow from y and its derivatives
W = hcat(B, A * B, A^2 * B, A^3 * B)
q = (W \ Matrix(1.0I, 4, 4))[4:4, :]           # the last row of W⁻¹
Tq = vcat(q, q * A, q * A^2, q * A^3)          # x = Tq⁻¹ [y, ẏ, ÿ, y⃛]
state(Y) = Tq \ Y[1:4]
voltage(Y) = (Y[5] - (q * A^4 * state(Y))[1]) / (q * A^3 * B)[1]

## A move of y: a rest-to-rest step whose first four derivatives vanish at both ends (degree 9)
const C9 = [0, 0, 0, 0, 0, 126, -420, 540, -315, 70]     # coefficients of τ^0…τ^9
poly(c, τ) = sum(c[i] * τ^(i - 1) for i in eachindex(c))
deriv_coeffs(c) = [c[i] * (i - 1) for i in 2:length(c)]
function step_derivs(τ, Tm)
    τ <= 0 && return zeros(5)
    τ >= 1 && return [1.0, 0, 0, 0, 0]
    out, c = zeros(5), Float64.(C9)
    for d in 0:4
        out[d+1] = poly(c, τ) / Tm^d
        c = deriv_coeffs(c)
    end
    out
end

## Out to θ1 at t0, back at t1, each move taking Tm
θ1, t0, t1, T = deg2rad(60), 1.0, 4.0, 7.0
yfinal = q[1] * θ1                              # y at rest with the arm at θ1
Y(t, Tm) = yfinal .* (step_derivs((t - t0) / Tm, Tm) .- step_derivs((t - t1) / Tm, Tm))

## The shortest move with the feedforward within 6 V
peak_u(Tm) = maximum(abs(voltage(Y(t, Tm))) for t in 0:0.002:T)
function shortest(lo = 0.2, hi = 3.0)
    for _ in 1:40
        mid = (lo + hi) / 2
        peak_u(mid) <= 6 ? (hi = mid) : (lo = mid)
    end
    hi
end
Tm = round(shortest(), digits = 2)

## Write it at the loop's rate: t, θ, α, θ̇, α̇, u_ff
Ts = 0.002
peak_alpha = 0.0
open(joinpath(@__DIR__, "out", "trajectory-$which.csv"), "w") do io
    println(io, "t,theta,alpha,omega,nu,u_ff")
    for k in 0:round(Int, T / Ts)
        Yk = Y(k * Ts, Tm)
        x = state(Yk)
        global peak_alpha = max(peak_alpha, abs(x[2]))
        println(io, join(round.([k * Ts; x; voltage(Yk)], sigdigits = 8), ","))
    end
end

## The plan as polynomials for the flows' function blocks: each of θ, α, θ̇, α̇, u_ff is
## yfinal (P(τ_out) - P(τ_back)), τ the move's time clamped to [0, 1]; P's coefficients, τ^0…τ^9
M = inv(Tq)
coeffs = [Float64.(C9)]
for d in 1:4
    push!(coeffs, [deriv_coeffs(coeffs[end]); 0.0])
end
P(w) = sum(w[d+1] .* coeffs[d+1] ./ Tm^d for d in 0:length(w)-1)
wu = ([0, 0, 0, 0, 1] .- [vec(q * A^4 * M); 0]) ./ (q * A^3 * B)[1]
open(joinpath(@__DIR__, "out", "trajectory-$which.toml"), "w") do io
    println(io, "# design/trajectory.jl: the plan as x(t) = yfinal (P(τ_out) - P(τ_back)), τ = clamp((t - t0) / Tm, 0, 1)")
    println(io, "Tm = $Tm\nt0 = $t0\nt1 = $t1\nyfinal = $yfinal")
    for (name, w) in zip(["theta", "alpha", "omega", "nu"], eachrow(M))
        println(io, "$name = ", repr(P(collect(w))))
    end
    println(io, "u_ff = ", repr(P(wu)))
end

## What the plan asks
(Tm = Tm, peak_u = round(peak_u(Tm), digits = 2), peak_alpha_deg = round(rad2deg(peak_alpha), digits = 2))
