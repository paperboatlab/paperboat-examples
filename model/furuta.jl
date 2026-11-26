# The Furuta pendulum in Julia: the equations of Furuta.mo, for the Julix scripts and the tools.
#
# State x = [θ, α, θ̇, α̇]: the arm's angle, the pendulum's angle from upright (rad), and their rates.
# Input u: the motor voltage (V). Parameters: a NamedTuple read from a TOML file (design/datasheet.toml,
# flows/out/identified.toml).

using LinearAlgebra, TOML

const g = 9.81

"The parameters in `file` as a NamedTuple; `Jp` from the rod when the file leaves it out."
function load_params(file)
    d = TOML.parsefile(file)
    p = (; (Symbol(k) => Float64(v) for (k, v) in d if v isa Real)...)
    haskey(d, "Jp") ? p : merge(p, (Jp = p.mp * p.Lp^2 / 12,))
end

"ẋ = f(x, u): the Lagrange equations of arm and pendulum, with the motor's torque and the friction."
function deriv(x, u, p)
    θ, α, ω, ν = x
    s, c = sincos(α)
    Jr = p.Jr + p.mp * p.Lr^2          # the arm with the pendulum's mass at its tip
    Jp = p.Jp + p.mp * p.lp^2          # the pendulum about its pivot
    h = p.mp * p.Lr * p.lp
    τ = p.km * (u - p.km * ω) / p.Rm - p.Br * ω - p.fc * ω / sqrt(ω^2 + 1e-4)  # Coulomb, smoothed at 0.01 rad/s
    m11, m12, m22 = Jr + Jp * s^2, h * c, Jp
    r1 = τ - 2Jp * s * c * ω * ν + h * s * ν^2
    r2 = Jp * s * c * ω^2 + p.mp * g * p.lp * s - p.Bp * ν
    det = m11 * m22 - m12^2
    [ω, ν, (m22 * r1 - m12 * r2) / det, (m11 * r2 - m12 * r1) / det]
end

"One RK4 step of length h with u held."
function rk4(x, u, p, h)
    k1 = deriv(x, u, p)
    k2 = deriv(x .+ h / 2 .* k1, u, p)
    k3 = deriv(x .+ h / 2 .* k2, u, p)
    k4 = deriv(x .+ h .* k3, u, p)
    x .+ h / 6 .* (k1 .+ 2k2 .+ 2k3 .+ k4)
end

"A, B of ẋ = A x + B u about the upright (x = 0, u = 0), by central differences."
function linearize(p; ε = 1e-6)
    A = zeros(4, 4)
    for j in 1:4
        e = zeros(4); e[j] = ε
        A[:, j] = (deriv(e, 0.0, p) - deriv(-e, 0.0, p)) / 2ε
    end
    B = (deriv(zeros(4), ε, p) - deriv(zeros(4), -ε, p)) / 2ε
    A, reshape(B, 4, 1)
end

"The zero-order-hold discretization of (A, B) at sample time T."
function c2d(A, B, T)
    n, m = size(B)
    E = exp([A B; zeros(m, n + m)] * T)
    E[1:n, 1:n], E[1:n, n+1:n+m]
end

"The discrete LQR gain K (u = -K x) for (Ad, Bd, Q, R), by iterating the Riccati equation."
function dlqr(Ad, Bd, Q, R; iters = 100_000, tol = 1e-12)
    P = copy(Q)
    for _ in 1:iters
        K = (R + Bd' * P * Bd) \ (Bd' * P * Ad)
        Pn = Q + Ad' * P * (Ad - Bd * K)
        norm(Pn - P) < tol * norm(P) && (P = Pn; break)
        P = Pn
    end
    (R + Bd' * P * Bd) \ (Bd' * P * Ad)
end
