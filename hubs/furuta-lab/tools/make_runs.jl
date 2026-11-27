# make_runs.jl: the bench, simulated. Regenerates everything the study reads, in the order the study did it:
#
#   design/out/trajectory-datasheet.csv, lqr-datasheet.toml   Julix (design/trajectory.jl, design/lqr.jl)
#   runs/2026-11-17_e1-lqr-datasheet/              the datasheet LQR on the rig
#   runs/2026-11-18_e2-excitation/                 identification and validation runs
#   flows/greybox.nlp.json, flows/out/identified.toml   the grey-box estimate (tools/identify.jl)
#   design/out/*-identified.*, flows/mpc.json      the redesign on the identified model
#   runs/2026-11-20_e4-lqr-identified/, runs/2026-11-23_e5-mpc/
#   results.toml, media/*.svg                      the numbers and figures the notes and the report quote
#
# julia tools/make_runs.jl (plain Julia 1.11, no packages). Deterministic: fixed seeds.

using Printf
const HUB = normpath(joinpath(@__DIR__, ".."))
include(joinpath(HUB, "tools", "rig.jl"))
include(joinpath(HUB, "tools", "controllers.jl"))
include(joinpath(HUB, "tools", "identify.jl"))
include(joinpath(HUB, "tools", "svgplot.jl"))

run_dir(name) = mkpath(joinpath(HUB, "runs", name))
const T_CLOSED = 7.0
const X0_UP = [0.0, deg2rad(2.0), 0.0, 0.0]     # caught by hand 2° off upright

function write_run(file, log; every = 1, header = "t,u,theta,alpha")
    open(file, "w") do io
        println(io, header)
        for k in 1:every:length(log.t)
            @printf(io, "%.4f,%.4f,%.6f,%.6f\n", log.t[k], log.u[k], log.θ[k], log.α[k])
        end
    end
end

"The closed-loop figures of merit of a balance run against its reference, after the catch (t ≥ 0.5 s)."
function metrics(log, ref)
    ks = findall(>=(0.5), log.t)
    eθ = [log.θ[k] - ref(log.t[k])[1][1] for k in ks]
    eα = [log.α[k] - ref(log.t[k])[1][2] for k in ks]
    (max_alpha_err_deg = maximum(abs.(rad2deg.(eα))),
     rms_alpha_err_deg = sqrt(sum(abs2, rad2deg.(eα)) / length(eα)),
     max_theta_deg = maximum(abs.(rad2deg.(log.θ))),
     rms_track_deg = sqrt(sum(abs2, rad2deg.(eθ)) / length(eθ)),
     saturated_pct = 100 * count(>=(RIG["u_max"]), abs.(log.u)) / length(log.u),
     past_limit_s = count(>(deg2rad(90)), abs.(log.θ)) * (log.t[2] - log.t[1]),
     fell = maximum(abs.(log.α)) > deg2rad(30))
end

"""
The excitation: the arm on a gentle PD around a chirp, a ±2 V PRBS on the voltage, the pendulum hanging.
The PRBS is a hash of the 150 ms slot and the seed, so flows/excite.psf's function block makes the same one.
"""
prbs(t, seed) = (x = sin((floor(t / 0.15) + 1000seed) * 12.9898) * 43758.5453; 2.0 * sign(x - floor(x) - 0.5))
chirp(t; T = 20.0) = deg2rad(30) * sin(2π * (0.2t + (2.5 - 0.2) * t^2 / (2T)))

function excitation(; seed, Ts = 0.002)
    est = rate_filter(Ts)
    (t, θ, α) -> (x = est(θ, α); 4.0 * (chirp(t) - x[1]) - 0.08 * x[3] + prbs(t, seed))
end

