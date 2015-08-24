import os
import os.path
import subprocess
import sys

blossom = 'blossom5-v2.05.src/blossom5'

if not os.path.exists(blossom):
    print 'Did not find BLOSSOM V executable at expected path %s' % blossom
    print 'See README for installation instructions'
    sys.exit(1)

# Find cost assuming a perfect matching exists.
def solve_pm(n, edges):
    try:
        os.mkdir('tmp')
    except OSError:
        assert os.path.exists('tmp')
    graph_path = 'tmp/graph.txt'
    sol_path = 'tmp/sol.txt'
    stdout_path = 'tmp/stdout.txt'
    stderr_path = 'tmp/stderr.txt'

    graph_f = file(graph_path, 'w')
    print >>graph_f, n, len(edges)
    for i, j, cost in edges:
        print >>graph_f, i, j, cost
    graph_f.close()

    subprocess.check_call( [blossom, '-c', '-e', graph_path, '-w', sol_path],
        stdout=file(stdout_path, 'w'), stderr=file(stderr_path, 'w') )

    output = list(file(stdout_path))
    cost_line = output[-1]

    cost_prefix = 'cost = '
    assert cost_line.startswith(cost_prefix)
    cost = int(float(cost_line[len(cost_prefix):]) + 0.5)

    return cost

# Find cost without assuming a perfect matching exists.
def solve(n, edges):
    edge_set = set()
    for i, j, cost in edges:
        assert i < j
        edge_set.add( (i, j) )

    pm_edges = []
    for i in range(n):
        for j in range(i+1, n):
            cost = int( (i,j) not in edge_set )
            pm_edges.append( (i, j, cost) )

    pm_cost = solve_pm(n, pm_edges)
    assert pm_cost >= 0

    if pm_cost != 0:
        print '    No perfect matching exists'
        return None

    return solve_pm(n, edges)
