pyjobs
======

A Python-based and jupyter notebook-friendly job manegement system for
remote job management systems.

pyjobs allows to submit/list/detele/track jobs on Univa Grid Engine
(UGE) or Sun Grid Engine (SGE). It enables to remotely execute ``qsub``,
``qstat``, ``qdel`` (via ``ssh``) and show the log/error files on local
jupyter notebook (or jupyter lab). It can also make it possible to
execute jobs on other machines via ``ssh`` and ``nohup`` (under
developments).

Requirements
------------

-  ``ssh`` environment to remote machine. pyjobs is designed to be run
   on local machine. ``ssh`` connection to remote machines (such as
   ABCI) must be prerequired.

Usage
-----

pyjobs is designed to be run on local Jupyter notebook environment.

On jupyter notebooks, run

.. code:: python

    from pyjobs import *
    import subprocess,json
    jobs=pyjobs()
    jobs,type(jobs),json.dumps(jobs)

to initialize ``jobs`` instance of pyjobs.

``jobs`` instance is used to manage your jobs on a specific remote (or
local) machine. ``jobs.qsub()`` ``jobs.show()`` ``jobs.kill()``
``jobs.rm()`` ``jobs.bye()``

-  Run job

   .. code:: python

       jobs.qsub(s2o,"s2o.sh",jc="+gpu,g1,72h",n=0,docker="nvcr-pytorch-1903")

-  Show job list

   .. code:: python

       jobs.show(depth=1,no_update=False)

-  Assign a job to the ``jobs`` instance later

   .. code:: python

       jobs[3059261]=pyjob(jobid="3059261",jobname="s2o.sh",jobfile=`cat s2o.sh`)
       #jobs.dump()

-- Delete a latest job and its log

``jobs.kill()``\ +\ ``jobs.rm()``

.. code:: python

    jobs.bye(-1)

-  shell support with ssh

.. code:: python

    def shellrun(commandline,server,cd,ssh_bash_profile=True,nohup=False)

.. code:: python

    def run_via_ssh(commandline,server,cd,ssh_bash_profile=True,nohup=False)

-  when nohup=True, commandline shuould be a shell file.

