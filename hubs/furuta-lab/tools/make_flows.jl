# make_flows.jl: writes Simplicial's flows (flows/*.psf, format 1) from the design's outputs, so a flow
# carries the gain and the plan the notes quote. Each is a child of the station folder stations/furuta-rig
# (not the packed .pst): a block's file param resolves against the station's folder, so the mpc and nlp
# blocks reach flows/mpc.json and flows/greybox.nlp.json only from the station's place in the hub.
#
#   e1-lqr-datasheet.psf, e4-lqr-identified.psf   the balance loop: plan, encoders, rates, state feedback
#   mpc.psf                                       the same with the control toolkit's mpc block (flows/mpc.json)
#   excite.psf                                    E2's excitation, the pendulum hanging; variable `seed`
#   estimate.psf                                  E3: a Step flow, the nlp block on flows/greybox.nlp.json
#
# The plan's state and feedforward are `function` blocks: yfinal (P(τ_out) - P(τ_back)), the polynomials
# design/trajectory.jl wrote to design/out/trajectory-<which>.toml.

using TOML

const FLOWS = joinpath(@__DIR__, "..", "flows")
const DESIGN_OUT = joinpath(@__DIR__, "..", "design", "out")

num(x) = repr(round(x, sigdigits = 12))
horner(c, v) = foldr((ci, acc) -> "$(num(ci)) + $v*($acc)", c[1:end-1]; init = num(c[end]))

station_header() = Dict("name" => "furuta-rig", "version" => "0.1.0", "path" => "../stations/furuta-rig")

node(id, type, pos; params...) = Dict("id" => id, "type" => type, "pos" => collect(pos), "params" => Dict(String(k) => v for (k, v) in params))
edge(a, b) = Dict("from" => collect(a), "to" => collect(b))

"The plan, the encoders and the rates: what every balance flow shares. Returns nodes and edges."
function plan_and_state(which)
    tr = TOML.parsefile(joinpath(DESIGN_OUT, "trajectory-$which.toml"))
    Tm, t0, t1, yf = tr["Tm"], tr["t0"], tr["t1"], tr["yfinal"]
    q = 2π / 8192
    nodes = [
        node("rig-1", "rig", (760, 160)),
        node("tau-out", "function", (0, 0); f = "clamp((t - $(num(t0))) / $(num(Tm)), 0, 1)"),
        node("tau-back", "function", (0, 80); f = "clamp((t - $(num(t1))) / $(num(Tm)), 0, 1)"),
        [node("plan-$n", "function", (220, 60i); f = "$(num(yf)) * (($(horner(tr[n], "a"))) - ($(horner(tr[n], "b"))))")
         for (i, n) in enumerate(["theta", "alpha", "omega", "nu", "u_ff"])]...,
        node("x-ref", "mux", (440, 60); names = "theta alpha omega nu", units = "rad rad rad/s rad/s"),
        node("enc-theta", "quantizer", (980, 120); interval = q),
        node("enc-alpha", "quantizer", (980, 200); interval = q),
        node("d-theta", "discrete_derivative", (1160, 120)),
        node("d-alpha", "discrete_derivative", (1160, 200)),
        node("rate-theta", "lag", (1340, 120); tau = 1 / (2π * 40)),
        node("rate-alpha", "lag", (1340, 200); tau = 1 / (2π * 40)),
        node("x", "mux", (1520, 160); names = "theta alpha omega nu", units = "rad rad rad/s rad/s"),
        node("error", "sum", (1700, 120); signs = "+-"),
        node("scope-arm", "scope", (1160, 320); inputs = 2),
        node("scope-pendulum", "scope", (1160, 440); inputs = 2),
    ]
    edges = [
        [edge(("tau-out", "y"), ("plan-$n", "a")) for n in ["theta", "alpha", "omega", "nu", "u_ff"]]...,
        [edge(("tau-back", "y"), ("plan-$n", "b")) for n in ["theta", "alpha", "omega", "nu", "u_ff"]]...,
        [edge(("plan-$n", "y"), ("x-ref", n)) for n in ["theta", "alpha", "omega", "nu"]]...,
        edge(("rig-1", "theta"), ("enc-theta", "u")), edge(("rig-1", "alpha"), ("enc-alpha", "u")),
        edge(("enc-theta", "y"), ("d-theta", "u")), edge(("enc-alpha", "y"), ("d-alpha", "u")),
        edge(("d-theta", "y"), ("rate-theta", "u")), edge(("d-alpha", "y"), ("rate-alpha", "u")),
        edge(("enc-theta", "y"), ("x", "theta")), edge(("enc-alpha", "y"), ("x", "alpha")),
        edge(("rate-theta", "y"), ("x", "omega")), edge(("rate-alpha", "y"), ("x", "nu")),
        edge(("x", "y"), ("error", "a")), edge(("x-ref", "y"), ("error", "b")),
        edge(("enc-theta", "y"), ("scope-arm", "a")), edge(("plan-theta", "y"), ("scope-arm", "b")),
        edge(("enc-alpha", "y"), ("scope-pendulum", "a")), edge(("plan-alpha", "y"), ("scope-pendulum", "b")),
    ]
    nodes, edges
end

