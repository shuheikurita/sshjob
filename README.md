# Sshjob

## Free from shellscripts that generate other shellscripts on HPC

A Python-based and jupyter-friendly job management system for remote serevers and HPC job management systems.

Sshjob allows to submit/list/detele/track jobs on Univa Grid Engine (UGE) or Sun Grid Engine (SGE) from python program.
It enables to remotely execute `qsub`, `qstat`, `qdel` (via `ssh`) and show the log/error files on local jupyter notebook (or jupyter lab).
It can also make it possible to execute jobs on other machines via `ssh` and `nohup`.

## Requirements
- `ssh` environment to remote machines from the local machine where you run sshjob. You also need `ssh-agent` to auth without passwords.
- `bash` and `nohup` (for job execution on remote shells) on local and remote machine.

Sshjob provides easy and sophisticated way to access your servers, HPC clusters via ssh and python including notebooks and jupyter-lab. sshjob doesn't provide the ssh and job-running environment. They should be established before sshjob is introduced.

## Install
```bash
pip install sshjob
```

## Usage
Sshjob is designed to be run on local Jupyter notebook environment.
Jupyter is recommended but not mandatory.

On python, run
```python
from sshjob import *
jobs=pyjobs()
```
to initialize `pyjobs` instance of pyjobs. Here `jobs` is a sub-class of the ordered dictionary.

`pyjobs` instance is used to manage your jobs on a specific remote (or local) machine.
`jobs.qsub()`
`jobs.show()`
`jobs.kill()`
`jobs.rm()`
`jobs.bye()`

### Run jobs on remote shell

This is ax example to create a shellfile of `run.sh`, transfer the shellfile to `server1:~/s2s/run.sh` and execute it with `nohup`.
```python
from sshjob import *
jobs=pyjobs("server1:~/s2s::SHELL")
gpu=0
shell_file="""
cd $HOME/s2s
GPU=%d
CUDA_VISIBLE_DEVICES=$GPU python s2s.sh
"""%gpu
jobs.qsub(shell_file,"run.sh",jc="")
```

The new shell file of `run.sh` is
```bash
# (header)
cd $HOME/s2s
GPU=0
CUDA_VISIBLE_DEVICES=$GPU python s2s.sh
# (footer)
```
. The header is important for grid engines of HPC and specified in `jc=""` of qsub function.

You can specify the port number (ex. 12345) such as
```python
from sshjob import *
jobs=pyjobs("localhost:s2s:12345:SHELL")
gpu=0
shell_file="""
cd $HOME/s2s
GPU=%d
CUDA_VISIBLE_DEVICES= python s2s.sh
"""%gpu
jobs.qsub(shell_file,"run.sh",jc="+gpu,g1,72h")
```

### Run jobs on remote HPC

For HPC with a SGE job shceduler,
```python
from sshjob import *
jobs=pyjobs("localhost:s2s:12345:SHELL")
gpu=0
shell_file="""
cd $HOME/s2s
GPU=%d
CUDA_VISIBLE_DEVICES= python s2s.sh
"""%gpu
jobs.qsub(shell_file,"run.sh",jc="+gpu,g1,72h")
```
. Since job scheduler engines have many dialogs, you need to manually define an job_queues function for many cases.

```python

def sge_custom(short,jc=None,docker=""):
    result=[]
    if "gpu" in short:
        if "large" in short:
            result.append("#$ -l rt_G.large=1")
        elif "full" in short:
            result.append("#$ -l rt_F=1")
        elif "small" in short:
            result.append("#$ -l rt_G.small=1")
        else:
            raise NameError("Unknown job class",short)
    else:
        raise NameError("Unknown job class",short)
    if "24h" in short:
        result.append("#$ -l h_rt=24:00:00")
    elif "72h" in short or "3d" in short:
        result.append("#$ -l h_rt=72:00:00")
    elif "168h" in short or "7d" in short:
        result.append("#$ -l h_rt=168:00:00")

    if jc is not None:
        result.append("#$ -jc "+jc)

    result+=[
        "#$ -cwd",
    ]
    return result,docker

def shell(short,docker=""):
    return ["#localhost"],docker
    
JOB_ENVIRONMENTS = ["localhost:s2s::SHELL","server1:s2s::SHELL","hpc_server:s2s::SGE_CUSTOM",]
JOB_QUEUS        = {"SGE_CUSTOM":sge_custom}

jobs=pyjobs(
    environments = JOB_ENVIRONMENTS,
    job_queus = JOB_QUEUS,
    )
```

### Show job list

Show jobid, job states and git states if available.
```python
jobs.show()
```
For details
```python
jobs.show(depth=1,no_update=False)
```
.

### Track job log and error outputs
```
jobs.track(jobid=-1)
```
`jobid==0` is the initial job and `jobid==-1` is the last job on the `jobs` ordered dictionary. 

### Stop (kill) a job
```
jobs.kill(jobid)
```

### Delete a job log
```python
jobs.kill(jobid=-1)
```

### Stop and delete one latest job.
```python
jobs.bye(jobid=-1) # `jobs.kill(jobid=-1)`+`jobs.rm(jobid=-1)`
```

### Assign a job to the `jobs` instance later
```python
jobs[3059261]=pyjob(jobid="3059261",jobname="s2s.sh",jobfile=`cat s2s.sh`)
#jobs.dump()
```

### Remote shell support via ssh

```python
def shellrun(commandline,server,cd,ssh_bash_profile=True,nohup=False)
```

```python
def run_via_ssh(commandline,server,cd,ssh_bash_profile=True,nohup=False)
```
- when nohup=True, commandline shuould be a shell file.

