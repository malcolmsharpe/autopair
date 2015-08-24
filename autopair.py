import csv
import random
import time

import backend

seed = time.time()
print 'Seed = %r' % seed
print
random.seed(seed)

standings = 'data/CoNDOR Season 3 Matchup Chart - Standings.csv'

forbid_fix = {
    'imwaytoopunny': 'imwaytopunny',
}

omit = set( ['Xelnas', 'KageYuuki', 'Zeldaethan9'] ) # dropped/withdrawn/removed
omit.add('CanadianBac0nz') # away week 4
omit.add('RobSnowlock') # away week 4
omit.add('aiLoodee') # bye week 4

rdr = csv.reader(file(standings))
rows = list(rdr)
point_map = {}
forbid_map = {}
all_forbid = set()
racers = []
for row in rows[4:]:
    racer = row[1]
    if racer in omit:
        print 'Skipping %s' % racer
        continue
    if racer == '':
        print 'Skipping blank row'
        continue

    points = int(row[2])
    point_map[racer] = points
    racers.append(racer)

    prev = row[11:]
    forbid = []
    for name in prev:
        name = name.strip()
        if name in forbid_fix:
            name = forbid_fix[name]
        if name not in ['', '--']:
            forbid.append(name)
    forbid = set(forbid)
    forbid_map[racer] = forbid
    all_forbid |= forbid

    print '%s has %d points and previously played %s' % (racer, points, prev)
print

print 'Read %d eligible racers' % len(racers)
print

edges = []
for i in range(len(racers)):
    for j in range(i+1, len(racers)):
        ri = racers[i]
        rj = racers[j]

        rfi = ri.lower()
        rfj = rj.lower()

        assert rfi in all_forbid, '%s not found in previous matches' % rfi
        assert rfj in all_forbid, '%s not found in previous matches' % rfj

        if rfi in forbid_map[rj] or rfj in forbid_map[ri]:
            continue

        spread = abs(point_map[ri] - point_map[rj])
        cost = spread ** 2
        edges.append( (i, j, cost) )
print 'Found %d non-rematches' % len(edges)

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

def find_cost(chosen):
    subg = filter_edges(chosen)
    subg.extend(chosen)
    print '  Finding cost for %d chosen edges in subgraph with %d edges' % (len(chosen), len(subg))

    return backend.solve(len(racers), subg)

ref_cost = find_cost([])
print 'Reference cost = %d' % ref_cost
print
assert ref_cost != None, 'No perfect matching in initial graph'

chosen = []
elig = None
while True:
    if not elig:
        elig = filter_edges(chosen)
        if not elig:
            break
        random.shuffle(elig)

    e = elig.pop()
    print 'Trying edge %s' % (e,)

    candid = chosen + [e]
    e_cost = find_cost(candid)

    print '  Becomes cost %s (compare to %d)' % (e_cost, ref_cost)

    if e_cost == ref_cost:
        chosen = candid
        elig = None
print

chosen.sort(key=lambda (i,j,cost): (-point_map[racers[i]] - point_map[racers[j]], racers[i]))
print 'Final matching:'
for i, j, cost in chosen:
    ri = racers[i]
    rj = racers[j]

    pi = point_map[ri]
    pj = point_map[rj]

    spread = abs(pi - pj)

    print '%20s (%d)   plays %20s (%d)   --   spread = %d' % (ri, pi, rj, pj, spread)
