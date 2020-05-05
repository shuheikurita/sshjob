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

from os.path import expanduser
path_base=""

require_files=["header_basic.sh","header_cpu.sh", "header_gpu.sh","footer.sh"]

DEFAULT_JOB_QUEUE={"SGE_DEFAULT":sge_default, "SHELL":shell}


class sshjobsys(OrderedDict):
    @staticmethod
    def version():
        return "0.0.dev48"
    def __init__(self,
                 environment=":::SHELL",
                 job_queues={"SHELL":shell},
                 file=""):
        #self.basedir=basedir
        super(sshjobsys, self).__init__()
        assert isinstance(environment,str)
        assert isinstance(job_queues,dict)
        for req in require_files:
            if not os.path.isfile(req):
                open(req,"w").write("")
        if file:
            self.load(file)
        elif file=="":
            if file:
                self.load(file)
                print("[SSHJOB] Load from "+self.file)
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
        self.environment = environment
        self.job_queues = DEFAULT_JOB_QUEUE
        self.add_job_queue(job_queues)
        self.res = None

    @property
    def __dict__(self):
        return self.dumps(to_str=False)

    def dumps(self,to_str=True):
        expand={"environment":self.environment, "file":self.file, "jobs":self}
        if to_str:
            return json.dumps(expand)
        else:
            return expand
    def dump(self,path=None):
        expand=self.dumps(to_str=False)
        if path:
            json.dump(expand,open(path,"w"))
        else:
            json.dump(expand,open(self.file,"w"))
    def load_from_dict(self,expand,merge=False):
        if "jobs" not in expand:
            print("[SSHJOB] Seems not a sshjobsys dump.")
            return False
        if not merge:
            super(sshjobsys, self).clear()
        for jobid,jobname in expand["jobs"].items():
            self[jobid]=pyjob(**jobname)
        # "environments" for compatibility
        self.environment = expand["environment"] if "environment" in expand else \
            expand["environments"][0] if "environments" in expand else \
                [":::SHELL"]
        return True
    def load(self,path=None,merge=False):
        if path:
            expand = json.load(open(path,"r"))
        else:
            expand = json.load(open(self.file,"r"))
        if self.load_from_dict(expand, merge):
            if path:
                self.file=path
                print("[SSHJOB] Save to",self.file)
                print("[SSHJOB] For loading, use:  jobs.load(\"%s\")"%self.file)
            else:
                self.file=expand["file"]

    def show(self,depth=0,no_update=False,search=[]):
        system = self.environment.split(":")
        searches = [search] if isinstance(search,str) else search
        if not no_update:
            try:
                if "SHELL" in system[-1]:
                    self.updating(shellsystem=True,depth=depth-1)
                else:
                    self.updating(depth=depth-1)
            except Exception as e:
                print("Update failed. Use no_update=True")
                if depth>3:
                    print(e)
        for i,(jobid,v) in enumerate(self.items()):
            if type(v)==str:
                print("#%02d"%i,jobid,v)
            else:
                pid = v["pid"]
                pid = "NO_PID" if pid is None or pid=="" else str(pid)
                pid = " "*(6-len(pid))+pid
                if depth==0:
                    print("*** %02d"%i,jobid,v["state"],v["startat"].replace("T"," "),pid,v["jobname"])
                elif depth==1:
                    git = v["git"] if "git" in v else ""
                    NO_GIT="fatal: Not a git repository"
                    git = "NO_GIT" if git[:len(NO_GIT)]==NO_GIT else git
                    print("*** %02d"%i,jobid,v["state"],v["startat"].replace("T"," "),pid,v["jobname"], git)
                elif depth>1:
                    print(json.dumps(v))
                if searches:
                    print(self.jobfile(key=i,searches=searches))
        if depth>0:
            print("## File:",self.file)
            print("## Len:",len(self))

    def add_job_queue(self,job_queues={}):
        self.job_queues.update(job_queues)
        self.show_job_queue()

    def show_job_queue(self):
        list_job_queues = [name for name,func in self.job_queues.items()]
        print("[SSHJOB] We recognize %d job queues of : %s"%(len(self.job_queues),", ".join(list_job_queues)))

    #def __setitem__(self, key, value):
    #    if isinstance(key, str):
    #        assert "jobid" in value
    #        OrderedDict.__setitem__(self, value[""], value)
    #        for jid,info in reversed(self.items()):
    #            if info["jobname"] == key:
    #                    OrderedDict.__setitem__(self, jid, value)
    #    else:
    #        dict.__setitem__(self, key, value)

    def get_jid_from_key(self, key):
        if key in self:
            return key
        elif isinstance(key, str):
            for jid,info in reversed(self.items()):
                if "jobname" not in info: continue
                if info["jobname"] == key:
                        return jid
            return OrderedDict.__getitem__(self, key) # ERROR
        elif isinstance(key, int) and key<len(self):
            jid = list(self.keys())[key]
            return jid
        else:
            return OrderedDict.__getitem__(self, key) # ERROR

    def get_jid_from_keys(self,keys):
        try:
            gen = iter(keys)
        except TypeError as te:
            gen = iter([keys])
        res=[]
        while True:
            try:
                key = gen.__next__()
                res.append(self.get_jid_from_key(key))
            except StopIteration:
                break
        return res

    def range(self,*args):
        #print(range(*args))
        return self.get_jid_from_keys(range(*args))

    def __getitem__(self, key):
        jid = self.get_jid_from_key(key)
        return OrderedDict.__getitem__(self, jid)

    #def track()

    def __str__(self):
        return dict(self).__str__()

    def __repr__(self):
        return dict(self).__repr__()

    def index(self,jid):
        for i,(_,info) in enumerate(self.items()):
            if info["jobid"]==jid:
                return i
        return None

    def last(self):
        return list(self.values())[-1]

    ## com : commands
    ## type : Cluster type, such as raiden, abci
    ## hqw : alias to hold_qid
    def qsub(self,
            com,
            shellname=None,
            jc="+cpu",
            docker="",
            basedir="",
            baseshell="",
            opts=[],
            hold_jid=None,
            hqw=None,
            n=0,
            range=[0],
            qsuboption=[],
            git=False,
            **kwargs,
             ):

        system = self.environment.split(":")
        ssh    = None if len(system[0])==0 else system[0]
        sshdir = None if len(system[1])==0 else system[1]

        jc,docker = self.job_queues[system[-1]](jc,docker=docker)
        opt_er=get_opt()+jc
        opt_er="\n".join(opt_er)
        if n>0:
            print("jc",jc)
            print("docker",docker)
            print("opt_er",opt_er)
        header = None
        if "#localhost" in jc:
            header= open(path_base+"header_basic.sh","r").read()
        else:
            header= open(path_base+"header_gpu.sh","r").read() if "gpu" in opt_er or "gs" in opt_er \
                else open(path_base+"header_cpu.sh","r").read()
        header = header.replace("__DOCKER__INFO__",docker)
        footer=open(path_base+"footer.sh","r").read()
        if type(com)==str:
            com=[com]
        now = datetime.datetime.now().isoformat()
        if git:
            git_state = get_git_state(server=ssh,cd=sshdir)
        else:
            git_state = ""

        for i in range:
            ## Create shell file to run
            shellname = shellname if type(shellname)==str else shellname(i,basedir,baseshell)
            shellfile = opt_er
            for opt in opts:
                opt = opt if type(opt)==str else opt(i,basedir,baseshell)
                shellfile += opt
                shellfile += "\n"
            shellfile += header
            shellfile += "\n"
            for command in com:
                command = command if type(command)==str else command(i,basedir,baseshell)
                shellfile += command
                shellfile += "\n"
            shellfile += footer
            shellfile += "\n"

            # print(shellname)
            open(shellname,"w").write(shellfile)
            if ssh:
                assert type(sshdir)==str
                if len(system)==4 and len(system[2])>0:
                    scp_server=system[2]
                else:
                    scp_server=ssh
                print("[SSHJOB] Send %s to %s:%s"%(shellname,system[2],sshdir))
                scp(scp_server,sshdir,[shellname])

            commandline=[]
            if "#localhost" in jc:
                #commandline.append("nohup")
                #commandline.append("sh")
                pass
            else:
                commandline.append("qsub")
            commandline+=qsuboption
            if hold_jid or hqw:
                if hold_jid and hqw:
                    print("IGNORED: hqw=",hqw)
                commandline.append("-hold_jid")
                if hold_jid:
                    commandline.append(str(hold_jid))
                else:
                    commandline.append(str(hqw))
            commandline.append(shellname)

            if n>=1:
                print("[SSHJOB] Command Line:")
                print("[SSHJOB]"," ".join(commandline))

            if n>=2: # test
                print("[SSHJOB] We created (and sent if needed) a shell script file of *** "+shellname+" ***, but didn't run it.")
            elif "#localhost" in jc:
                jobid=int(get_datetime())
                commandline.append( ">"+shellname+".o"+str(jobid))
                commandline.append("2>"+shellname+".e"+str(jobid))

                pid,res = shell_nohup(commandline,server=ssh,cd=sshdir,**kwargs)
                try:
                    #commandline=" ".join(commandline)
                    #TEMP_PYRAIDEN_FILE="__temp.pyraiden__"
                    #commandline+="  & \n echo $! >"+TEMP_PYRAIDEN_FILE
                    #print(commandline)
                    #res=os.system(commandline)
                    #pid=int(open(TEMP_PYRAIDEN_FILE,"r").read().strip())
                    #os.system("rm "+TEMP_PYRAIDEN_FILE)
                    print("[SSHJOB] shell: [Job Number] : [Process ID] = %4d :"%(len(self)),pid)
                    self[jobid]=pyjob(**{"qsub":str(res), "jobid":str(jobid), "pid":str(pid),
                            "jobname":shellname, "state":"",
                            "jc":jc, "startat":now, "git":git_state,
                            "jobfile":shellfile,
                                 }) # res,state
                    assert int(pid)>0
                except:
                    print("[SSHJOB] Cannot find a new process ID of",shellname)
                    print("[SSHJOB] shell says: ",res)
                    print("[SSHJOB] This does NOT ALWAYS mean that a new job is NOT running. Just we cannot track the new process id.")
                    repr = {"qsub":str(res), "jobid":str(jobid), "pid":"PID_HERE (string)",
                                 "jobname":shellname, "state":"",
                                 "jc":jc, "startat":now, "git":git_state,
                                 "jobfile":shellfile,
                                 }.__repr__()
                    print("[SSHJOB] If the new job is sucessfully running, you can manually add it to pyjobs as:")
                    print("[SSHJOB] jobs[%s] = pyjob(**%s)"%(jobid,repr))
            else:
                res = self.shell_run(commandline,server=ssh,cd=sshdir,**kwargs)
                #try:
                jobid = int(parse_qsub_output(res["stdout"]))
                print("qsub: [Job Number] : [Job ID] = %4d : %d"%(len(self),jobid))
                if jobid>0:
                    self[jobid]=pyjob(**{"qsub":res, "jobid":jobid,
                            "jobname":shellname, "state":"",
                            "jc":jc, "startat":now, "git":git_state,
                            "jobfile":shellfile,
                                 }) # res,state
                    #try:
                    #    if os.path.exists(pyraiden_log_dir):
                    #        os.mkdir(pyraiden_log_dir)
                    #        open(pyraiden_log_dir+pyraiden_log_prefix+str(jobid),"w").write(json.dumps(raiden[jobid]))
                    #except:
                    #    print("Cannot save joblog",shellname)
                #except:
                else:
                    print("[SSHJOB] Cannot find a new job id of",shellname)
                    print("[SSHJOB] qsub says: ",res)
                    print("[SSHJOB] This does NOT ALWAYS mean that a new job is NOT running. Just we cannot track the new job id.")
                    repr = {"qsub":res,"jobid":"JOB_ID_HERE (string)",
                                         "jobname":shellname,"state":"",
                                         "jc":jc, "startat":now, "git":git_state,
                                         "jobfile":shellfile,
                                         }.__repr__()
                    print("[SSHJOB] If the new job is sucessfully running, you can manually add it to pyjobs as:")
                    print("[SSHJOB] jobs[JOB_ID (int)] = pyjob(**%s)"%repr)
        self.dump()

    def shell_run(self,commandline,server=None,cd=None,**kwargs):
        system = self.environment.split(":")
        ssh    = None if len(system[0])==0 else system[0]
        sshdir = None if len(system[1])==0 else system[1]
        ssh    = server if server else ssh
        sshdir = cd     if cd     else sshdir
        self.res = shell_run(commandline,server=ssh,cd=sshdir,**kwargs)
        return self.res

    def jobfile(self,key,searches=None):
        jid = self.get_jid_from_key(key)
        info = self[jid]
        if searches:
            rlt = []
            for search in searches:
                rlt.append( [line for line in self[key]["jobfile"].split("\n") if re.search(search,line)] )
            return rlt
        else:
            return self[key]["jobfile"].split("\n")

    def stdout(self,key,line=20,pipe=None,egrep=None,grep=None,pattern=None,**kwargs):
        system = self.environment.split(":")
        sshdir = "" if len(system[1])==0 else system[1]
        jid = self.get_jid_from_key(key)
        info = self[jid]
        jobname = info["jobname"]
        fno=jobname+".o"+info["jobid"]
        print('*** stdout file: %s/%s'%(sshdir,fno))
        if pipe:
            com="""
             cat %s | %s ;
            """%(fno,pipe)
        elif egrep:
            com="""
             cat %s | grep -E \'%s\' ;
            """%(fno,pipe)
        elif grep:
            com="""
             cat %s | grep \'%s\' ;
            """%(fno,pipe)
        elif line<0 or pattern:
            com="""
             cat %s ;
            """%(fno)
        else:
            com="""
             tail -n %d %s ;
            """%(line,fno)
        res = self.shell_run(com,**kwargs)
        if pattern:
            p=re.compile(pattern)
            return "\n".join([l for l in res["stdout"].split("\n") if re.match(p,l)])
        else:
            return res["stdout"]

    def stderr(self,key,line=20,pipe=None,egrep=None,grep=None,pattern=None,**kwargs):
        system = self.environment.split(":")
        sshdir = "" if len(system[1])==0 else system[1]
        jid = self.get_jid_from_key(key)
        info = self[jid]
        jobname = info["jobname"]
        fne=jobname+".e"+info["jobid"]
        print('*** stderr file: %s/%s'%(sshdir,fne))
        if pipe:
            com="""
             cat %s | %s ;
            """%(fne,pipe)
        elif egrep:
            com="""
             cat %s | grep -E \'%s\' ;
            """%(fne,pipe)
        elif grep:
            com="""
             cat %s | grep \'%s\' ;
            """%(fne,pipe)
        elif line<0 or pattern:
            com="""
             cat %s ;
            """%(fne)
        else:
            com="""
             tail -n %d %s ;
            """%(line,fne)
        res = self.shell_run(com,**kwargs)
        if pattern:
            p=re.compile(pattern)
            return "\n".join([l for l in res["stdout"].split("\n") if re.match(p,l)])
        else:
            return res["stdout"]

    def track(self,key,line=20,**kwargs):
        jid = self.get_jid_from_key(key)
        info = self[jid]
        jobname = info["jobname"]
        fno=jobname+".o"+info["jobid"]
        fne=jobname+".e"+info["jobid"]
        com="""
         echo \'***\' E %s ;
         head -n %d %s ;
         echo -----------------------[SSHJOB]------------------------------- ;
         tail -n %d %s ;
         echo ;
         echo ;
         echo \'***\' O %s ;
         head -n %d %s ;
         echo -----------------------[SSHJOB]------------------------------- ;
         tail -n %d %s """%(fne,line,fne,line,fne,fno,line,fno,line,fno)
        res = self.shell_run(com,**kwargs)
        return res["stdout"]

    def qstat(self,depth=5):
        qstat = self.shell_run(["qstat"])
        qlines = qstat["stdout"].strip().split("\n")
        qlines = [line.strip().split() for line in qlines[2:]]
        jobs={}
        for qline in qlines:
            if depth>2:
                print(qline)
            #print(len(qline))
            if len(qline)==10:
                jobid,prior,name,user,state,date,clock,node,job_type,ja_task_ID = qline
                jobs[jobid]={"jobid":jobid,"prior":prior,"name":name,"user":user,"state":state,"date":date,"clock":clock,"node":node,"job_type":job_type,"ja_task_ID":ja_task_ID}
            elif len(qline)==9:
                jobid,prior,name,user,state,date,clock,job_type,ja_task_ID = qline
                jobs[jobid]={"jobid":jobid,"prior":prior,"name":name,"user":user,"state":state,"date":date,"clock":clock,"node":"UNKNOWN","job_type":job_type,"ja_task_ID":ja_task_ID}
            else:
                if depth>1:
                    print(qline)
                    print(len(qline))
        return jobs

    def shellstat(self,depth=0):
        system_ = self.environment.split(":")
        ssh    = None if len(system_[0])==0 else system_[0]
        pids = [info["pid"] for jobid,info in self.items()]
        pnames = ["bash "+info["jobname"] for jobid,info in self.items()]
        return check_if_running(pids,pnames,server=ssh,debug=depth)

    def get_state(self,jobid,jobstates):
        jobid=str(jobid)
        if jobid in jobstates:
            return jobstates[jobid]["state"]
        else:
            return "x"
    def updating(self,depth=0,shellsystem=False):
        wait=[]
        fail_to_run=[]
        start=[]
        run=[]
        finishing=[]
        finish=[]
        if shellsystem:
            jobstates=self.shellstat(depth=depth)
        else:
            jobstates=self.qstat(depth=depth)
        for i,(jobid,info) in enumerate(self.items()):
            try:
                jobid=int(info["jobid"])
            except:
                continue
            jobname=info["jobname"]
            if shellsystem:
                if jobstates[i]:
                    info["state"]="r"
                    run.append(jobname)
                else:
                    info["state"]="d"
                    finish.append(jobname)
            else:
                state=self.get_state(jobid,jobstates)
                if state=="x": # not on queue
                    if info["state"]=="":
                        fail_to_run.append(jobname)
                    else:
                        finish.append(jobname)
                    info["state"]="d"
                elif state=="r":
                    if info["state"]=="":
                        start.append(jobname)
                    run.append(jobname)
                    info["state"]=state
                elif state=="qw":
                    wait.append(jobname)
                    info["state"]=state
                elif state=="dr":
                    finishing.append(jobname)
                    info["state"]=state
                else:
                    print("Unknown job state: ",state)
        return {\
               "wait":wait,
               "fail_to_run":fail_to_run,
               "start":start,
               "run":run,
               "finishing":finishing,
               "finish":finish}

    # Delete item from OrderedDict
    def disown(self,keys):
        jidx = self.get_jid_from_keys(keys)
        #print("Job IDs: ",jidx)
        for jid in jidx:
            del self[jid]

    def _kill(self,infos,kill_by_pid=False,debug=0):
        if isinstance(infos,dict) and "jobid" in infos:
            if "pid" in infos and infos["pid"] is not None:
                self._kill(int(infos["pid"]),kill_by_pid=True,debug=debug)
            else:
                self._kill(int(infos["jobid"]),debug=debug)
        elif isinstance(infos,int):
            pid = str(infos)
            if kill_by_pid:
                res = kill_dependents(pid,debug=debug)
            else:
                if debug>9:
                    res = self.shell_run(["echo",pid])
                else:
                    res = self.shell_run(["qdel",pid])
            print(res["stdout"])
        elif isinstance(infos,list):
            for info in infos:
                self._kill(info,debug=debug)
        elif type(infos)==str:
            raise NotImplemented
        else:
            raise NameError("NotFound: "+infos.__str__())

    # Stop job
    def kill(self,keys,debug=0):
        for key in self.get_jid_from_keys(keys):
            self._kill(self[key],debug=debug)

    def killall(self,debug=0):
        for jobid,info in self.items():
            self._kill(info,debug=debug)

    # Delete job log files
    def rm(self,keys,save=True, **kwargs):
        jidx = self.get_jid_from_keys(keys)
        print("Job IDs: ",jidx)
        res = self.trash(jidx, **kwargs)
        self.disown(jidx)
        if save:
            self.dump()
        return res

    def rmall(self,save=False):
        self.rm(keys=self.keys())
        super(sshjobsys, self).clear()

    # Stop and Delete job log files
    def bye(self,keys,save=True):
        jidx = self.get_jid_from_keys(keys)
        print("Job IDs: ",jidx)
        for key in jidx:
            self.kill(key)
        print("[SSHJOB] Wait 2 seconds...")
        sleep(2)
        for key in jidx:
            self.rm(key,save=save)

    def trash(self,keys,force=False, **kwargs):
        jidx = self.get_jid_from_keys(keys)
        com="mkdir -p trush ; "
        try_rm=[]
        for jid in jidx:
            info=self[jid]
            jobname=info["jobname"]
            d=False
            if force:
                d=True
            elif info["state"] in ["d"]:
                d=True
            if d:
                print("*** TRUSHING LOG", jobname)
                fno=jobname+".o"+info["jobid"]
                fne=jobname+".e"+info["jobid"]
                com+="mv %s %s %s trush/ ; "%(jobname,fno,fne)
                try_rm.append(jid)
            else:
                print("Cannot trash log files of running job ", jobname)
        print("[SSHJOB] Try to remove stdout/stderr of "+" ".join([str(t) for t in try_rm])+" remotely.")
        res = self.shell_run(com.split(" "), **kwargs)
        return res # TODO: return only if succeed to trash

    # A function that check the remote environment works
    def check_env(self):
        system = self.environment.split(":")
        ssh    = None if len(system[0])==0 else system[0]
        sshdir = None if len(system[1])==0 else system[1]

        res = self.shell_run("""if [ -d %s ]; then echo "SUCCESS"; fi"""%sshdir,server=ssh,cd=".")
        if "SUCCESS" in res["stdout"]:
            print("check_env:SUCCESS")
            return 0
        return -1

    # A function to init the remote environment
    def init_env(self):
        system = self.environment.split(":")
        ssh    = None if len(system[0])==0 else system[0]
        sshdir = None if len(system[1])==0 else system[1]

        if self.check_env() != 0:
            print("Initialing an environment of "+self.environment)
            res=self.shell_run("""mkdir -p %s/trush"""%sshdir,server=ssh,cd=".")
            self.check_env()
            return res
        else:
            print("Existing an environment of "+self.environment)

    @property
    def server(self):
        system = self.environment.split(":")
        ssh    = None if len(system[0])==0 else system[0]
        sshdir = None if len(system[1])==0 else system[1]
        return ssh
    @property
    def pwd(self):
        system = self.environment.split(":")
        ssh    = None if len(system[0])==0 else system[0]
        sshdir = None if len(system[1])==0 else system[1]
        return sshdir
    # AN easy rapper for self.sell_run()
    def exec(self,commandline, **kwargs):
        return self.shell_run(commandline, **kwargs)["stdout"]
    def execp(self,commandline, **kwargs):
        print(self.shell_run(commandline, **kwargs)["stdout"])
    def ls(self,pwd=".",lah=False, **kwargs):
        assert isinstance(pwd,str)
        system = self.environment.split(":")
        ssh    = None if len(system[0])==0 else system[0]
        sshdir = None if len(system[1])==0 else system[1]
        if lah:
            res=self.shell_run("""ls -lah %s"""%pwd, **kwargs)
        else:
            res=self.shell_run("""ls %s"""%pwd, **kwargs)
        return res["stdout"]

