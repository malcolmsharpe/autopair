import csv
import random
import subprocess
import time

seed = time.time()
seed = 1440296616.851588 # tmp
print 'Seed = %r' % seed
print
random.seed(seed)

blossom = 'blossom5-v2.05.src/blossom5'
standings = 'data/CoNDOR Season 3 Matchup Chart - Standings.csv'

forbid_fix = {
    'imwaytoopunny': 'imwaytopunny',
}

omit = set( ['Xelnas', 'KageYuuki'] )

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

    all_vtx = set()
    for i, j, cost in subg:
        all_vtx.add(i)
        all_vtx.add(j)
    if len(all_vtx) != len(racers):
        # This check is necessary to avoid crashing the solver.
        print '    Skipping since %d vertices have zero degree' % (len(racers) - len(all_vtx))
        return None

    graph_path = 'tmp/graph.txt'
    sol_path = 'tmp/sol.txt'
    stdout_path = 'tmp/stdout.txt'
    #print 'Generating graph file %s' % graph_path

    graph_f = file(graph_path, 'w')
    print >>graph_f, len(racers), len(subg)
    for i, j, cost in subg:
        print >>graph_f, i, j, cost
    graph_f.close()

    #print 'Solving to file %s with output %s' % (sol_path, stdout_path)
    subprocess.check_call( [blossom, '-c', '-e', graph_path, '-w', sol_path],
        stdout=file(stdout_path, 'w') )
    output = list(file(stdout_path))
    cost_line = output[-1]
    cost_prefix = 'cost = '
    assert cost_line.startswith(cost_prefix)
    cost = int(float(cost_line[len(cost_prefix):]) + 0.5)

    return cost

def print_sol(sol_path):
    print 'Interpreting solution:'
    print
    for line in list(file(sol_path))[1:]:
        i, j = map(int, line.split())
        ri = racers[i]
        rj = racers[j]
        print '%20s (%d) plays %20s (%d)' % (ri, point_map[ri], rj, point_map[rj])

ref_cost = find_cost([])
print 'Reference cost = %d' % ref_cost
print

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

chosen.sort()
print 'Final matching:'
for i, j, cost in chosen:
    ri = racers[i]
    rj = racers[j]

    pi = point_map[ri]
    pj = point_map[rj]

    spread = abs(pi - pj)

    print '%20s (%d) plays %20s (%d) -- spread = %d' % (ri, pi, rj, pj, spread)
