#!/usr/bin/env python

from helpers import *

def get_result(rundir, ninfo):
    info = ['']*ninfo
    ret = check_execute(rundir / 'result.log',
                        rundir / 'result.sh',
                        cwd=rundir)
    if ret != 0:
        return ret, info

    z = rundir / 'result.txt'
    if not z.exists():
        return ret, info

    with open(z, 'r', encoding='utf-8') as f:
        info = []
        for line in f:
            info.append(line[:-1])
    if len(info) != ninfo:
        print(f"Invalid info present in {rundir/'result.txt'} -- expected {ninfo} elements.")
        info = ['']*ninfo

    return ret, info

def results(argv):
    redo = False
    while len(argv) > 2:
        if argv[1] == '--redo':
            redo = True
            del argv[1]
        else:
            break
    assert len(argv) == 1, f"Usage: {argv[0]} [--redo]"

    cfg = Config("config.yaml")

    s = Status(cfg.work/"builds.csv")
    
    for buildID, stat in s.items():
        out = Status(cfg.work/buildID/"results.csv")
        if len(out.columns) == 0:
            out.columns = ['runID','date','return value'] + cfg.resultvars

        rs = Status(cfg.work/buildID/"runs.csv")
        for runID, run in rs.items():
            if run[2] != '0': # run did not start
                continue

            if (not redo) and runID in out: # already checked this result?
                if out[runID][2] != '99':
                    continue
            ret, info = get_result(cfg.work/buildID/runID, len(cfg.resultvars))
            out[runID] = [runID, stamp(), ret] + info
    
        if len(out) > 0:
            out.write(cfg.work/buildID/"results.csv", 'w')

    return 0

if __name__=="__main__":
    import sys
    exit( results(sys.argv) )
