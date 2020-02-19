# sshrun
A Python-based and jupyter notebook-friendly job manegement system for remote job management systems.

pyjobs allows to submit/list/detele/track jobs on Univa Grid Engine (UGE) or Sun Grid Engine (SGE).
It enables to remotely execute `qsub`, `qstat`, `qdel` (via `ssh`) and show the log/error files on local jupyter notebook (or jupyter lab).
It can also make it possible to execute jobs on other machines via `ssh` and `nohup` (under developments).

## Requirements
- `ssh` environment to remote machine. pyjobs is designed to be run on local machine. `ssh` connection to remote machines (such as ABCI) must be prerequired.

Sshrun provides easy and sophiscated ways to access your servers and HPC clusters via ssh and python including notebooks and jupyter-lab. Sshrun doesn't provide the ssh and job-running environments. They should be established before sshrun is introduced.

## Install
```bash
pip install sshrun
```

## Usage
pyjobs is designed to be run on local Jupyter notebook environment.

On jupyter notebooks, run
```python
from sshjob import *
jobs=pyjobs()
```
to initialize `jobs` instance of pyjobs.

`jobs` instance is used to manage your jobs on a specific remote (or local) machine.
`jobs.qsub()`
`jobs.show()`
`jobs.kill()`
`jobs.rm()`
`jobs.bye()`

- Run job

This is ax example to create a shellfile of `run.sh`, transfer the shellfile to `server1:~/s2s/run.sh` and execute it with `nohup`.
```python
from sshjob import *
jobs=pyjobs("server1:~/s2s::SHELL")
gpu=0
shell_file="""
cd $HOME/s2s
GPU=%d
CUDA_VISIBLE_DEVICES= $GPU python s2s.sh
"""%gpu
jobs.qsub(shell_file,"run.sh")
```

The create a new shell file of run.sh as
```bash
# (header)
cd $HOME/s2s
GPU=0
CUDA_VISIBLE_DEVICES= $GPU python s2s.sh
# (footer)
```
.

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

- Show job list

```python
jobs.show()
```

For details
```python
jobs.show(depth=1,no_update=False)
```
.

- Assign a job to the `jobs` instance later
```python
jobs[3059261]=pyjob(jobid="3059261",jobname="s2s.sh",jobfile=`cat s2s.sh`)
#jobs.dump()
```

-- Delete a latest job and its log

`jobs.kill()`+`jobs.rm()`

```python
jobs.bye(-1)
```

- shell support with ssh

```python
def shellrun(commandline,server,cd,ssh_bash_profile=True,nohup=False)
```

```python
def run_via_ssh(commandline,server,cd,ssh_bash_profile=True,nohup=False)
```
- when nohup=True, commandline shuould be a shell file.

