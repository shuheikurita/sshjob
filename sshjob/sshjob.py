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
        return "0.0.dev12"
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
        self.environment = environment
        self.job_queues = DEFAULT_JOB_QUEUE
        self.add_job_queue(job_queues)

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

    def show(self,system=None,depth=0,no_update=False,search=[]):
        system = system if system is not None else self.environment
        system = system.split(":")
        searches = [search] if isinstance(search,str) else search
        if not no_update:
            try:
                if "SHELL" in system[-1]:
                    self.updating(shellsystem=True,depth=depth-1)
                else:
                    self.updating()
            except:
                print("Update failed. Use no_update=True")
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

                pid,res = shell_nohup(commandline,server=ssh,cd=sshdir)
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
                res = shell_run(commandline,server=ssh,cd=sshdir)
                try:
                    res = parse_qsub_output(res)
                    jobid=int(res["jobid"])
                    print("qsub: [Job Number] : [Job ID] = %4d : %d"%(len(self),jobid))
                    self[jobid]=pyjob(**{"qsub":res, "jobid":res["jobid"],
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
                except:
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

    def shell_run(self,commandline,ssh_bash_profile=True):
        system = self.environment.split(":")
        ssh    = None if len(system[0])==0 else system[0]
        sshdir = None if len(system[1])==0 else system[1]
        return shell_run(commandline,server=ssh,cd=sshdir,ssh_bash_profile=ssh_bash_profile)

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

    def track(self,key,system=None,line=20):
        jid = self.get_jid_from_key(key)
        info = self[jid]
        jobname = info["jobname"]
        fno=jobname+".o"+info["jobid"]
        fne=jobname+".e"+info["jobid"]
        com=""" echo \'***\' E %s ;
         head -n %d %s ;
         echo -----------------------[SSHJOB]------------------------------- ;
         tail -n %d %s ;
         echo ;
         echo ;
         echo \'***\' O %s ;
         head -n %d %s ;
         echo -----------------------[SSHJOB]------------------------------- ;
         tail -n %d %s """%(fne,line,fne,line,fne,fno,line,fno,line,fno)
        res = self.shell_run(com,ssh_bash_profile=False)
        print(res["stdout"])

    def qstat(self,depth=5):
        qstat = self.shell_run(["qstat"], system=self.system)
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

    def updating(self,depth=0,shellsystem=False):
        system = self.environment

        wait=[]
        fail_to_run=[]
        start=[]
        run=[]
        finishing=[]
        finish=[]
        if shellsystem:
            system_ = system.split(":")
            ssh    = None if len(system_[0])==0 else system_[0]
            pids = [info["pid"] for jobid,info in self.items()]
            pnames = ["bash "+info["jobname"] for jobid,info in self.items()]
            local_stat = check_if_running(pids,pnames,server=ssh,debug=depth)
        else:
            jobstates=self.qstat(system=system,depth=depth)
        for i,(jobid,info) in enumerate(self.items()):
            try:
                jobid=int(info["jobid"])
            except:
                continue
            jobname=info["jobname"]
            if shellsystem:
                if local_stat[i]:
                    info["state"]="r"
                    run.append(jobname)
                else:
                    info["state"]="d"
                    finish.append(jobname)
            else:
                state=get_state(jobid,jobstates)
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
        print("Job IDs: ",jidx)
        for jid in jidx:
            del self[jid]

    # Stop job
    def kill(self,keys,debug=0):
        system = self.environment.split(":")
        ssh    = None if len(system[0])==0 else system[0]
        for key in self.get_jid_from_keys(keys):
            kill(self[key],server=ssh,debug=debug)

    def kill_all(self,debug=0):
        system = self.environment.split(":")
        ssh    = None if len(system[0])==0 else system[0]
        for jobid,info in self.items():
            kill(info,server=ssh,debug=debug)

    # Delete job log files
    def rm(self,keys,save=True):
        system = self.environment.split(":")
        ssh    = None if len(system[0])==0 else system[0]
        sshdir = None if len(system[1])==0 else system[1]
        jidx = self.get_jid_from_keys(keys)
        print("Job IDs: ",jidx)
        self.trash(jidx,server=ssh,cd=sshdir)
        # TODO: do not disown when trashing fail.
        self.disown(jidx)
        if save:
            self.dump()

    def rm_all(self,save=False,system=None):
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

    def trash(self,keys,force=False,server=None,cd=None):
        jidx = self.get_jid_from_keys(keys)
        com="mkdir -p trush ; "
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
            else:
                print("Cannot trash log files of running job ", jobname)
        res = shell_run(com.split(" "),server=server,cd=cd)
        print(res)

    # A function that check the remote environment works
    def check_env(self,system=None):
        system = self.environment.split(":")
        ssh    = None if len(system[0])==0 else system[0]
        sshdir = None if len(system[1])==0 else system[1]

        res = shell_run("""if [ -d %s ]; then echo "SUCCESS"; fi"""%sshdir,server=ssh,cd=".")
        if "SUCCESS" in res["stdout"]:
            print("check_env:SUCCESS")
            return 0
        return -1

    # A function to init the remote environment
    def init_env(self,system=None):
        system = self.environment.split(":")
        ssh    = None if len(system[0])==0 else system[0]
        sshdir = None if len(system[1])==0 else system[1]

        if self.check_env(system=system) != 0:
            print("Initialing...")
            res=shell_run("""mkdir -p %s"""%sshdir)
            self.check_env(system=system)
            return res
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
        return self

def parse_qsub_output(res):
    if type(res)!=dict:
        res=subprocess_res_to_dict(res)
    said=res["stdout"]
    #print(said)
    says=said.split()
    if says[-1] != "submitted":
        print("NOT SUBMITTED: ",res)
        return {"id":"-1","res":res}
    else:
        jid=says[2]
    return {"jobid":jid,"res":res}

## Pyraiden support

def gstat(raiden):
    gpu_stat(raiden)
def gpu_stat(raiden):
    qany("gpu_stat",raiden)
def qacct(raiden):
    qany("qacct -j",raiden)

def qany(command,raiden):
    for jobid,info in raiden.items():
        if type(jobid)!=int: continue
        jobname=info["jobname"]
        res = subprocess.run([command,info["jobid"]], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print("***** "+jobname,end="")
        said=res.stdout.decode('utf-8').strip()
        print(said)


def get_state(jobid,jobstates):
    jobid=str(jobid)
    if jobid in jobstates:
        return jobstates[jobid]["state"]
    else:
        return "x"

def kill(infos,local=False,server=None,debug=0):
    if isinstance(infos,dict) and "jobid" in infos:
        if "pid" in infos and infos["pid"] is not None:
            kill(int(infos["pid"]),local=True,server=server,debug=debug)
        else:
            kill(int(infos["jobid"]),server=server,debug=debug)
    elif isinstance(infos,int):
        pid = str(infos)
        if local:
            res = kill_dependents(pid,server=server,debug=debug)
        else:
            if debug>9:
                res = shell_run(["echo",pid],server=server)
            else:
                res = shell_run(["qdel",pid],server=server)
        print(res["stdout"])
    elif isinstance(infos,list):
        for info in infos:
            kill(info,server=server,debug=debug)
    elif type(infos)==str:
        raise NotImplemented
    else:
        raise NameError("NotFound: "+infos.__str__())

def track_tail(raiden,n=3,eo="e",updating=True):
    if eo not in ["e","o"]:
        print("eo must be e/o")
    if updating:
        raiden.updating()
    seems_end=0
    for jobname,info in raiden.items():
        print("***** "+jobname,end="")
        if info["state"] in ["","qw"]:
            print(" ...seems not runing")
            continue
        else:
            print()
        jid=info["jobid"]
        fne=jobname+"."+eo+info["jobid"]
        try:
            lasts=open(fne,"r").readlines()[-n:]
        except:
            print("Can't open ",fne)
            continue
        for l in lasts:
            print(l.strip())
        if len(lasts)>0:
            if re.search("end",lasts[-1], re.IGNORECASE) != None:
                seems_end+=1
    print("***** End: ",seems_end,"/",len(raiden),seems_end/len(raiden))

def track_match(raiden,pattern,eo="e",updating=True):
    if eo not in ["e","o"]:
        print("eo must be e/o")
    p=re.compile(pattern)
    if updating:
        raiden.updating()
    seems_end=0
    for jobname,info in raiden.items():
        print("***** "+jobname,end="")
        if info["state"] in ["","qw"]:
            print(" ...seems not runing")
            continue
        else:
            print()
        jid=info["jobid"]
        fne=jobname+"."+eo+info["jobid"]
        lasts=[l for l in open(fne,"r").readlines() if re.match(p,l)]
        for l in lasts:
            print(l.strip())
        if len(lasts)>0:
            seems_end+=1
    print("***** Match: ",seems_end,"/",len(raiden),seems_end/len(raiden))

def qdel(jobid):
    stop = subprocess.run(["qdel",jobid], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return stop

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