"The loop's output: feedback (a 1-vector at `port` of `id`) plus the feedforward, to the rig."
function close_loop!(nodes, edges, id, port)
    push!(nodes, node("u-fb", "demux", (2060, 120); names = "v"), node("cmd", "sum", (2240, 160); signs = "++"),
          node("graph-u", "graph", (2420, 240)))
    push!(edges, edge((id, port), ("u-fb", "u")), edge(("u-fb", "v"), ("cmd", "a")), edge(("plan-u_ff", "y"), ("cmd", "b")),
          edge(("cmd", "y"), ("rig-1", "cmd")), edge(("cmd", "y"), ("graph-u", "in")))
end

function write_flow(name, flow; overrides = Dict(), variables = [], run)
    doc = Dict{String,Any}("paperboat" => 1, "station" => station_header(), "flow" => flow, "run" => run)
    isempty(overrides) || (doc["overrides"] = overrides)
    isempty(variables) || (doc["variables"] = variables)
    open(joinpath(FLOWS, name), "w") do io
        print(io, json(doc))
        println(io)
    end
end

"A minimal JSON writer (Julia has no JSON stdlib): Dict, Vector, String, Number, Bool."
json(x::AbstractString) = "\"" * replace(x, "\\" => "\\\\", "\"" => "\\\"") * "\""
json(x::Bool) = x ? "true" : "false"
json(x::Integer) = string(x)
json(x::Real) = repr(Float64(x))
json(x::AbstractVector) = "[" * join(json.(x), ", ") * "]"
json(x::AbstractDict) = "{" * join(["$(json(String(k))): $(json(v))" for (k, v) in sort(collect(x); by = first)], ", ") * "}"

function lqr_flow(which)
    nodes, edges = plan_and_state(which)
    K = TOML.parsefile(joinpath(DESIGN_OUT, "lqr-$which.toml"))["K"]
    push!(nodes, node("lqr", "state_feedback", (1880, 120); K = "[" * join(num.(K), ", ") * "]"))
    push!(edges, edge(("error", "y"), ("lqr", "x")))
    close_loop!(nodes, edges, "lqr", "u")
    Dict("flow" => "signal", "nodes" => nodes, "edges" => edges)
end

function mpc_flow()
    nodes, edges = plan_and_state("identified")
    push!(nodes, node("mpc", "mpc", (1880, 120); file = "../../flows/mpc.json"))
    push!(edges, edge(("error", "y"), ("mpc", "y")))
    close_loop!(nodes, edges, "mpc", "u")
    Dict("flow" => "signal", "nodes" => nodes, "edges" => edges)
end

function excite_flow()
    q = 2π / 8192
    drive = "4*(0.5235987756*sin(2*pi*(0.2*t + 0.0575*t^2)) - th) - 0.08*w + 2*sign(frac(sin((floor(t/0.15) + 1000*seed)*12.9898)*43758.5453) - 0.5)"
    nodes = [
        node("rig-1", "rig", (520, 120)),
        node("seed", "variable", (0, 200); name = "seed"),
        node("drive", "function", (260, 120); f = drive),
        node("enc-theta", "quantizer", (760, 80); interval = q),
        node("enc-alpha", "quantizer", (760, 200); interval = q),
        node("d-theta", "discrete_derivative", (940, 0)),
        node("rate-theta", "lag", (1120, 0); tau = 1 / (2π * 40)),
        node("graph-theta", "graph", (940, 120)),
        node("graph-alpha", "graph", (940, 240)),
        node("graph-u", "graph", (520, 320)),
    ]
    edges = [
        edge(("seed", "y"), ("drive", "seed")), edge(("drive", "y"), ("rig-1", "cmd")), edge(("drive", "y"), ("graph-u", "in")),
        edge(("rig-1", "theta"), ("enc-theta", "u")), edge(("rig-1", "alpha"), ("enc-alpha", "u")),
        edge(("enc-theta", "y"), ("d-theta", "u")), edge(("d-theta", "y"), ("rate-theta", "u")),
        edge(("enc-theta", "y"), ("drive", "th")), edge(("rate-theta", "y"), ("drive", "w")),
        edge(("enc-theta", "y"), ("graph-theta", "in")), edge(("enc-alpha", "y"), ("graph-alpha", "in")),
    ]
    Dict("flow" => "signal", "nodes" => nodes, "edges" => edges)
end

function estimate_flow()
    nodes = [node("start", "start", (0, 0)), node("nlp", "nlp", (200, 0); file = "../../flows/greybox.nlp.json", tol = 1e-9, max_iter = 500),
             node("say", "say", (420, 0); text = "x = [mp, lp, Br, Bp, km, fc] over the datasheet's (fc over 1e-3 N m)")]
    edges = [edge(("start", "next"), ("nlp", "in")), edge(("nlp", "out"), ("say", "in")), edge(("nlp", "x"), ("say", "value"))]
    Dict("flow" => "step", "nodes" => nodes, "edges" => edges)
end

balance_run = Dict("dt" => 0.002, "duration" => 7.0, "solver" => "rk4")
write_flow("e1-lqr-datasheet.psf", lqr_flow("datasheet"); run = balance_run)
write_flow("e4-lqr-identified.psf", lqr_flow("identified"); run = balance_run)
write_flow("mpc.psf", mpc_flow(); run = merge(balance_run, Dict("dt" => 0.005)))
write_flow("excite.psf", excite_flow();
           overrides = Dict("objects" => Dict("rig-1" => Dict("props" => Dict("alpha0" => float(π))))),
           variables = [Dict("name" => "seed", "type" => "number", "value" => 1)],
           run = Dict("dt" => 0.002, "duration" => 20.0, "solver" => "rk4"))
write_flow("estimate.psf", estimate_flow(); run = Dict("duration" => 600.0))
