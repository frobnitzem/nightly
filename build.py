#!/usr/bin/env python3

from helpers import *

class BuildEnv:
    def __init__(self, work_dir, repo_dir, names, tpl):
        assert len(tpl) == len(names), "Error: invalid number of build vars"
        self.repo = repo_dir
        self.names = names

        self.tpl = tpl
        self.vals = dict( (n, t) for n,t in zip(self.names, tpl) )

        self.ID = derive( tpl )
        self.vals['buildID'] = self.ID
        self.build_dir = work_dir / self.vals['buildID']
        self.log = self.build_dir / 'status.txt'

    @log_step
    def run(self):
        self.build_dir.mkdir(parents=True, exist_ok=True)
        if self.log.exists():
            self.log.unlink()

        if self.clone(): return 1
        if self.setup(): return 2
        if self.mkenv(): return 3
        if self.build(): return 4

        return 0

    @log_step
    def clone(self):
        check_execute(self.build_dir/'clone.log',
                      R.cwd / 'templates' / 'clone.sh', self.repo, self.vals['commit'],
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
    assert len(argv) >= 3, f"Usage: {argv[0]} <config.yaml> [build info]"

    cfg = Config(argv[1])
    build_info = argv[2:]
    if cfg.validate_buildinfo(build_info):
        return 101

    repo = Path( cfg.machines[ build_info[0] ]['repo'] ).resolve()
    assert (repo/'.git').is_dir(), f"{repo} is not a git repository"

    B = BuildEnv(cfg.work, repo, cfg.buildvars, build_info)
    ret = B.run()
    log_build_result(cfg.work, ret, B)
    if ret:
        print("Encountered error.")
    return ret

if __name__=="__main__":
    import sys
    exit( main(sys.argv) )
