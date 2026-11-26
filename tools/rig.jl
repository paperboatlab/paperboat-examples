# The bench, simulated: the stand-in for the real rig that recorded runs/. The true parameters and
# what the model leaves out (dead band, saturation, encoder counts, delay, end stops) are in rig.toml.

include(joinpath(@__DIR__, "..", "model", "furuta.jl"))

const RIG = TOML.parsefile(joinpath(@__DIR__, "rig.toml"))
const TRUTH = load_params(joinpath(@__DIR__, "rig.toml"))

"ẋ of the rig: the model's equations with the truth's parameters, plus the end stops."
function rig_deriv(x, u, p)
    d = deriv(x, u, p)
    over = abs(x[1]) - RIG["stop"]
    if over > 0  # a stiff rubber stop: 5 N m/rad and some damping
        τ = -sign(x[1]) * 5.0 * over - 0.02 * x[3]
        d[3] += τ / (p.Jr + p.mp * p.Lr^2)
    end
    d
end

function rig_rk4(x, u, p, h)
    k1 = rig_deriv(x, u, p)
    k2 = rig_deriv(x .+ h / 2 .* k1, u, p)
    k3 = rig_deriv(x .+ h / 2 .* k2, u, p)
    k4 = rig_deriv(x .+ h .* k3, u, p)
    x .+ h / 6 .* (k1 .+ 2k2 .+ 2k3 .+ k4)
end

"What the amplifier gives for a command: the dead band, then saturation."
amp(u) = clamp(abs(u) <= RIG["deadband"] ? 0.0 : u - sign(u) * RIG["deadband"], -RIG["u_max"], RIG["u_max"])

"An encoder's reading of angle a: whole counts."
counts(a) = round(a * RIG["counts"] / 2π) * 2π / RIG["counts"]

"""
Run the rig for `T` seconds from `x0`. Every `Ts` the controller sees the encoders and the time,
`controller(t, θ, α) -> u` (V, before the amplifier); the voltage arrives `delay` later. Returns the
log at the control rate: t, the commanded u, the encoders' θ and α, and the true state.
"""
function run_rig(controller, x0, T; Ts = 0.002, h = 0.0005)
    x = copy(x0)
    steps = round(Int, T / Ts)
    sub = round(Int, Ts / h)
    lag = round(Int, RIG["delay"] / h)
    queue = zeros(lag + 1)      # the voltages on their way, one per substep
    log = (t = Float64[], u = Float64[], θ = Float64[], α = Float64[], x = Vector{Float64}[])
    for k in 0:steps-1
        t = k * Ts
        θm, αm = counts(x[1]), counts(x[2])
        u = controller(t, θm, αm)
        push!(log.t, t); push!(log.u, u); push!(log.θ, θm); push!(log.α, αm); push!(log.x, copy(x))
        for _ in 1:sub
            queue = [queue[2:end]; amp(u)]
            x = rig_rk4(x, queue[1], TRUTH, h)
        end
    end
    log
end
