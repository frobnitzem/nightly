from pathlib import Path
import csv
import os
import subprocess
import time
from hashlib import blake2b
from datetime import datetime as dt
import yaml

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
        from jinja2 import Environment, FileSystemLoader, StrictUndefined

        self.cwd = Path(__file__).resolve().parent
        file_loader = FileSystemLoader(self.cwd / 'templates')
        self.env = Environment(loader=file_loader, undefined=StrictUndefined)

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
    # Run the function with a timer, and catch all errors.
    # Print what we're doing to the terminal.
    # Output the results to self.log.
    def run_step(self, *args, **kws):
        print(f"{self.ID}: Starting {func.__name__}")
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

class Config:
    def __init__(self, fname):
        with open(fname, encoding='utf-8') as f:
            cfg = yaml.safe_load(f)

        self.work = Path(cfg['work']).resolve()
        self.buildvars = ["machine", "commit"] + cfg['buildvars']
        self.runvars = self.buildvars + cfg['runvars']
        self.machines = cfg['machines']

    def validate_buildinfo(self, args):
        if len(args) != len(self.buildvars):
            print(f"Error: got {len(args)} buildvars, expected {len(self.buildvars)}")
            print("        expected buildinfo = " + ", ".join(self.buildvars))
            return True
        return False

    def validate_runinfo(self, args):
        if len(args) != len(self.runvars):
            print(f"Error: got {len(args)} runvars, expected {len(self.runvars)}")
            print("        expected runinfo = " + " ".join(self.runvars))
            return True
        return False

