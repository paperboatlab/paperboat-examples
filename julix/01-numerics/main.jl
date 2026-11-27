# main.jl: numerics with Julia's standard library only, the first Julix example.
# Run it all (F5), or one cell at a time: put the cursor in a cell and press Ctrl Enter
# (a cell starts at a line beginning with ##). Every name you define appears under Variables;
# the console (Ctrl J) works on the same session.

## Matrices and linear algebra
using LinearAlgebra
A = [4.0 1 0; 1 3 1; 0 1 2]          # a symmetric 3 × 3 matrix
b = [1.0, 2, 3]
x = A \ b                            # solves A x = b
residual = norm(A * x - b)
λ, V = eigen(A)                      # A V = V Λ, λ ascending

## A damped pendulum, integrated with a fixed-step Runge-Kutta
# θ'' = -(g/ℓ) sin θ - c θ', from 1 rad at rest, for 10 s
pendulum(s; g = 9.81, ℓ = 1.0, c = 0.5) = [s[2], -(g / ℓ) * sin(s[1]) - c * s[2]]

function rk4(f, s, h, n)
    for _ in 1:n
        k1 = f(s); k2 = f(s + h / 2 * k1); k3 = f(s + h / 2 * k2); k4 = f(s + h * k3)
        s = s + h / 6 * (k1 + 2k2 + 2k3 + k4)
    end
    s
end

h = 1e-3
θ_end, ω_end = rk4(pendulum, [1.0, 0.0], h, round(Int, 10 / h))

## Results, for the golden test (examples' `out/` is not checked in)
using TOML
mkpath("out")
open("out/results.toml", "w") do io
    TOML.print(io, Dict("x" => x, "residual" => residual, "eigenvalues" => λ,
                        "theta_end" => θ_end, "omega_end" => ω_end))
end
println("x = ", x, ", θ(10 s) = ", θ_end)
