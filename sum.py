#!/usr/bin/env python
# Summarize the results of all builds and runs
# by printing a neat markdown summary.

from helpers import *
import shutil
import re, sys

def show_file(fname, file=sys.stdout):
    # print the file inside triple quotes
    if not fname.exists():
        return 1
    print("```", file=file)
    with open(fname, 'r', encoding = 'utf-8') as f:
        print(f.read(), file=file)
    print("```", file=file)
    return 0

def show_status(base, fname, file=sys.stdout):
    # print a status.txt file from base / fname
    # and show failing parts
    fail = re.compile(r'(\w+) failed after')
    with open(base / fname, 'r', encoding = 'utf-8') as f:
        for line in f:
            if line[0] == ' ': # abnormal format for the line
                print("       > " + line.strip(), file=file)
            else:
                print("    - " + line.strip(), file=file)
                m = fail.search(line)
                if m is not None:
                    show_file(base / f"{m[1]}.log", file=file)

def show_csv(fname, file=sys.stdout, link=None):
    s = Status(fname)
    s.show(file=file, link=None)
    return s

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

def main(argv):
    assert len(argv) == 1, f"Usage: {argv[0]}"
    config = Config("config.yaml")
    out = Path("results")
    out.mkdir(parents=True, exist_ok=True)
    work = config.work

    with open(out/"README.md", 'w', encoding='utf-8') as f:
        f.write("""# Build and Run Results
    * [List of Attempted Runs](runs.md)
    * [List of Builds](builds.md) [csv](builds.csv)
    * [Result Summary](results.md) [csv](results.csv)\n""")

    #builds = show_csv(work / 'builds.csv')
    builds = Status(work / 'builds.csv')
    shutil.copyfile(work / 'builds.csv', out / 'builds.csv')

    bld = open(out / "builds.md", 'w', encoding='utf-8')
    #bld.write("# [Builds](builds.csv)\n")
    #builds.show(file=bld, link="")
    bld.write("# [Builds](builds.csv)\n\n")
    for k,v in builds.items():
        err = ""
        if failed(v):
            ID, date, ret = v[0], v[1], int(v[2])
            (out/ID).mkdir(exist_ok=True)
            shutil.copyfile(work/ID/'build.log', out/ID/'build.log')
            #show_status( work / ID , 'status.txt' )
            err = " [[err = {ret}]]({ID}/build.log)"
        bld.write(f"  * {k}: {v}{err}\n")
    bld.close()

    run = open(out / "runs.md", 'w', encoding='utf-8')
    print("\n# Runs", file=run)
    all_results = None

    for buildID,v in builds.items():
        build_out = out / buildID
        build_out.mkdir(exist_ok=True)
        for fname in ['build.sh', 'build.log', 'env.sh',
                      'clone.log', 'setup.sh', 'setup.log',
                      'status.txt', 'runs.csv', 'results.csv']:
            if (work/buildID/fname).exists():
                shutil.copyfile(work/buildID/fname, build_out/fname)


        print(f"\n## Build [{buildID}]({buildID}/status.txt)\n", file=run)
        for name,val in zip(builds.columns, v):
            print(f"  * {name}: {val}", file=run)

        print(f"\n### [Script submissions]({buildID}/runs.csv)\n", file=run)
        runs = show_csv(work / buildID / 'runs.csv', file=run)
        fails = [v for k,v in runs.items() if failed(v)]

        print(f"\n### [Run results]({buildID}/results.csv)\n", file=run)
        results = Status(work / buildID / 'results.csv')
        r = runs.join(results, ['date', 'return value'] + config.resultvars)
        r.show(file=run, link=buildID)
        for runID, v in r.items():
            run_out = build_out / runID
            run_out.mkdir(exist_ok=True)
            for fname in ['run.sh', 'run.log', 'result.sh', 'result.log',
                          'result.txt', 'status.txt']:
                if (work/buildID/runID/fname).exists():
                    shutil.copyfile(work/buildID/runID/fname, run_out/fname)

        if all_results is None:
            all_results = r
        else:
            all_results.update(r)

        if len(fails) > 0:
            print("\n### Failing Run Info\n", file=run)
            for r in fails:
                ID, date, ret = r[0], r[1], int(r[2])
                print(f"  * {date}: {work/buildID/ID} returned {ret}", file=run)
                show_status( work / buildID / ID , 'status.txt', file=run )
    
    with open(out / "results.md", 'w', encoding='utf-8') as f:
        f.write("# [Results](results.csv)\n")
        if all_results is None or len(all_results.columns) == 0:
            f.write("\n*empty*\n")
        else:
            all_results.show(cols=['runID'] + config.runvars + config.resultvars, file=f)
        all_results.write(out / "results.csv", 'w')

if __name__=="__main__":
    import sys
    exit( main(sys.argv) )
