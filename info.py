#!/usr/bin/env python

from helpers import *

import shutil

def print_file(dirname, name):
    fname = dirname/name
    if not fname.exists():
        print(f"No {name}")
        return

    print(f"{name}:")
    with open(fname, 'r', encoding = 'utf-8') as f:
        print(f.read())

def info(argv):
    assert len(argv) >= 2, f"Usage: {argv[0]} <ID> ..."

    cfg = Config("config.yaml")

    err = 0
    for ID in argv[1:]:
        err += info_id(cfg, ID)

    return err

def info_id(cfg, ID):
    s = Status(cfg.work/"builds.csv")
    if ID in s:
        print(f"Build {ID}")
        print(f"  status: {s[ID]}")

        # cfg.work/buildID
        print("  runs:")
        rs = Status(cfg.work/ID/"runs.csv")
        rs.show()

        print("  logs:")
        for log in ["clone", "setup", "build"]:
            print_file(cfg.work/ID, f"{log}.log")
        return 0

    # assume ID is a runID and check all builds for it
    for buildID, stat in s.items():
        rs = Status(cfg.work/buildID/"runs.csv")
        if ID not in rs:
            continue

        print(f"Run {buildID}/{ID}")
        print(f"  status: {rs[ID]}")

        # check if result was present
        out = Status(cfg.work/buildID/"results.csv")
        if ID in out:
            print(f"  result: {out[ID]}")

        print("  logs:")
        for log in ["run", "result"]:
            print_file(cfg.work/buildID/ID, f"{log}.log")

        return 0

    print(f"ID {ID} not found.")
    return 1

if __name__=="__main__":
    import sys
    sys.exit( info(sys.argv) )
