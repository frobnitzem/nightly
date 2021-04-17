#!/usr/bin/env python
# Summarize the results of all builds and runs
# by printing a neat markdown summary.

from helpers import *
import re

def show_csv(fname):
    # print the CSV information in a markdown table
    #
    #   returns: file read as a dictionary
    if not fname.exists():
        print("*empty*")
        return {}

    ans = {}
    with open(fname, 'r', encoding = 'utf-8', newline='') as csvfile:
        reader = csv.reader(csvfile, dialect='excel')
        hdr = next(reader)
        top = "| " + " | ".join(hdr) + " |"
        print(top)
        print( "| --- "*len(hdr) + "|" )
        for row in reader:
            print("| " + " | ".join(row) + " |")
            ans[row[0]] = row

    return ans

def show_file(fname):
    if not fname.exists():
        return 1
    print("```")
    with open(fname, 'r', encoding = 'utf-8') as f:
        print(f.read())
    print("```")
    return 0

def show_status(base, fname):
    fail = re.compile(r'(\w+) failed after')
    with open(base / fname, 'r', encoding = 'utf-8', newline='') as f:
        for line in f:
            print("    - " + line)
            m = fail.search(line)
            if m is not None:
                show_file(base / f"{m[1]}.log")

def filter_fails(tbl):
    # Turn the dictionary back into a list of "failing" instances
    # for futher examination.
    tbl = [b for k,b in tbl.items() if b[2] != "0"]
    return tbl

def main(argv):
    assert len(argv) == 2, f"Usage: {argv[0]} <config.yaml>"
    config = Config(argv[1])
    work = config.work

    print("# Builds\n")
    builds = filter_fails( show_csv(work / 'builds.csv') )

    print("\n# Runs\n")
    runs = filter_fails( show_csv(work / 'runs.csv') )

    if len(builds) > 0:
        print("\n# Failing Build Info\n")
        for b in builds:
            ID, date, ret = b[0], b[1], int(b[2])
            print(f"  * {date}: {work/ID} returned {ret}")
            show_status( work / ID , 'status.txt' )

    if len(runs) > 0:
        print("\n# Failing Run Info\n")
        for r in runs:
            ID, date, ret = r[0], r[1], int(r[2])
            print(f"  * {date}: {work/ID} returned {ret}")
            show_status( work / ID , 'status.txt' )

if __name__=="__main__":
    import sys
    exit( main(sys.argv) )

