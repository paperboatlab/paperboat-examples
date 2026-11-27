# The grey-box identification (notes/e3-greybox.md): the equations of motion, with six unknown physical
# parameters, fitted to the excitation run by equation error.
#
#   - Rates and accelerations come from the encoders by a Savitzky–Golay filter (cubic, 62 ms window);
#     the voltage goes through the same filter.
#   - At 200 instants the two equations' residuals are written out as Simplicial's problem,
#     flows/greybox.nlp.json, which flows/estimate.psf solves with the nlp block (Ipopt).
#   - The same sum of squares is minimised here by Levenberg–Marquardt, so the hub's numbers don't
#     need Ipopt to be checked: flows/out/identified.toml.
#
# Known (measured, not fitted): Lr, Jr, Lp, Rm. Fitted: mp, lp, Br, Bp, km, fc, each scaled by its
# datasheet value (x = 1 is the datasheet; fc by 1e-3 N m).

include(joinpath(@__DIR__, "..", "model", "furuta.jl"))

const NAMES = ["mp", "lp", "Br", "Bp", "km", "fc"]

"The run's columns: t, u, θ, α (CSV with a header)."
function read_run(file)
    rows = [parse.(Float64, split(l, ',')) for l in Iterators.drop(eachline(file), 1)]
    (t = getindex.(rows, 1), u = getindex.(rows, 2), θ = getindex.(rows, 3), α = getindex.(rows, 4))
end

