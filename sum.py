#!/usr/bin/env python
# Summarize the results of all builds and runs
# by printing a neat markdown summary.

from helpers import *
import shutil
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

#def show_csv(fname):
#    s = Status(fname)
#    s.show()
#    return s

def sortby(data, col):
    v = [(row[col], row) for row in data]
    v.sort()
    return [x[1] for x in v]

sorts = ['date', 'return value', 'machine', 
         'compiler', 'accel', 'mpi', 'problem', 'phash']
order = ['return value', 'problem', 'phash', 'machine', 'accel', 'compiler', 'mpi', 'date']

def output_dir(self, out, name):
    # output
    #

    if len(self) == 0:
        print("*empty*")
        return

    hdr = [f"[{c}]({name}_{c})" for c in self.columns]
    hdr = "| " + " | ".join(hdr) + " |"
    print( "| --- "*len(self.columns) + "|" )

    items = []
    for k,row in self.items():
        color = "color:red" if failed(row) else "color:green"
        r = [span(row[0], color)]
        r.extend(row[1:])
        items.append(r)

    for i, c in enumerate(self.columns):
        if i == 0:
            continue
        with open(out / f"{name}_{c}.md", 'w') as f:
            
            for r in sortby(items, i):
                print("| " + " | ".join(r) + " |", file=f)

def span(text, style):
    return f'<span style="{style}">{text}</span>'

# does the return-code indicate fail?
def failed(b):
    return b[2] != "0"


def main(argv):
    assert len(argv) == 1, f"Usage: {argv[0]}"
    config = Config("config.yaml")
    out = Path("results")
    out.mkdir(parents=True, exist_ok=True)
    work = config.work

    #builds = show_csv(work / 'builds.csv')
    builds = Status(work / 'builds.csv')
    shutil.copyfile(work / 'builds.csv', out / 'builds.csv')

    bld = open(out / "builds.md")
    bld.write("# [Builds](builds.csv)\n")
    for k,v in builds.items():
        bld.write()

    #fails = open(out / "fails.md")
    #fails = [v for k,v in builds.items() if failed(v)]

    #if len(fails) > 0:
    #    print("\n# Failing Build Info\n")
    #    for b in fails:
    #        ID, date, ret = b[0], b[1], int(b[2])
    #        print(f"  * {date}: {work/ID} returned {ret}")
    #        show_status( work / ID , 'status.txt' )

    print("\n# Runs")
    all_results = None

    for buildID,v in builds.items():
        print(f"\n## Build {buildID} {v}\n")

        print(f"\n### Script submissions\n")
        runs = show_csv(work / buildID / 'runs.csv')
        fails = [v for k,v in runs.items() if failed(v)]

        print(f"\n### Run results\n")
        results = Status(work / buildID / 'results.csv')
        r = runs.join(results)
        if all_results is None:
            all_results = r
        else:
            all_results.update(r)

        if len(fails) > 0:
            print("\n## Failing Run Info\n")
            for r in fails:
                ID, date, ret = r[0], r[1], int(r[2])
                print(f"  * {date}: {work/buildID/ID} returned {ret}")
                show_status( work / buildID / ID , 'status.txt' )

    if all_results is not None:
        print("\n# Result Summary\n")
        all_results.show(cols=config.runvars + config.resultvars)
    all_results.write("all_results.csv")

if __name__=="__main__":
    import sys
    exit( main(sys.argv) )
