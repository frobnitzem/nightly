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
  * mesh = mesh grid size (x,y,z)
  * procs = processor grid size (x,y,z)

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


## Config description files

The configuration process for each build has 5 steps:

1. mkdir/cd to `$WORK/buildID` and run `templates/clone.sh <git repo dir> <commit>`
   - this script should clone picongpu at the specified commit into `picongpu`
   - its output is captured to clone.log
   - nonzero return aborts the build

2. cd to `$WORK/buildID` and run `templates/setup.sh <unpacked buildID tuple>`
   - this script should copy-in the physics problem at the required commit hash
   - its output is captured to setup.log
   - nonzero return aborts the build

3. create the `$WORK/buildID/env.sh` file to set compile / run shell environment
   and the `$WORK/buildID/build.sh` file that will run the build
   - the first is generated from `templates/<machine>.env.sh.j2 % buildID tuple`
   - the second is generated from `templates/build.sh.j2 % buildID tuple`
   - no separate logfile, only `status.txt` records completion

4. cd to `$WORK/buildID` and execute `./build.sh` (no args)
   - this script should do:
     * source env.sh
     * run pic-create
     * mkdir + cd to `build`
     * execute cmake
  - output is captured by build.log
  - nonzero return code indicates an error

5. report success / failure to `$WORK/builds.csv`


The run process after successful builds has the following steps:

1. manually create the working directory as `$WORK/buildID/runID/`

2. create the job submit script and submit to batch queue
   - `templates/submit.sh.j2 % runID tuple`
   - this script is copied into `$WORK/buildID/runID/submit.sh`

3. update the `status.txt` and `$WORK/runs.csv` file


# Output Documentation

Running the testing system will use config options
to generate input directories, runscripts, and jobs.
It will then add this info to `started.csv` and
launch those jobs.

The job itself updates `status.txt` in its own
directory.  At any time, the `summary.sh` script
can be run to update the final `completed.csv` file.

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

4. run information summary @ `$WORK/runs.csv`

   - Schema: runID, buildID, date, runID tuple elements

5. completed job information summary @ `$WORK/results.csv`

   - runID, startup time, #steps, core run-time

