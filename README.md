----------------------------------------------------------------
```

            d8,            d8b                d8b           
           `8P             ?88         d8P    88P           
                            88b     d888888P.d88            
  88bd88b   88b  d888b8b    888888b   ?88'   888   ?88   d8P 
  88P' ?8b  88P,d8P' ?88    88P `?8b  88P    ?88   d88   88  
 d88   88P d88  88b  ,88b  d88   88P.;88b     88b  ?8(  d88  
d88'   88b.88'  `?88P'`88.d88'   88b  `?8b     88b,`?88P'?8b 
                      )88                                )88
                     ,88P                               ,d8P
                 `?8888P                             `?888P'
```
----------------------------------------------------------------


# PIConGPU nightly build and performance tests

This repository contains scripts to build and run picongpu
on multiple systems in multiple test configurations.

Results are output in a custom work directory.

The top-level program for automated runs is `nightly.py`.
It checks recent code commits and only runs what is needed.

To adapt this to your own workflow, read this document,
run these scripts on a test repository to check
your understanding, then edit the scripts in `templates/` directory.


# Dependencies

* python packages:
    - pyyaml
    - jinja2

* shell utilities:
    - git


# Programs Included

  * `nightly.py <config.yaml> <machine name>`

        Change to the "repo" dir for the given machine and execute `git fetch`.        
        Then check for new commits and execute build and run steps as appropriate.

  * `build.py <config.yaml> <build info>` Carry out a build and log the results.

  * `run.py <config.yaml> <run info>` Carry out a run and log the results.

  * `results.py <config.yaml>` Gather all results from completed runs.

  * `sum.py <config.yaml>` Create a human-readable summary of the build and run results.


# Configuration

Configurations are a 2-level tree with buildID and runID parts.

The buildID is composed from all buildvars present in the `config.yaml`,
plus `machine` and `commit` as two mandatory fields.
In the example `config.yaml` shipping with this program,
the variables are as follows:

* buildID
  * machine = machine name
  * commit = picongpu commit hash
  * compiler = compiler module name
  * accel = accelerator module name (cuda or rocm)
  * mpi = mpi module name
  * problem = physics problem name
  * phash = physics problem commit hash (for FOM)

The runID is composed from all runvars present in the `config.yaml`,
plus the information from the buildID.  In the example `config.yaml`,
these include grid sizes for problems:

* runID
  * buildID tuple
  * nx, ny, nz = processor grid size (x, y, z)
  * grid = global grid size "x y z"
  * periodic = 0/1 flags indicating periodicity "x y z"

---
**NOTE**

Planned, future config. variables:
  * particle type
  * Maxwell solver type

---

The tuple of all information in a buildID is called the `buildID tuple`.
It is inlined into the first several elements of the runID.

When a string ID is needed, the "build ID" and "run ID"-s are hashed.
For details, see the `derive` function in `helpers.py`.

### So what?

These configuration options present in `config.yaml` are
are used to define file locations, and run information throughout
the build/run process.  In particular, they are present during
rendering of the jinja2 templates in `templates/*.j2`.
More details are provided below.


## Build Process

The build takes place in `build_dir` = `$WORK/buildID`.
All build scripts are launched from this directory.

Both `build_dir` and `buildID` are available to the templates
in case they need absolute paths.  No files should be changed
outside this directory, however.


The `build.py` script carries out these steps, aborting the process on error:

1. mkdir `build_dir` and run `templates/clone.sh <git repo dir> <commit>`
   - this script should clone picongpu at the specified commit into `picongpu`
   - its output is captured to `clone.log`
   - nonzero return aborts the build

2. create shell scripts in `build_dir`
   - `templates/<machine>.env.sh.j2 % buildID tuple` ~> `env.sh`
     * this is for you to re-use to setup the compile / run shell environment
   - `templates/setup.sh.j2 % buildID tuple` ~> `setup.sh`
   - `templates/build.sh.j2 % buildID tuple` ~> `build.sh`
   - This step has no separate logfile. Only `status.txt` records its completion.

3. execute `./setup.sh`
   - this script should copy-in the physics problem at the required commit hash
   - its output is captured to `setup.log`
   - nonzero return aborts the build

4. execute `./build.sh`
   - this script should do:
     * source env.sh
     * run pic-create
     * mkdir + cd to `build`
     * execute cmake
  - output is captured by `build.log`
  - nonzero return code indicates an error

5. report success / failure to `$WORK/builds.csv`


## Run Process

Runs take place in `run_dir` = `$WORK/buildID/runID`.
All run scripts are launched from this directory.

Both, `run_dir` and `runID` are available to the templates
in case they need absolute paths.
No files should be changed outside `run_dir`, however.


The `run.py` script carries out these steps, aborting the process on error:

1. mkdir `run_dir` and create its shell scripts
   - `templates/<machine>.run.sh.j2 % runID tuple` ~> `run.sh`
     * this script should create a batch script and submit it to the queue
   - `templates/result.sh.j2 % runID tuple` ~> `result.sh`
     * This script is run later to check run results.
     * This script may report extra information as a single-line, comma-delimited file, "result.txt".
     * It should be idempotent, returning 99 if the run has not completed yet.

2. execute `./run.sh`
   - its output is captured to `run.log`
   - nonzero return aborts the run

3. report success / failure to `$WORK/buildID/runs.csv` file


## Results Process

The `results.py` program simply works through all run directories
that are incomplete and executes their `result.sh` script
(from within the `run_dir`).  As usual, script
output is logged to `result.log`.

It reports success / failure to `$WORK/buildID/results.csv` file.
It also checks whether a `result.txt` file exists.
If so, it treats it as a whitespace-separated list.
It tokenizes the list, and appends it to the
entry in `results.csv`.

Note that this only scans runs in the `buildID/runs.csv` file
that are not already present (or are present, but
marked incomplete).
To mark a run incomplete, `result.sh` should return 99.


# List of Output Files

* `build.py` logs to `$WORK/builds.csv`
* `run.py` logs to `$WORK/buildID/runs.csv`
* `results.py` logs to `$WORK/buildID/results.csv`

## Output data

The outputs from each run are stored in several places:

1. build directory @ `$WORK/buildID`

   - contains a `status.txt` documenting the history
     of the compile state

2. run-directory @ `$WORK/runID`

   - contains a `status.txt` documenting the history
     of the run state

3. build information summary @ `$WORK/builds.csv`

   - Schema: buildID, date, compile return code (0 if OK), buildID tuple elements

4. run information summary @ `$WORK/buildID/runs.csv`

   - Schema: runID, date, run return code, runID tuple elements

5. completed job information summary @ `$WORK/results.csv`

   - Schema: runID, date, results return code, resultvars (gathered from results.txt)

