#!/usr/bin/env python

from helpers import *
import shutil

def clean(argv):
    assert len(argv) >= 3, f"Usage: {argv[0]} <config.yaml> <ID> ..."

    cfg = Config(argv[1])

    err = 0
    for ID in argv[2:]:
        err += del_id(cfg, ID)

    return err

def del_id(cfg, ID):
    s = Status(cfg.work/"builds.csv")
    if ID in s: # delete the entire build
        print(f"Deleting build {ID}")
        del s[ID]
        s.write(cfg.work/"builds.csv", 'w')

        try:
            shutil.rmtree(cfg.work/ID)
        except FileNotFoundError:
            pass
        return 0

    # assume ID is a runID and check all builds for it
    for buildID, stat in s.items():
        rs = Status(cfg.work/buildID/"runs.csv")
        if ID not in rs:
            continue

        print(f"Deleting run {buildID}/{ID}")
        del rs[ID]
        rs.write(cfg.work/buildID/"runs.csv", 'w')

        # check if result was present
        out = Status(cfg.work/buildID/"results.csv")
        if ID in out:
            del out[ID]
            out.write(cfg.work/buildID/"results.csv", 'w')

        try:
            shutil.rmtree(cfg.work/buildID/ID)
        except FileNotFoundError:
            pass

        return 0

    print(f"ID {ID} not found.")
    return 1

if __name__=="__main__":
    import sys
    sys.exit( clean(sys.argv) )