"The fit (%) of simulating the excitation loop on parameters p against a recorded run's angles."
function validation_fit(p, seed, recorded)
    ctrl = excitation(seed = seed)
    x = [0.0, π, 0.0, 0.0]; Ts, h = 0.002, 0.0005
    θ, α = Float64[], Float64[]
    for k in 0:length(recorded.t)-1
        u = ctrl(k * Ts, counts(x[1]), counts(x[2]))
        push!(θ, x[1]); push!(α, x[2])
        for _ in 1:4
            x = rk4(x, clamp(u, -10, 10), p, h)
        end
    end
    fit(y, ŷ) = 100 * (1 - norm(y .- ŷ) / norm(y .- sum(y) / length(y)))
    (theta = fit(recorded.θ, θ), alpha = fit(recorded.α, α), θ = θ, α = α)
end

lqr_gain(file) = reshape(Float64.(TOML.parsefile(file)["K"]), 1, 4)

function main()
    results = Dict{String,Any}()
    pd = load_params(joinpath(HUB, "design", "datasheet.toml"))

    # Julix: the trajectory and the datasheet LQR
    ENV["LQR_PARAMS"] = "datasheet"
    traj = include(joinpath(HUB, "design", "trajectory.jl"))
    include(joinpath(HUB, "design", "lqr.jl"))
    ref = load_reference(joinpath(HUB, "design", "out", "trajectory-datasheet.csv"))
    results["trajectory_datasheet"] = Dict("move_s" => traj.Tm, "peak_alpha_deg" => traj.peak_alpha_deg, "peak_u_ff" => traj.peak_u)

    # E1: the datasheet LQR on the rig
    K1 = lqr_gain(joinpath(HUB, "design", "out", "lqr-datasheet.toml"))
    e1 = run_rig(lqr_controller(K1, ref), X0_UP, T_CLOSED)
    write_run(joinpath(run_dir("2026-11-17_e1-lqr-datasheet"), "run.csv"), e1)

    # E2: excitation, one run to fit and one to validate
    d2 = run_dir("2026-11-18_e2-excitation")
    ident = run_rig(excitation(seed = 1), [0.0, π, 0.0, 0.0], 20.0)
    valid = run_rig(excitation(seed = 2), [0.0, π, 0.0, 0.0], 20.0)
    write_run(joinpath(d2, "identification.csv"), ident)
    write_run(joinpath(d2, "validation.csv"), valid)

    # E3: the grey-box estimate, and how both models replay the validation run
    pi_, x, se = identify(joinpath(d2, "identification.csv"))
    rec = read_run(joinpath(d2, "validation.csv"))
    vd, vi = validation_fit(pd, 2, rec), validation_fit(pi_, 2, rec)
    results["identification"] = Dict(
        "estimate" => Dict(n => getfield(pi_, Symbol(n)) for n in NAMES),
        "stderr" => Dict(n => se[i] * scales(pd)[i] for (i, n) in enumerate(NAMES)),
        "datasheet" => Dict(n => getfield(pd, Symbol(n)) for n in NAMES),
        "fit_theta_pct" => Dict("datasheet" => vd.theta, "identified" => vi.theta),
        "fit_alpha_pct" => Dict("datasheet" => vd.alpha, "identified" => vi.alpha))

    # E4: the LQR redesigned on the identified model
    ENV["LQR_PARAMS"] = "identified"
    traj4 = include(joinpath(HUB, "design", "trajectory.jl"))
    include(joinpath(HUB, "design", "lqr.jl"))
    ref4 = load_reference(joinpath(HUB, "design", "out", "trajectory-identified.csv"))
    results["trajectory_identified"] = Dict("move_s" => traj4.Tm, "peak_alpha_deg" => traj4.peak_alpha_deg, "peak_u_ff" => traj4.peak_u)
    K4 = lqr_gain(joinpath(HUB, "design", "out", "lqr-identified.toml"))
    e4 = run_rig(lqr_controller(K4, ref4), X0_UP, T_CLOSED)
    write_run(joinpath(run_dir("2026-11-20_e4-lqr-identified"), "run.csv"), e4)

    # E5: MPC on the identified model, the control toolkit's mpc block at 5 ms
    m = mpc_model(pi_)
    open(joinpath(HUB, "flows", "mpc.json"), "w") do io
        rows(M) = "[" * join(["[" * join(round.(M[i, :], sigdigits = 10), ", ") * "]" for i in 1:size(M, 1)], ", ") * "]"
        println(io, "{")
        println(io, "  \"\$comment\": \"The identified model (flows/out/identified.toml) linearized about the upright and discretized at $(m.Ts) s; x = [θ, α, θ̇, α̇], u in V. Written by tools/make_runs.jl.\",")
        println(io, "  \"A\": ", rows(m.A), ",")
        println(io, "  \"B\": ", rows(m.B), ",")
        println(io, "  \"Q\": ", rows(m.Q), ",")
        println(io, "  \"R\": ", rows(m.R), ",")
        println(io, "  \"N\": $(m.N),")
        println(io, "  \"u_min\": [$(m.u_min)],")
        println(io, "  \"u_max\": [$(m.u_max)]")
        println(io, "}")
    end
    e5 = run_rig(mpc_controller(m, ref4), X0_UP, T_CLOSED; Ts = m.Ts)
    write_run(joinpath(run_dir("2026-11-23_e5-mpc"), "run.csv"), e5)

    # The numbers the notes quote
    for (name, log, r) in (("e1_lqr_datasheet", e1, ref), ("e4_lqr_identified", e4, ref4), ("e5_mpc", e5, ref4))
        results[name] = Dict(String(k) => (v isa Bool ? v : round(v, sigdigits = 4)) for (k, v) in pairs(metrics(log, r)))
    end
    open(joinpath(HUB, "results.toml"), "w") do io
        println(io, "# Written by tools/make_runs.jl: every number the notes and the report quote.")
        TOML.print(io, results; sorted = true)
    end

    # The figures
    media = mkpath(joinpath(HUB, "media"))
    deg(v) = rad2deg.(v)
    err(log, r, i) = deg([(i == 1 ? log.θ[k] : log.α[k]) - r(log.t[k])[1][i] for k in eachindex(log.t)])
    svgplot(joinpath(media, "e1-arm.svg"), e1.t, [deg([ref(t)[1][1] for t in e1.t]), deg(e1.θ)];
            labels = ["arm reference", "arm θ"], ylabel = "θ (°)", title = "E1 · the arm under the datasheet LQR")
    w = findall(t -> 10 <= t <= 14, rec.t)
    svgplot(joinpath(media, "e3-validation.svg"), rec.t[w], [deg(rec.α[w]) .- 180, deg(vd.α[w]) .- 180, deg(vi.α[w]) .- 180];
            labels = ["recorded", "datasheet model", "identified model"], ylabel = "α − 180 (°)", title = "E3 · the validation run replayed, 10–14 s")
    svgplot(joinpath(media, "pendulum-error.svg"), e1.t, [err(e1, ref, 2), err(e4, ref4, 2), err(e5, ref4, 2)]; ts = [e1.t, e4.t, e5.t],
            labels = ["E1 datasheet LQR", "E4 identified LQR", "E5 MPC"], ylabel = "α − α_ref (°)", title = "The pendulum off its plan, same arm move")
    svgplot(joinpath(media, "arm-error.svg"), e1.t, [err(e1, ref, 1), err(e4, ref4, 1), err(e5, ref4, 1)]; ts = [e1.t, e4.t, e5.t],
            labels = ["E1 datasheet LQR", "E4 identified LQR", "E5 MPC"], ylabel = "θ − θ_ref (°)", title = "The arm off its plan")
    include(joinpath(HUB, "tools", "make_flows.jl"))
    results
end

results = main()
for k in ("e1_lqr_datasheet", "e4_lqr_identified", "e5_mpc")
    println(rpad(k, 20), results[k])
end
println(results["identification"]["fit_theta_pct"], " ", results["identification"]["fit_alpha_pct"])