pyjobs = sshjobsys

class pyjob(dict):
    def __init__(self,jobid,jobname,
                 jobfile="",
                 state="",jc="",qsub="",startat="",git="",
                 pid=None):


        # jobid : name of shellfile
        # jobname : name of shellfile
        # jobfile : contexts of shellfile

        super(pyjob, self).__init__({"qsub":qsub,
                          "jobid":str(jobid),
                          "jobname":jobname,
                          "state":state,
                          "jc":jc,
                          "startat":startat,
                          "git":git,
                          "jobfile":jobfile,
                          "pid":str(pid) if pid is not None else None,
                                 })

    @property
    def __dict__(self):
        return dict(self)

# This function needs to be overwritten in some environments.
def parse_qsub_output(res):
    assert isinstance(res,str)
    pattern = '.*Your job (\d+) .*has been submitted.*'
    result = re.match(pattern, repr(res))
    if result:
        jid=result.group(1)
        return jid
    else:
        print("[SSHJOB] NOT SUBMITTED: ",res)
        return "-1"

#def rerun(jobnames,raiden):
#    jobs=qstat()
#    for job in jobnames:
#        state=get_state("2444381",jobs)
#        if "r"==state:
#            jobid=raiden[job]
#            stop = subprocess.run(["qdel",jobid], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
#            print(stop)
#            star = subprocess.run(["qsub",job], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
#            print(star)
#            raiden[job] = subprocess.run(["qsub",shellfile], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
#        else:
#            print(job," state is ",state)

def get_opt():
    return [\
        "#!/bin/bash",
        ]

def get_date_name():
    return "sh"+datetime.datetime.now().strftime('%Y%m%d-%H%M-%S%f')[2:-4]
def get_datetime():
    return datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')[2:-4]

def help():
    print("jobs = pyjobs()")
    print("jobs.qsub()")
    print("jobs.show()")
    print()
    print("jobtype: 1d,3d,7d")
    print("jobtype: +gpu,8g,3d -> +g8 7d")
    print()
    print("See https://github.com/shuheikurita/sshjob")

if __name__ == '__main__':
    help()
