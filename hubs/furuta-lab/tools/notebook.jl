# notebook.jl: what the notes' cells call. `figures(run, trajectory)` reads a closed-loop run and the
# plan it followed and gives the figures of merit of notes/hypothesis.md, after the catch (t ≥ 0.5 s).
# Plain Julia.

function read_csv(file)
    lines = collect(eachline(file))
    names = Symbol.(split(lines[1], ','))
    cols = [Float64[] for _ in names]
    for l in lines[2:end], (i, v) in enumerate(split(l, ','))
        push!(cols[i], parse(Float64, v))
    end
    NamedTuple{Tuple(names)}(Tuple(cols))
end

function figures(run_file, trajectory_file)
    r, p = read_csv(run_file), read_csv(trajectory_file)
    dt = p.t[2] - p.t[1]
    at(t) = clamp(1 + floor(Int, t / dt + 1e-9), 1, length(p.t))
    ks = findall(>=(0.5), r.t)              # after the catch
    eθ = [rad2deg(r.theta[k] - p.theta[at(r.t[k])]) for k in ks]
    eα = [rad2deg(r.alpha[k] - p.alpha[at(r.t[k])]) for k in ks]
    rms(v) = sqrt(sum(abs2, v) / length(v))
    (max_alpha_err = round(maximum(abs.(eα)), digits = 2),
     rms_alpha_err = round(rms(eα), digits = 2),
     rms_track = round(rms(eθ), digits = 2),
     max_theta = round(maximum(abs.(rad2deg.(r.theta))), digits = 1),
     saturated_pct = round(100 * count(>=(10), abs.(r.u)) / length(r.u), digits = 1),
     peak_u = round(maximum(abs.(r.u)), digits = 1))
end
