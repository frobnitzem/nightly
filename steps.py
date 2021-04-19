import csv
from helpers import derive, log_step, stamp

class StepsEnv:
    def __init__(self, work_dir, names, tpl, **kws):
        assert len(tpl) == len(names), f"Error: invalid number of {self.step} vars"
        for k, v in kws.items(): # e.g. self.repo = repo
            setattr(self, k, v)

        self.names = names

        self.tpl = tpl
        self.ID = derive( tpl )

        self.work_dir = work_dir
        self.dir = work_dir / self.ID
        self.log = self.dir / 'status.txt'

        # values available for substitution in jinja2 templates
        self.vals = dict( (n, t) for n,t in zip(self.names, tpl) )
        self.vals[f'{self.step}ID']   = self.ID
        self.vals[f'{self.step}_dir'] = self.dir

    @log_step
    def run(self):
        self.dir.mkdir(parents=True, exist_ok=True)
        if self.log.exists():
            self.log.unlink()

        for i, step_name in enumerate(self.process):
            fn = getattr( self, step_name )
            if fn() != 0:
                return (i+1)

        return 0

    def log_result(self, ret):
        work = self.work_dir
        logname = f"{self.step}s.csv"
        with open(work / logname, 'a', encoding='utf-8') as f:
            sz = f.tell()
            writer = csv.writer(f, dialect='excel')
            if sz == 0:
                writer.writerow([f'{self.step}ID','date','return value'] + list(self.names))
            writer.writerow([self.ID,stamp(),ret] + list(self.tpl))

