using LinearAlgebra
using Ripserer
using JSON3

function rips_filtration(D; threshold=Inf)
    r = Rips(D, threshold=threshold)
    n = size(D, 1)

    edges_ = collect(Ripserer.edges(r))
    tris_  = collect(Ripserer.columns_to_reduce(r, edges_))

    simplices = vcat(
        [[i] for i in 1:n],
        [sort(collect(Ripserer.vertices(e))) for e in edges_],
        [sort(collect(Ripserer.vertices(t))) for t in tris_],
    )
    births = vcat(
        zeros(Float64, n),
        [Float64(birth(e)) for e in edges_],
        [Float64(birth(t)) for t in tris_],
    )

    order = sortperm(births)
    return simplices[order], births[order]
end

function show_filtration(simplices, births)
    println("Simplex filtration (1-indexed vertices):")
    for (s, b) in zip(simplices, births)
        println("  $s -> $(round(b, digits=6))")
    end
end

function write_filtration_json(simplices, births, path)
    open(path, "w") do f
        JSON3.write(f, Dict("simplices" => simplices, "appears_at" => births))
    end
end

D = [sqrt((x1-x2)^2 + (y1-y2)^2)
     for (x1,y1) in [(1,0),(2,0),(1,1),(2,1)],
         (x2,y2) in [(1,0),(2,0),(1,1),(2,1)]]

simplices, births = rips_filtration(D, threshold=1.5)
show_filtration(simplices, births)
write_filtration_json(simplices, births, "filtration.json")

