# The loops the flows build, in Julia, for the bench (tools/make_runs.jl):
#   - rates from the encoders: a discrete derivative through a 40 Hz first-order lag (flows' derivative + lag),
#   - the reference: design/out/trajectory-<which>.csv, the state to follow and the feedforward voltage,
#   - lqr: u = u_ff - K (x - x_ref) at 2 ms (flows/lqr.psf: state_feedback),
#   - mpc: the control toolkit's mpc block at 5 ms on the deviation x - x_ref (flows/mpc.psf, model
#     flows/mpc.json), its u added to u_ff: the condensed QP over the horizon with box bounds on u, and the
#     block's one-step latency (it outputs the last u, then solves).

include(joinpath(@__DIR__, "..", "model", "furuta.jl"))

"The reference from a trajectory CSV (t, θ, α, θ̇, α̇, u_ff), held between samples: t -> (x_ref, u_ff)."
function load_reference(file)
    rows = [parse.(Float64, split(l, ',')) for l in Iterators.drop(eachline(file), 1)]
    dt = rows[2][1] - rows[1][1]
    τ -> (r = rows[clamp(1 + floor(Int, τ / dt + 1e-9), 1, length(rows))]; (r[2:5], r[6]))
end

"A state estimate from the encoders: [θ, α, θ̇, α̇], rates through a first-order lag at fc Hz."
function rate_filter(Ts; fc = 40.0)
    a = exp(-2π * fc * Ts)
    prev = nothing
    ω, ν = 0.0, 0.0
    (θ, α) -> begin
        if prev !== nothing
            ω = a * ω + (1 - a) * (θ - prev[1]) / Ts
            ν = a * ν + (1 - a) * (α - prev[2]) / Ts
        end
        prev = (θ, α)
        [θ, α, ω, ν]
    end
end

"State feedback around the reference: u = u_ff - K (x - x_ref), at Ts."
function lqr_controller(K, ref; Ts = 0.002)
    est = rate_filter(Ts)
    (t, θ, α) -> ((xr, uff) = ref(t); uff - (K * (est(θ, α) - xr))[1])
end

"The mpc block's condensed problem: H, and the maps from x0 and ref to its linear term."
function condense(A, B, Q, R, N)
    n, m = size(B)
    Φ = reduce(vcat, [A^k for k in 0:N-1])
    Γ = zeros(n * N, m * N)
    for k in 0:N-1, j in 0:k-1
        Γ[k*n+1:(k+1)*n, j*m+1:(j+1)*m] = A^(k - 1 - j) * B
    end
    Qb = kron(Matrix(1.0I, N, N), Q)
    Rb = kron(Matrix(1.0I, N, N), R)
    H = Rb + Γ' * Qb * Γ
    (H = Symmetric(H), F = Γ' * Qb, Φ = Φ, n = n, N = N)
end

"min ½U'HU + f'U with lo ≤ U ≤ hi: the unconstrained minimum when it fits, else projected gradient
(accelerated) from it, then on the bounds it pins, Newton on the free part, until the set settles."
function box_qp(H, f, lo, hi; iters = 2000)
    U = -(H \ f)
    all(lo .<= U .<= hi) && return U
    L = eigmax(H)
    U = clamp.(U, lo, hi); Y = copy(U); t = 1.0
    for _ in 1:iters
        Un = clamp.(Y .- (H * Y .+ f) ./ L, lo, hi)
        tn = (1 + sqrt(1 + 4t^2)) / 2
        Y = Un .+ ((t - 1) / tn) .* (Un .- U)
        U, t = Un, tn
    end
    for _ in 1:20  # polish: fix the active bounds, solve the rest exactly
        g = H * U .+ f
        act = [(U[i] <= lo + 1e-9 && g[i] > 0) || (U[i] >= hi - 1e-9 && g[i] < 0) for i in eachindex(U)]
        free = .!act
        Un = copy(U)
        Un[free] = -(H[free, free] \ (f[free] .+ H[free, act] * U[act]))
        Un = clamp.(Un, lo, hi)
        Un == U && break
        U = Un
    end
    U
end

"The mpc block on the deviation: every Ts it outputs u_ff plus the u solved at the previous step, then solves."
function mpc_controller(model, ref; Ts = 0.005)
    c = condense(model.A, model.B, model.Q, model.R, model.N)
    est = rate_filter(Ts)
    U = zeros(model.N)
    last = 0.0
    (t, θ, α) -> begin
        xr, uff = ref(t)
        out = uff + last
        U = box_qp(c.H, c.F * (c.Φ * (est(θ, α) - xr)), model.u_min, model.u_max)
        last = U[1]
        out
    end
end

"The MPC's model for the mpc block (flows/mpc.json) from parameters p."
function mpc_model(p; Ts = 0.005, N = 80)
    A, B = linearize(merge(p, (fc = 0.0,)))
    Ad, Bd = c2d(A, B, Ts)
    (A = Ad, B = Bd, Q = Matrix(Diagonal([100.0, 300.0, 0.3, 0.3])), R = fill(1.0, 1, 1), N = N, u_min = -4.0, u_max = 4.0, Ts = Ts)  # the headroom the trajectory leaves
end
