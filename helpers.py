from pathlib import Path
import csv
import os
import subprocess
import time
from hashlib import blake2b
from datetime import datetime, timedelta
import yaml

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
            #e = ex
            import traceback
            e = traceback.format_exc()
            ret = 100
        assert isinstance(ret, int), "Error: func must return integer!"

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

    def join(self, other, both=False):
        # Left join.
        # if both == True, do an inner join (removing rows with no key in `other')
        # return a new table with information from both tables.
        # the keys must be the same.
        # columns from self are on the left
        # the first column from other is removed
        #
        s = Status()
        s.columns = self.columns + other.columns[1:]
        f = ['']*(len(other.columns)-1) # filler for empty rhs
        for k, v in self.items():
            if k not in other:
                if not both:
                    s[k] = v + f
            else:
                s[k] = v + other[k][1:]
        return s

    def show(self, cols=None):
        # print in markdown table format
        #
        if len(self) == 0:
            print("*empty*")
            return

        if cols is None:
            cols = list(range(len(self.columns)))
        else:
            cols = [self.columns.index(j) for j in cols]
        hdr = [self.columns[j] for j in cols]
        print( "| " + " | ".join(hdr) + " |" )
        print( "| --- "*len(hdr) + "|" )
        for k,row in self.items():
            print("| " + " | ".join([row[j] for j in cols]) + " |")

    def write(self, fname, mode='a'):
        with open(fname, mode, encoding='utf-8') as f:
            sz = f.tell()
            writer = csv.writer(f, dialect='excel')
            if sz == 0:
                writer.writerow(self.columns)
            for k,v in self.items():
                writer.writerow(v)

