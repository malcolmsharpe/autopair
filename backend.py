from collections import defaultdict
import os
import os.path
import subprocess
import sys

def ensure_tmp_dir():
    try:
        os.mkdir('tmp')
    except OSError:
        assert os.path.exists('tmp')

blossom = 'blossom5-v2.05.src/blossom5'

if not os.path.exists(blossom):
    print 'Did not find BLOSSOM V executable at expected path %s' % blossom
    print 'See README for installation instructions'
    sys.exit(1)

# Find cost assuming a perfect matching exists.
def solve_pm(n, edges):
    ensure_tmp_dir()

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

scip = './scip'

if not os.path.exists(scip):
    print 'Did not find (link to) SCIP executable at expected path %s' % scip
    sys.exit(1)

def var_name(i, j):
    if j < i:
        return var_name(j, i)
    assert i != j
    return 'x_{%d,%d}' % (i, j)

# Solve the problem where vertices need a general number of adjacent edges.
# The edges in 'chosen' are forced to be taken.
def solve_b(b, edges, zeros, ones):
    ensure_tmp_dir()

    ip_path = 'tmp/bmatch.lp'
    sol_path = 'tmp/bmatch_sol.log'
    stdout_path = 'tmp/stdout.txt'
    stderr_path = 'tmp/stderr.txt'

    # Clear the old solution (if any).
    file(sol_path, 'w')

    ip_f = file(ip_path, 'w')

    adj = defaultdict(lambda: [])

    print >>ip_f, 'min'
    for i, j, cost in edges:
        print >>ip_f, '  +%d %s' % (cost, var_name(i,j))
        adj[i].append(j)
        adj[j].append(i)

    print >>ip_f, 'st'
    for i, bi in enumerate(b):
        line = [' ']
        for j in adj[i]:
            line.append('+ %s' % var_name(i,j))
        line.append('= %d' % bi)
        print >>ip_f, ' '.join(line)

    zeros = set(zeros)
    ones = set(ones)
    print >>ip_f, 'bounds'
    for e in edges:
        i, j, cost = e
        if e in ones:
            print >>ip_f, '  %s = 1' % var_name(i,j)
        elif e in zeros:
            print >>ip_f, '  %s = 0' % var_name(i,j)
        else:
            print >>ip_f, '  0 <= %s <= 1' % var_name(i,j)
    print >>ip_f, 'end'
    
    ip_f.close()

    subprocess.check_call( [scip, '-f', ip_path, '-l', sol_path],
        stdout=file(stdout_path, 'w'), stderr=file(stderr_path, 'w') )

    output = list(file(sol_path))
    success = False
    opt = 0
    for line in output:
        if 'SCIP Status' in line:
            if 'infeasible' in line:
                return None
            if 'optimal solution found' in line:
                success = True

        if 'objective value:' in line:
            opt = int(line.split()[-1])

    assert success
    return opt
