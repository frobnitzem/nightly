#!/usr/bin/env python3

from pathlib import Path
from hashlib import blake2b
from datetime import datetime as dt
import csv
import os
import subprocess
import time

def derive(tpl):
    h = blake2b(digest_size=10)
    for s in tpl:
        h.update( s.encode('utf-8') )
    return h.hexdigest()

def check_execute(log, *args, **kws):
    if log is not None:
        log = open(log, "wb")
    ret = bool(subprocess.call(args, stdout=log, stderr=log, **kws))
    if log is not None:
        log.close()
    return ret

#### jinja2 template rendering  cruft ####
class Render:
    def __init__(self):
        from jinja2 import Environment, FileSystemLoader

        self.cwd = Path(__file__).resolve().parent
        file_loader = FileSystemLoader(self.cwd / 'templates')
        self.env = Environment(loader=file_loader)

    def render_file(self, template, vals, out):
        output = self.env \
                 . get_template(template) \
                 . render(vals)
        with open(out, 'w', encoding='utf-8') as f:
            f.write(output)
        os.chmod(out, 0o755)

R = Render()

def stamp():
    return dt.now().strftime("%Y-%m-%d %H:%M:%S")

def log_step(func):
    def run_step(self, *args, **kws):
        print(f"{self.vals['buildID']}: Starting {func.__name__}")
        t0 = time.time()
        e = None
        try:
            ret = func(self, *args, **kws)
        except Exception as ex:
            e = ex
            ret = 100
        t1 = time.time()
        with open(self.log, 'a', encoding='utf-8') as f:
            if ret:
                f.write(f"{stamp()}: {func.__name__} failed after {t1-t0} seconds.\n")
                if e is not None:
                    f.write(f"    Internal Exception: {e}\n")
            else:
                f.write(f"{stamp()}: {func.__name__} succeeded in {t1-t0} seconds.\n")
        return ret
    return run_step

class BuildEnv:
    def __init__(self, work_dir, tpl):
        self.names = ['machine', 'compiler', 'rocm', 'mpi', 'commit', 'problem', 'phash']
        assert len(tpl) == len(self.names)
        self.tpl = tpl
        self.vals = dict( (n, t) for n,t in zip(self.names, tpl) )

        self.vals['buildID'] = derive( tpl )
        self.build_dir = work_dir / self.vals['buildID']
        self.log = self.build_dir / 'status.txt'

    @log_step
    def run(self):
        self.build_dir.mkdir(parents=True, exist_ok=True)

        if self.clone(): return 1
        if self.setup(): return 2
        if self.mkenv(): return 3
        if self.build(): return 4

        return 0

    @log_step
    def clone(self):
        check_execute(self.build_dir/'clone.log',
                      R.cwd / 'templates' / 'clone.sh', self.vals['commit'], self.vals['buildID'],
                      cwd = str(self.build_dir))

    @log_step
    def setup(self):
        check_execute(self.build_dir/'setup.log',
                      R.cwd / 'templates' / 'setup.sh', *self.tpl,
                      cwd = str(self.build_dir))

    @log_step
    def mkenv(self):
        # Create env.sh and build.sh from templates
        R.render_file(f'{self.vals["machine"]}.env.sh.j2', self.vals, self.build_dir / 'env.sh')
        R.render_file('build.sh.j2', self.vals, self.build_dir / 'build.sh')

    @log_step
    def build(self):
        check_execute(self.build_dir/'build.log',
                      self.build_dir/'build.sh',
                      cwd = str(self.build_dir))

def log_build_result(work, ret, B):
    with open(work / 'builds.csv', 'a', encoding='utf-8') as f:
        sz = f.tell()
        writer = csv.writer(f, dialect='excel')
        if sz == 0:
            writer.writerow(['buildID','date','return value'] + list(B.names))
        writer.writerow([B.vals["buildID"],stamp(),ret] + list(B.tpl))

def main(argv):
    assert len(argv) == 2, f"Usage: {argv[0]} <work dir>"
    work = Path(argv[1]).resolve()

    # ['machine', 'compiler', 'rocm', 'mpi', 'commit', 'problem', 'phash']
    build_cfgs = [
            ('poplar', 'gcc/8.1.0', 'rocm/4.1.1', 'ompi/4.1.0/llvm/rocm/4.1.1', 'abcd', 'LaserWakeField', '')
        ]
    B = BuildEnv(work, build_cfgs[0])
    ret = B.run()
    log_build_result(work, ret, B)
    if ret:
        print("Encountered error.")
    return ret

if __name__=="__main__":
    import sys
    exit( main(sys.argv) )
