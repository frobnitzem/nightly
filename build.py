#!/usr/bin/env python3

from helpers import *
from steps import StepsEnv

class BuildEnv(StepsEnv):
    step = 'build'
    process = [ 'clone', 'mkenv', 'setup', 'build' ]

    @log_step
    def clone(self):
        return check_execute(
                      self.dir/'clone.log',
                      R.cwd / 'templates' / 'clone.sh', self.repo, self.vals['commit'],
                      cwd = str(self.dir))

    @log_step
    def mkenv(self):
        # Create env.sh and build.sh from templates
        R.render_file(f'{self.vals["machine"]}.env.sh.j2', self.vals, self.dir / 'env.sh')
        R.render_file('setup.sh.j2', self.vals, self.dir / 'setup.sh')
        R.render_file('build.sh.j2', self.vals, self.dir / 'build.sh')
        return 0

    @log_step
    def setup(self):
        return check_execute(
                      self.dir/'setup.log',
                      self.dir/'setup.sh',
                      cwd = str(self.dir))

    @log_step
    def build(self):
        return check_execute(
                      self.dir/'build.log',
                      self.dir/'build.sh',
                      cwd = str(self.dir))

def build(argv):
    assert len(argv) >= 2, f"Usage: {argv[0]} [build info]"

    cfg = Config("config.yaml")
    info = argv[1:]
    if cfg.validate_buildinfo(info):
        return 101

    repo = Path( cfg.machines[ info[0] ]['repo'] ).resolve()
    assert (repo/'.git').is_dir(), f"{repo} is not a git repository"

    B = BuildEnv(cfg.work, cfg.buildvars, info, repo=repo)
    ret = B.run()
    B.log_result( ret )

    if ret:
        print("Encountered error during build.")
    return ret

if __name__=="__main__":
    import sys
    exit( build(sys.argv) )
