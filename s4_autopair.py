import csv
import random
import time

import backend

seed = time.time()
print 'Seed = %r' % seed
print
random.seed(seed)

standings = 'data/s4_standings_week2.csv'

# Correct the names of racers who have inconsistent names.
forbid_fix = {
    'angelica': 'angelica_seikai',
}

# Racers who have dropped from the tournament (lowercase)
omit = set( ['otherrobert', 'ognos'] )

# How many matches played per week,
# and players who are playing a different number
# this week.
weekly_matches = 2
exceptions = {
    'echaen': 4,
    'iamdaman00': 0,
}

nrounds = 12

rdr = csv.reader(file(standings))
rows = list(rdr)
point_map = {}
forbid_map = {}
all_forbid = set()
racers = []
unlower_racer = {}
for row in rows[4:]:
    racer = row[1].strip()
    unlower_racer[racer.lower()] = racer
    if racer.lower() in omit:
        print 'Skipping %s' % racer
        continue
    if row[0] == '' or racer == '':
        print 'Skipping blank row'
        continue

    print row
    points = int( float(row[2]) * 2 )
    point_map[racer.lower()] = points
    racers.append(racer)

    prev = row[3 + nrounds:]
    forbid = []
    for name in prev:
        name = name.strip().lower()
        if name in forbid_fix:
            name = forbid_fix[name]
        if name != '' and '--' not in name:
            forbid.append(name)
    forbid = set(forbid)
    forbid_map[racer.lower()] = forbid
    all_forbid |= forbid

    print '%s has %d points and previously played %s' % (racer, points, prev)
print

racers_lower = set(r.lower() for r in racers)
for name in all_forbid:
    if name not in omit and name not in racers_lower:
        print 'Unknown name in forbid set: %s' % name
for name in exceptions:
    if name not in racers_lower:
        print 'Unknown name  in exceptions: %s' % name

print 'Read %d eligible racers' % len(racers)
print

# Convert between vertex tuple and integer index.
# vertex: (lowercase racer name, match number)
int_of_vertex = {}
vertex_of_int = {}
n_vertices = 0
for r in racers:
    r = r.lower()
    for m in range(exceptions.get(r, weekly_matches)):
        v = (r, m)
        int_of_vertex[v] = n_vertices
        vertex_of_int[n_vertices] = v
        n_vertices += 1

# Build the initial graph.
edges = []
for i in range(n_vertices):
    for j in range(i+1, n_vertices):
        ri, mi = vertex_of_int[i]
        rj, mj = vertex_of_int[j]

        # Racers can't match with themselves.
        if ri == rj:
            continue

        assert ri in all_forbid
        assert rj in all_forbid

        # Don't rematch.
        if ri in forbid_map[rj]:
            assert rj in forbid_map[ri]
            continue
        assert rj not in forbid_map[ri]

        # The cost is the squared point difference.
        spread = abs(point_map[ri] - point_map[rj])
        cost = spread ** 2
        edges.append( (i, j, cost) )

print 'Found %d non-rematches' % len(edges)

# Return only those edges whose endpoints are unmatched by the edges in the collection 'chosen'.
def filter_edges(chosen):
    matched = set()
    for i, j, cost in chosen:
        assert i not in matched
        matched.add(i)
        assert j not in matched
        matched.add(j)

    chosen = set(chosen)

    elig = []
    for edge in edges:
        i, j, cost = edge
        if i in matched or j in matched:
            continue
        elig.append(edge)

    return elig

# Find the optimal cost given a collection of chosen edges.
def find_optimal_cost(chosen):
    subg = filter_edges(chosen)
    subg.extend(chosen)
    print '  Finding cost for %d chosen edges in subgraph with %d edges' % (len(chosen), len(subg))

    return backend.solve(n_vertices, subg)

# Find the cost before any edges have been chosen.
# The end solution will have the same cost.
ref_cost = find_optimal_cost([])
print 'Reference cost = %d' % ref_cost
print
assert ref_cost != None, 'No perfect matching in initial graph'

chosen = []
elig = None
while True:
    if not elig:
        elig = filter_edges(chosen)
        if not elig:
            # All vertices have been matched.
            break
        # This is the only randomization needed.
        random.shuffle(elig)

    e = elig.pop()
    print 'Trying edge %s' % (e,)

    candid = chosen + [e]
    e_cost = find_optimal_cost(candid)

    print '  Becomes cost %s (compare to %d)' % (e_cost, ref_cost)

    if e_cost == ref_cost:
        chosen = candid
        elig = None
print

def chosen_sort_key(edge):
    i, j, cost = edge
    ri, mi = vertex_of_int[i]
    rj, mj = vertex_of_int[j]

    return (-(point_map[ri] + point_map[rj]), ri, rj)
chosen.sort(key=chosen_sort_key)

print 'Final matching:'
for i, j, cost in chosen:
    ri, mi = vertex_of_int[i]
    rj, mj = vertex_of_int[j]

    pi = point_map[ri] / 2.0
    pj = point_map[rj] / 2.0

    spread = abs(pi - pj)

    ri = unlower_racer[ri]
    rj = unlower_racer[rj]

    print '%20s (%4.1f)   plays %20s (%4.1f)   --   spread = %4.1f' % (ri, pi, rj, pj, spread)
