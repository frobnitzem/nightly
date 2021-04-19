#!/usr/bin/env python
# Summarize the results of all builds and runs
# by printing a neat markdown summary.

from helpers import *
import re

def show_file(fname):
    # print the file inside triple quotes
    if not fname.exists():
        return 1
    print("```")
    with open(fname, 'r', encoding = 'utf-8') as f:
        print(f.read())
    print("```")
    return 0

def show_status(base, fname):
    # print a status.txt file from base / fname
    # and show failing parts
    fail = re.compile(r'(\w+) failed after')
    with open(base / fname, 'r', encoding = 'utf-8') as f:
        for line in f:
            if line[0] == ' ': # abnormal format for the line
                print("       > " + line.strip())
            else:
                print("    - " + line.strip())
                m = fail.search(line)
                if m is not None:
                    show_file(base / f"{m[1]}.log")

# does the return-code indicate fail?
def failed(b):
    return b[2] != "0"

def show_csv(fname):
    s = Status(fname)
    s.show()
    return s

def main(argv):
    assert len(argv) == 2, f"Usage: {argv[0]} <config.yaml>"
    config = Config(argv[1])
    work = config.work

    print("# Builds\n")
    builds = show_csv(work / 'builds.csv')

    fails = [v for k,v in builds.items() if failed(v)]

    if len(fails) > 0:
        print("\n# Failing Build Info\n")
        for b in fails:
            ID, date, ret = b[0], b[1], int(b[2])
            print(f"  * {date}: {work/ID} returned {ret}")
            show_status( work / ID , 'status.txt' )

    print("\n# Runs")

    for buildID,v in builds.items():
        print(f"\n## Build {buildID} {v}\n")

        print(f"\n### Script submissions\n")
        runs = show_csv(work / buildID / 'runs.csv')
        fails = [v for k,v in runs.items() if failed(v)]
        
        print(f"\n### Run results\n")
        Status(work / buildID / 'results.csv').show()

        if len(fails) > 0:
            print("\n## Failing Run Info\n")
            for r in fails:
                ID, date, ret = r[0], r[1], int(r[2])
                print(f"  * {date}: {work/buildID/ID} returned {ret}")
                show_status( work / buildID / ID , 'status.txt' )

if __name__=="__main__":
    import sys
    exit( main(sys.argv) )

