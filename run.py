#!/usr/bin/env python

from helpers import *
from steps import StepsEnv

class RunEnv(StepsEnv):
    step = 'run'
    process = [ 'mkenv', 'runjob' ]

    @log_step
    def mkenv(self):
        # Create env.sh and build.sh from templates
        R.render_file(f'{self.vals["machine"]}.run.sh.j2', self.vals, self.dir / 'run.sh')
        R.render_file('result.sh.j2', self.vals, self.dir / 'result.sh')
        return 0

    @log_step
    def runjob(self):
        return check_execute(
                      self.dir/'run.log',
                      self.dir/'run.sh',
                      cwd = str(self.dir))

# TODO: ensure run_dir is created inside build_dir
def run(argv):
    assert len(argv) >= 3, f"Usage: {argv[0]} <config.yaml> [run info]"

    cfg = Config(argv[1])
    info = argv[2:]
    if cfg.validate_runinfo(info):
        return 101

    buildID = derive( info[:len(cfg.buildvars)] )
    work = cfg.work / buildID
    assert work.is_dir(), f"Error: build directory {work} not found."

    R = RunEnv(work, cfg.runvars, info)
    ret = R.run()
    R.log_result(ret)
    if ret:
        print("Encountered error during run.")
    return ret

if __name__=="__main__":
    import sys
    exit( run(sys.argv) )
