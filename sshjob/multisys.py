#!/usr/bin/env python
# -*- coding:utf-8 -*-

# Author: Shuhei Kurita
# Mailto: kurita@nlp.ist.i.kyoto-u.ac.jp
# Licence: GPL v2

from __future__ import absolute_import
from __future__ import unicode_literals

import datetime
#from datetime import datetime, timedelta, timezone
import re
import json
from time import sleep

from collections import OrderedDict

from sshjob.shell_runs import *
from sshjob.job_queues import *
from sshjob.sshjob import *

class sshjob(OrderedDict):
    def __init__(self,
                 envs={"local":":::SHELL"},
                 job_queues={"SHELL":shell},
                 file=None):
        super(sshjob, self).__init__()
        assert isinstance(envs,dict)
        assert isinstance(job_queues,dict)
        for label,env in envs.items():
            self[label]=sshjobsys(env,job_queues)
        self.job_queues = job_queues
        if file:
            self.load(file)
        elif file=="":
            if file:
                self.load(file)
                print("[SSHJOB] load from "+self.file)
            else:
                date=datetime.datetime.today().strftime("%Y%m%d")[2:]
                file = "pyjobs"+"."+date
                for i in range(100):
                    if not os.path.isfile(file+".%02d"%i):
                        self.file = file+".%02d"%i
                        print("[SSHJOB] Save to",self.file)
                        print("[SSHJOB] For loading, use:  jobs.load(\"%s\")"%self.file)
                        break
                else:
                    raise NameError("[SSHJOB] TOO MANY FILES")
        self.job_queues = DEFAULT_JOB_QUEUE
        self.add_job_queue(job_queues)

    @property
    def __dict__(self):
        expand={"file":self.file, "sshjob":{}}
        for label,jobsys in self.items():
            if isinstance(label,str):
                expand["sshjob"][label]=jobsys.__dict__
        return {"sshjob":expand}
    def show(self,**kwargs):
        for label,jobsys in self.items():
            if isinstance(label,str):
                print("# "+label)
                jobsys.show(**kwargs)
    def qsub(self,env,**kwargs):
        if env not in self:
            print("env="+env+" not found.")
        else:
            self[env].qsub(**kwargs)

    def dump(self,path):
        json.dump(self.__dict__,open(path,"w"))
    def loads(self,expand,merge=False):
        if "sshjob" in expand:
            if not merge:
                super(OrderedDict, self).clear()
            self.job_queues += expand["job_queues"]
            for label,env in expand["jobs"].items():
                self[label]=sshjobsys(env["environment"],self.job_queues)
                self[label].load_from_dict(expand)
            return True
        elif "jobs" in expand:
            print("[SSHJOB] Seems not a sshjobsys dump.")
            print("[SSHJOB] Use sshjobsys() instead.")
            return False
        else:
            print("[SSHJOB] Seems not a sshjob nor sshjobsys dump.")
            return False

    def load(self,path=None,merge=False):
        if path:
            expand = json.load(open(path,"r"))
        else:
            expand = json.load(open(self.file,"r"))
        if self.loads(expand, merge):
            if path:
                self.file=path
                print("[SSHJOB] Save to",self.file)
                print("[SSHJOB] For loading, use:  jobs.load(\"%s\")"%self.file)
            else:
                self.file=expand["file"]

    def add_job_queue(self,job_queues={}):
        self.job_queues.update(job_queues)
        self.show_job_queue()

    def show_job_queue(self):
        list_job_queues = [name for name,func in self.job_queues.items()]
        print("[SSHJOB] We recognize %d job queues of : %s"%(len(self.job_queues),", ".join(list_job_queues)))

    def multi_system(self,commandline,system=None,ssh_bash_profile=True):
        #system = system if system is not None else self.environments[0]
        #system = system.split(":")
        pass
