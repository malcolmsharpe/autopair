import csv
import random
import time

import backend

seed = int(time.time())
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

# Build the initial graph.
n_vertices = len(racers)
b = []
for i, r in enumerate(racers):
    r = r.lower()
    b.append(exceptions.get(r, weekly_matches))

edges = []
for i in range(n_vertices):
    for j in range(i+1, n_vertices):
        ri = racers[i].lower()
        rj = racers[j].lower()

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

# Find the optimal cost given fixed edges.
def find_optimal_cost(zeros, ones):
    print '  Finding cost for %d zero edges and %d one edges' % (len(zeros), len(ones))

    return backend.solve_b(b, edges, zeros, ones)

# Find the cost before any edges have been tried.
# The end solution will have the same cost.
ref_cost = find_optimal_cost([], [])
print 'Reference cost = %d' % ref_cost
print
assert ref_cost != None, 'No perfect b-matching in initial graph'

zeros = []
ones = []
elig = list(edges)
random.shuffle(elig)
for i, e in enumerate(elig):
    print 'Trying edge %s -- %d/%d' % (e, i+1, len(edges))

    candid = ones + [e]
    e_cost = find_optimal_cost(zeros, candid)

    print '  Becomes cost %s (compare to %d)' % (e_cost, ref_cost)

    if e_cost == ref_cost:
        ones = candid
    else:
        zeros.append(e)
print

def ones_sort_key(edge):
    i, j, cost = edge
    ri = racers[i].lower()
    rj = racers[j].lower()

    return (-(point_map[ri] + point_map[rj]), ri, rj)
ones.sort(key=ones_sort_key)

print 'Final matching with cost*4 = %d (seed = %r):' % (ref_cost, seed)
print
for i, j, cost in ones:
    ri = racers[i].lower()
    rj = racers[j].lower()

    pi = point_map[ri] / 2.0
    pj = point_map[rj] / 2.0

    spread = abs(pi - pj)

    ri = unlower_racer[ri]
    rj = unlower_racer[rj]

    cost_pretty = '%3d' % cost
    if cost == 0:
        cost_pretty = '   '

    print '%20s (%4.1f)   plays %20s (%4.1f)   --   spread = %4.1f;  cost*4 = %s' % (
        ri, pi, rj, pj, spread, cost_pretty)
