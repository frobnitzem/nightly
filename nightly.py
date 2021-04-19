#!/usr/bin/env python

from helpers import *
from build import build
from run import run

# list of commits in the last 30 days
def last_30(repo):
    since = days_earlier( 30 )
    lines = subprocess.check_output(['git', 'log', f'--since={since}', '--pretty=format:%H'], cwd=repo)
    return lines.decode('utf-8').split('\n')

# latest commit only
def latest(repo):
    lines = subprocess.check_output(['git', 'log', '-n1', '--pretty=format:%H'], cwd=repo)
    return [ lines.decode('utf-8').strip() ]

def main(argv):
    rebuild = False
    rerun  = False
    commit = None
    while len(argv) > 3:
        if argv[1] == '--rebuild':
            rebuild = True
            del argv[1]
        if argv[1] == '--rerun':
            rerun = True
            del argv[1]
        elif argv[1] == '-c':
            commit = argv[2]
            del argv[1:3]
        else:
            break
    assert len(argv) == 3, f"Usage: {argv[0]} [--rebuild] [--rerun] [-c commit] <config.yaml> <machine>"

    cfg = Config(argv[1])
    machine = argv[2]

    info = cfg.machines[machine]
    repo = Path(info['repo']).resolve()
    assert (repo/'.git').is_dir(), f"{repo} is not a git repository."

    if subprocess.call(["git", "fetch"], cwd=repo):
        print(f"Error executing git fetch in {repo}")
        return 1

    if commit is None:
        commits = latest(repo)
    else:
        commits = [commit]

    s = Status(cfg.work/"builds.csv")
    
    for commit in commits:
        assert commit.strip() == commit and commit != ""
        for b in info['configs']:
            build_args = ['build', argv[1], machine, commit] + b['build']
            buildID = derive(build_args[2:])
            print(f"examining {buildID}")

            try:
                ret = int( s[buildID][2] )
                print(f"Previous build result: {ret}")
                if rebuild:
                    do_build = True
                elif rerun: # only if necessary
                    do_build = ret != 0
                else:
                    continue # stick with cached result
            except KeyError:
                do_build = True

            if do_build:
                ret = build( build_args )
            if ret != 0:
                continue

            rs = Status(cfg.work/buildID/"runs.csv")
            build_args[0] = 'run'
            for r in b['runs']:
                runID = derive(build_args[2:])
                if runID not in rs or rerun:
                    run( build_args + r )
    
    return 0

if __name__=="__main__":
    import sys
    exit( main(sys.argv) )
