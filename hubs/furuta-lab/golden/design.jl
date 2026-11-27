# The design check (../example.toml): tools/make_runs.jl on a copy of the hub, since it rewrites the
# hub's files in place. Prints the copy's results.toml and the two LQR gains, for golden/design.json.
using TOML
hub = mktempdir()
for d in ("design", "flows", "model", "tools")
    cp(joinpath(@__DIR__, "..", d), joinpath(hub, d))
end
redirect_stdout(devnull) do
    include(joinpath(hub, "tools", "make_runs.jl"))
end
r = TOML.parsefile(joinpath(hub, "results.toml"))
for w in ("datasheet", "identified")
    r["lqr_$w"] = TOML.parsefile(joinpath(hub, "design", "out", "lqr-$w.toml"))
end
# One flat table ("e5_mpc.max_alpha_err_deg" = …): the harness applies its tolerance to top-level results
flat = Dict{String,Any}()
walk(d, p) = for (k, v) in d; v isa AbstractDict ? walk(v, "$p$k.") : (flat["$p$k"] = v) end
walk(r, "")
TOML.print(flat; sorted = true)
