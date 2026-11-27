# svgplot.jl: a line chart as a standalone SVG, for the notes (media/). The series take the kit's
# series slots in order (@paperboatlab/ui tokens.css --series-1…3, validated light and dark), 2 px lines,
# a legend and a label at each line's end; the grid and axes stay recessive. Dark follows the system.

using Printf

const SERIES_LIGHT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
const SERIES_DARK = ["#3987e5", "#d95926", "#199e70", "#c98500"]

function nice_ticks(lo, hi; n = 5)
    span = hi - lo
    step = 10.0^floor(log10(span / n))
    for m in (1, 2, 2.5, 5, 10)
        span / (m * step) <= n && (step *= m; break)
    end
    collect(ceil(lo / step)*step:step:floor(hi / step)*step)
end

esc(s) = replace(s, "&" => "&amp;", "<" => "&lt;", ">" => "&gt;")

"""
svgplot(file, t, ys; ts = fill(t, length(ys)), labels, ylabel, title): one line per series in `ys`
(at times `ts[i]`), written to `file`.
"""
function svgplot(file, t, ys; ts = fill(t, length(ys)), labels, ylabel, title, W = 720, H = 300)
    l, r, top, b = 56, 150, 52, 40
    pw, ph = W - l - r, H - top - b
    xlo, xhi = minimum(minimum.(ts)), maximum(maximum.(ts))
    ylo, yhi = minimum(minimum.(ys)), maximum(maximum.(ys))
    pad = 0.06 * (yhi - ylo + eps())
    ylo, yhi = ylo - pad, yhi + pad
    X(v) = l + pw * (v - xlo) / (xhi - xlo)
    Y(v) = top + ph * (1 - (v - ylo) / (yhi - ylo))
    io = IOBuffer()
    println(io, """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 $W $H" width="$W" height="$H" role="img" aria-label="$(esc(title))">""")
    println(io, "<style>")
    println(io, "text{font:12px 'Geist',system-ui,sans-serif;fill:#555}.title{font-weight:600;fill:#1a1a1a}.grid{stroke:#e6e6e6}.axis{stroke:#bdbdbd}.bg{fill:#fff}")
    for i in eachindex(ys)
        println(io, ".s$i{stroke:$(SERIES_LIGHT[i]);fill:none;stroke-width:2;stroke-linejoin:round}.k$i{fill:$(SERIES_LIGHT[i])}")
    end
    println(io, "@media (prefers-color-scheme: dark){text{fill:#a8a8a8}.title{fill:#ededed}.grid{stroke:#2e2e2e}.axis{stroke:#4a4a4a}.bg{fill:#191919}")
    for i in eachindex(ys)
        println(io, ".s$i{stroke:$(SERIES_DARK[i])}.k$i{fill:$(SERIES_DARK[i])}")
    end
    println(io, "}</style>")
    println(io, """<rect class="bg" width="$W" height="$H"/>""")
    println(io, """<text class="title" x="$l" y="20">$(esc(title))</text>""")
    # legend, one row under the title
    x = l
    for (i, lab) in enumerate(labels)
        println(io, """<rect class="k$i" x="$x" y="30" width="14" height="3" rx="1.5"/><text x="$(x + 20)" y="35">$(esc(lab))</text>""")
        x += 28 + 7 * length(lab)
    end
    for v in nice_ticks(ylo, yhi)
        @printf(io, "<line class=\"grid\" x1=\"%d\" x2=\"%d\" y1=\"%.1f\" y2=\"%.1f\"/>", l, l + pw, Y(v), Y(v))
        @printf(io, "<text x=\"%d\" y=\"%.1f\" text-anchor=\"end\">%s</text>\n", l - 6, Y(v) + 4, string(round(v, digits = 2)) |> s -> replace(s, r"\.0$" => ""))
    end
    for v in nice_ticks(xlo, xhi; n = 8)
        @printf(io, "<text x=\"%.1f\" y=\"%d\" text-anchor=\"middle\">%s</text>", X(v), top + ph + 18, replace(string(v), r"\.0$" => ""))
    end
    println(io, """<line class="axis" x1="$l" x2="$(l + pw)" y1="$(top + ph)" y2="$(top + ph)"/>""")
    println(io, """<text x="$(l + pw)" y="$(H - 6)" text-anchor="end">t (s)</text>""")
    println(io, """<text x="12" y="$(top + ph / 2)" transform="rotate(-90 12 $(top + ph / 2))" text-anchor="middle">$(esc(ylabel))</text>""")
    ends = Float64[]
    for (i, y) in enumerate(ys)
        tt = ts[i]
        step = max(1, length(tt) ÷ 1400)
        pts = join([@sprintf("%.1f,%.1f", X(tt[k]), Y(y[k])) for k in 1:step:length(tt)], " ")
        println(io, """<polyline class="s$i" points="$pts"/>""")
        push!(ends, Y(y[end]))
    end
    # direct labels at the right, nudged apart; none when the lines end together (the legend names them)
    order = sortperm(ends)
    together = length(ends) > 1 && minimum(diff(ends[order])) < 14
    together && (println(io, "</svg>"); write(file, take!(io)); return)
    placed = Float64[]
    for i in order
        yv = isempty(placed) ? ends[i] : max(ends[i], placed[end] + 14)
        push!(placed, yv)
        println(io, """<text x="$(l + pw + 8)" y="$(yv + 4)">$(esc(labels[i]))</text>""")
    end
    println(io, "</svg>")
    write(file, take!(io))
end
