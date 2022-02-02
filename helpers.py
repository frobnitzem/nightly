from typing import Callable
from functools import wraps
from pathlib import Path
import csv, sys, os, time
import subprocess
from hashlib import blake2b
from datetime import datetime, timedelta

import yaml

def span(text, style):
    return f'<span style="{style}">{text}</span>'

# does the return-code indicate fail?
def failed(b):
    return b[2] != "0"

def derive(tpl):
    h = blake2b(digest_size=10)
    for s in tpl:
        h.update( str(s).encode('utf-8') )
    return h.hexdigest()

def check_execute(log, *args, **kws):
    if log is None:
        ret = subprocess.call(args, **kws)
    else:
        log = open(log, "wb")
        ret = subprocess.call(args, stdout=log, stderr=log, **kws)
        log.close()
    return ret

#### jinja2 template rendering  cruft ####
class Render:
    def __init__(self):
        from jinja2 import Environment, FileSystemLoader, StrictUndefined

        self.cwd = Path().resolve()
        file_loader = FileSystemLoader(self.cwd / 'templates')
        self.env = Environment(loader=file_loader, undefined=StrictUndefined)

    def render_file(self, template, vals, out):
        # TODO: catch jinja2.exceptions.TemplateNotFound error?
        output = self.env \
                 . get_template(template) \
                 . render(vals)
        with open(out, 'w', encoding='utf-8') as f:
            f.write(output)
        os.chmod(out, 0o755)

R = Render()

def stamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def days_earlier(m):
    # Print the date n days earlier than today
    dt = timedelta(m)
    return (datetime.now() - dt).strftime("%Y-%m-%d %H:%M:%S")

def log_step(*args, **display_info):
    """
    display_info can contain info to give during the following events:

    name : str -- name of step/super-step being run
    """

    def mk_closure(func):
        # Run the function with a timer, and catch all errors.
        # Print what we're doing to the terminal.
        # Output the results to self.log.
        @wraps(func)
        def run_step(self, *args, **kws):
            name = display_info.get('name', func.__name__)
            print(f"{self.ID}: Starting {name}")
            t0 = time.time()
            e = None
            try:
                ret = func(self, *args, **kws)
            except Exception as ex:
                #e = ex
                import traceback
                e = traceback.format_exc()
                ret = 100
            assert isinstance(ret, int), "Error: func must return integer!"

            t1 = time.time()
            with open(self.log, 'a', encoding='utf-8') as f:
                if ret:
                    f.write(f"{stamp()}: {name} failed after {t1-t0} seconds.\n")
                    if e is not None:
                        f.write(f"    Internal Exception: {e}\n")
                else:
                    f.write(f"{stamp()}: {name} succeeded in {t1-t0} seconds.\n")
            return ret
        return run_step

    # invoked as @log_step
    if len(args) == 1 and isinstance(args[0], Callable):
        return mk_closure(args[0])
    return mk_closure

class Config:
    def __init__(self, fname):
        with open(fname, encoding='utf-8') as f:
            cfg = yaml.safe_load(f)

        self.work = Path(cfg['work']).resolve()
        self.buildvars = ["machine", "commit"] + cfg['buildvars']
        self.runvars = self.buildvars + cfg['runvars']
        self.resultvars = cfg['resultvars']
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

class Status(dict):
    # Encapsulates `{builds,runs,result}.csv` files
    #   dictionary of { ID : last entry }
    #
    # attr: columns = names of columns
    def __init__(self, fname=None):
        dict.__init__(self)

        if fname is None or not fname.exists():
            self.columns = []
            return

        with open(fname, 'r', encoding = 'utf-8', newline='') as csvfile:
            reader = csv.reader(csvfile, dialect='excel')
            hdr = next(reader)
            for row in reader:
                self[row[0]] = row

        self.columns = hdr

    def update(self, other):
        if len(self.columns) == 0:
            self.columns = other.columns
        N = len(self.columns)
        for k, v in other.items(): # justify to new #cols
            if len(v) < N:
                v = v + ['']*(N-len(v))
            self[k] = v

    def join(self, other, rhs_cols, both=False):
        # Left join.
        # if both == True, do an inner join (removing rows with no key in `other')
        # return a new table with information from both tables.
        # the keys must be the same.
        #
        # rhs_cols indicates the columns the right-side (other) must contain
        #
        # columns from self are on the left
        # the first column from other is removed (not present in right-side)
        #
        s = Status()
        if len(other.columns[1:]) > 0:
            assert tuple(rhs_cols) == tuple(other.columns[1:])
        s.columns = self.columns + rhs_cols
        f = ['']*len(rhs_cols) # filler for empty rhs
        for k, v in self.items():
            if k not in other:
                if not both:
                    s[k] = v + f
            else:
                s[k] = v + other[k][1:]
        return s

    def show(self, cols=None, file=sys.stdout, link=None):
        # print in markdown table format
        #
        if len(self) == 0:
            print("*empty*", file=file)
            return

        if cols is None:
            cols = list(range(len(self.columns)))
        else:
            cols = [self.columns.index(j) for j in cols]
        #print(cols)
        hdr = [self.columns[j] for j in cols]
        print( "| " + " | ".join(hdr) + " |", file=file)
        print( "| --- "*len(hdr) + "|", file=file)

        def get(row, j):
            try:
                return row[j]
            except IndexError:
                return ""
        for k,row in self.items():
            r = [get(row,j) for j in cols]
            if link is not None and len(r) > 0:
                color = "color:red" if failed(row) else "color:green"
                r[0] = span("[%s](%s)"%(r[0], Path(link)/r[0]), color)
            print("| " + " | ".join(r) + " |", file=file)

    def write(self, fname, mode='a'):
        with open(fname, mode, encoding='utf-8') as f:
            sz = f.tell()
            writer = csv.writer(f, dialect='excel')
            if sz == 0:
                writer.writerow(self.columns)
            for k,v in self.items():
                writer.writerow(v)