"Savitzky–Golay: the signal's value, 1st and 2nd derivatives at each sample (cubic over 2m+1)."
function savgol(y, T; m = 15)
    V = [Float64(i)^j for i in -m:m, j in 0:3]
    C = (V' * V) \ V'                   # rows: the polynomial's coefficients from the window
    n = length(y)
    f, d1, d2 = fill(NaN, n), fill(NaN, n), fill(NaN, n)
    for k in m+1:n-m
        c = C * y[k-m:k+m]
        f[k], d1[k], d2[k] = c[1], c[2] / T, 2c[3] / T^2
    end
    f, d1, d2
end

"The scales: x .* scale are the physical values."
scales(pd) = [pd.mp, pd.lp, pd.Br, pd.Bp, pd.km, 1e-3]

"The two equations' residuals at one instant, for scaled parameters x (as numbers)."
function residuals(x, s, known, sample)
    mp, lp, Br, Bp, km, fc = x .* s
    (; Lr, Jr, Lp, Rm) = known
    θ, α, ω, ν, θdd, αdd, u = sample
    Jp = mp * Lp^2 / 12 + mp * lp^2
    h = mp * Lr * lp
    sa, ca = sincos(α)
    τ = km * (u - km * ω) / Rm - Br * ω - fc * ω / sqrt(ω^2 + 1e-4)
    e1 = (Jr + mp * Lr^2 + Jp * sa^2) * θdd + h * ca * αdd - (τ - 2Jp * sa * ca * ω * ν + h * sa * ν^2)
    e2 = h * ca * θdd + Jp * αdd - (Jp * sa * ca * ω^2 + mp * g * lp * sa - Bp * ν)
    (e1, e2 / mp)  # the pendulum's equation per unit mass: else shrinking mp shrinks its error
end

"The same residuals as expression text in x(1)…x(6), for the nlp block."
function residual_text(s, known, sample)
    f(v) = repr(round(v, sigdigits = 10))
    mp, lp, Br, Bp, km, fc = ("(x($i)*$(f(s[i])))" for i in 1:6)
    (; Lr, Jr, Lp, Rm) = known
    θ, α, ω, ν, θdd, αdd, u = f.(sample)
    sa, ca, s2, sc = f(sin(sample[2])), f(cos(sample[2])), f(sin(sample[2])^2), f(sin(sample[2]) * cos(sample[2]))
    Jp = "($mp*$(f(Lp^2 / 12))+$mp*$lp^2)"
    h = "($mp*$(f(Lr))*$lp)"
    τ = "($km*($u-$km*$ω)/$(f(Rm))-$Br*$ω-$fc*$(f(sample[3] / sqrt(sample[3]^2 + 1e-4))))"
    e1 = "(($(f(Jr))+$mp*$(f(Lr^2))+$Jp*$s2)*$θdd+$h*$ca*$αdd-($τ-2*$Jp*$sc*$ω*$ν+$h*$sa*$(f(sample[4]^2))))"
    e2 = "(($h*$ca*$θdd+$Jp*$αdd-($Jp*$sc*$(f(sample[3]^2))+$mp*$(f(g))*$lp*$sa-$Bp*$ν))/$mp)"
    e1, e2
end

"The samples the fit uses: every `every`-th one, away from the filter's edges."
function samples(run; every = 50)
    T = run.t[2] - run.t[1]
    θ, ω, θdd = savgol(run.θ, T)
    α, ν, αdd = savgol(run.α, T)
    u = savgol(run.u, T)[1]  # the voltage through the same filter, so it matches the smoothed accelerations
    ks = [k for k in 1:every:length(run.t) if !isnan(θdd[k])]
    [(θ[k], α[k], ω[k], ν[k], θdd[k], αdd[k], u[k]) for k in ks]
end

"Levenberg–Marquardt on the stacked residuals, each equation weighted by `w`."
function fit(S, s, known, w; x0 = ones(6), iters = 200)
    r(x) = reduce(vcat, [collect(residuals(x, s, known, q)) .* w for q in S])
    x = copy(x0)
    λ = 1e-3
    cost = sum(abs2, r(x))
    for _ in 1:iters
        J = reduce(hcat, [(r(x .+ 1e-6 .* (1:6 .== j)) .- r(x .- 1e-6 .* (1:6 .== j))) ./ 2e-6 for j in 1:6])
        e = r(x)
        while true
            step = -(J' * J + λ * Diagonal(diag(J' * J))) \ (J' * e)
            xn = x .+ step
            cn = sum(abs2, r(xn))
            if cn < cost
                x, cost, λ = xn, cn, λ / 3
                break
            end
            λ *= 4
            λ > 1e10 && return x, cost, J
        end
        norm(J' * e) < 1e-12 && break
    end
    J = reduce(hcat, [(r(x .+ 1e-6 .* (1:6 .== j)) .- r(x .- 1e-6 .* (1:6 .== j))) ./ 2e-6 for j in 1:6])
    x, cost, J
end

"""
Identify from the run at `file`: writes flows/greybox.nlp.json and flows/out/identified.toml,
returns the identified parameters and the scaled estimate with its standard errors.
"""
function identify(file; hub = joinpath(@__DIR__, ".."))
    pd = load_params(joinpath(hub, "design", "datasheet.toml"))
    known = (Lr = pd.Lr, Jr = pd.Jr, Lp = pd.Lp, Rm = pd.Rm)
    s = scales(pd)
    S = samples(read_run(file))
    # weight each equation by its residual's spread at the datasheet, so both count
    e0 = [residuals(ones(6), s, known, q) for q in S]
    w = [1 / sqrt(sum(abs2, first.(e0)) / length(S)), 1 / sqrt(sum(abs2, last.(e0)) / length(S))]

    # Simplicial's problem: the same weighted sum of squares, as text
    terms = String[]
    for q in S
        e1, e2 = residual_text(s, known, q)
        push!(terms, "($(repr(w[1]))*$e1)^2", "($(repr(w[2]))*$e2)^2")
    end
    lb, ub = [0.5, 0.5, 0.1, 0.1, 0.5, 0.0], [2.0, 2.0, 10.0, 10.0, 2.0, 20.0]
    open(joinpath(hub, "flows", "greybox.nlp.json"), "w") do io
        println(io, "{")
        println(io, "  \"\$comment\": \"Written by tools/identify.jl from $(relpath(file, hub)): the equation error at $(length(S)) instants, x = [mp, lp, Br, Bp, km, fc] over their datasheet values (fc over 1e-3 N m).\",")
        println(io, "  \"fun\": \"", join(terms, " + "), "\",")
        println(io, "  \"x0\": [1, 1, 1, 1, 1, 0],")
        println(io, "  \"lb\": ", repr(lb), ",")
        println(io, "  \"ub\": ", repr(ub), ",")
        println(io, "  \"options\": { \"display\": \"iter\" }")
        println(io, "}")
    end

    x, cost, J = fit(S, s, known, w; x0 = [1, 1, 1, 1, 1, 0.0])
    σ2 = cost / (2length(S) - 6)
    se = sqrt.(diag(inv(J' * J)) .* σ2)
    p = merge(pd, NamedTuple{Tuple(Symbol.(NAMES))}(Tuple(x .* s)))
    open(joinpath(hub, "flows", "out", "identified.toml"), "w") do io
        println(io, "# Identified by flows/estimate.psf (and tools/identify.jl, the same problem) from $(relpath(file, hub)).")
        println(io, "# The fitted ones carry their standard error; the others are the datasheet's (measured).")
        for k in ["Lr", "Jr", "mp", "Lp", "lp", "Br", "Bp", "Rm", "km", "fc"]
            i = findfirst(==(k), NAMES)
            v = getfield(p, Symbol(k))
            println(io, rpad("$k = $(round(v, sigdigits = 4))", 20), i === nothing ? "# measured" : "# ± $(round(se[i] * s[i], sigdigits = 2))")
        end
    end
    p, x, se
end
