#!/usr/bin/env python
# -*- coding:utf-8 -*-

# Author: Shuhei Kurita
# Mailto: kurita@nlp.ist.i.kyoto-u.ac.jp
# Licence: GPL v2

from __future__ import absolute_import
from __future__ import unicode_literals


# Util functions that are for running process from python and independent from pyraiden

import subprocess,os,re

TEMP_PYRAIDEN_FILE="__temp.pyraiden__"

## Run and ssh

bash_types = {
    1:["bash -c \"", "\""],
    2:["'", "'"],
             }

def shell_run(commandline,server=None,cd=None,**kwargs):
    if server:
        cd = cd if cd is not None else "."
        return ssh_run(commandline,server,cd,**kwargs)
    else:
        if isinstance(commandline,str):
            commandline=commandline.split()
        assert isinstance(commandline,list)
        if cd is not None:
            commandline = ["cd ",cd,";"]+commandline

        #res = subprocess.run(commandline, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        commandline = " ".join(commandline)
        open(TEMP_PYRAIDEN_FILE,"w").write(commandline)
        res = subprocess.run(["bash",TEMP_PYRAIDEN_FILE], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        #os.system("rm "+TEMP_PYRAIDEN_FILE)

        result=res.__dict__
        result["stdout"] = res.stdout.decode("utf-8").strip() if res.stdout else ""
        result["stderr"] = res.stderr.decode("utf-8").strip() if res.stderr else ""
        return result

def shell_nohup(shellfile,server=None,cd=None,**kwargs):
    if server:
        cd = cd if cd is not None else "."
        return ssh_nohup(shellfile,server,cd,**kwargs)
    else:
        if isinstance(shellfile,str):
            commandline=shellfile.split()
        else:
            commandline=shellfile
        assert isinstance(commandline,list)
        commandline = " ".join(commandline)
        commandline = "cd %s;"%cd if cd is not None else "" + "nohup bash " + commandline
        commandline+="  & \n echo $! >"+TEMP_PYRAIDEN_FILE
        print(commandline)
        res=os.system(commandline)
        try:
            pid=int(open(TEMP_PYRAIDEN_FILE,"r").read().strip())
        except:
            pid=-1
        os.system("rm "+TEMP_PYRAIDEN_FILE)
        result={"returncode":res,"stdout":"","stderr":""}
        return str(pid),result

def ssh_run(commandline,server,cd,debug=False,ssh_bash_profile=True,bash_type=1,file_mode=False):
    if isinstance(commandline,list):
        commandline=" ".join(commandline)
    assert isinstance(commandline,str)
    profile  = " if [ -f .bash_profile ]; then source .bash_profile ; fi " if ssh_bash_profile else ""
    bash_type = bash_types[bash_type]
    command="ssh -tt %s %s %s ; cd %s ; echo __RUN_VIA_SSH__ >&2 ; echo __RUN_VIA_SSH__ ; %s %s "%\
            (server,bash_type[0],profile,cd,commandline,bash_type[1])
    if debug:
        print("ssh_run:",command)
    if file_mode:
        open(TEMP_PYRAIDEN_FILE,"w").write(command)
        res = subprocess.run(["bash",TEMP_PYRAIDEN_FILE], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    else:
        res=subprocess.run(command.split(" "), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result=res.__dict__
    result["stdout"] = res.stdout.decode("utf-8").split("__RUN_VIA_SSH__")[-1].strip() if res.stdout else ""
    result["stderr"] = res.stderr.decode("utf-8").split("__RUN_VIA_SSH__")[-1].strip() if res.stderr else ""
    return result

def ssh_nohup(shellfile,server,cd,**kwargs):
    if isinstance(shellfile,list):
        commandline=" ".join(shellfile)
    else:
        commandline=shellfile
    assert isinstance(commandline,str)
#    profile  = " if [ -f .bash_profile ]; then source .bash_profile ; fi " if ssh_bash_profile else ""
    nohup_pre =" nohup bash"
    nohup_post=" </dev/null & echo PID=$!= "
#    # MUST BE single quotation.
#    # MUST NOT USE BASH
#    # MUST BE sleep at the last.
#    command="ssh -tt %s ' %s ; cd %s;echo __RUN_VIA_SSH__ >&2 ; echo __RUN_VIA_SSH__ ; %s %s %s ; sleep 2' "%(server,profile,cd,nohup_pre,commandline,nohup_post)
#    print("command",command)
#    res=subprocess.run(command.split(" "), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
#    result=res.__dict__
    command=" %s %s %s ; sleep 2 "%(nohup_pre,commandline,nohup_post)
    result = ssh_run(command,server,cd,**kwargs)
    #result["stdout"] = res.stdout.decode("utf-8").split("__RUN_VIA_SSH__")[-1].strip() if res.stdout else ""
    #result["stderr"] = res.stderr.decode("utf-8").split("__RUN_VIA_SSH__")[-1].strip() if res.stderr else ""
    #result=shell_run(command)
    #result["stdout"] = result["stdout"].split("__RUN_VIA_SSH__")[-1].strip()
    #result["stderr"] = result["stderr"].split("__RUN_VIA_SSH__")[-1].strip()
    return parse_pid_output(result["stdout"]),result

def parse_pid_output(res):
    assert isinstance(res,str)
    pattern = '.*PID=(\d+)=.*'
    result = re.match(pattern, repr(res))
    if result:
        jid=result.group(1)
        return jid
    else:
        print("[SSHJOB] NOT SUBMITTED: ",res)
        return "-1"

def scp(server,sshdir,files):
    assert type(server)==str
    assert type(sshdir)==str
    sshdir = sshdir[:-1] if sshdir[-1]=="/" else sshdir
    scpcom=["scp"]+files+[server+":"+sshdir]
    res = subprocess.run(scpcom, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print("scp %s %s:%s"%(" ".join(files),server,sshdir))
    for said in res.stdout.decode('utf-8').strip().split("\n"):
        print(said)

def shell_cats(files,server=None,sshdir=None):
    flag_split="____SHELL_CAT____"
    if isinstance(files,str):
        files=[files]
    com=[]
    for i,file in enumerate(files):
        com+=["echo", flag_split,";","cat",file,";"]
    res = shell_run(com, server=server,cd=sshdir)
    return res["stdout"].split(flag_split)

def shell_cat(files,server=None,sshdir=None):
    if isinstance(files,str):
        files=[files]
    com=[]
    for i,file in enumerate(files):
        com+=["cat",file,";"]
        #com+=["echo", "\'***\'", file, ";", "cat", file, ";"]
    res = shell_run(com, server=server,cd=sshdir)
    return res["stdout"]

def subprocess_res_to_dict(res):
    result=res.__dict__
    if res.stdout:
        result["stdout"]=res.stdout.decode('utf-8').strip()
    if res.stderr:
        result["stderr"]=res.stderr.decode('utf-8').strip()
    return result


# process utils

def collect_child_process(pid,pid_set=set(),server=None,debug=0):
    res=shell_run(["ps","-o","pid=","--ppid",pid],server=server)
    if debug>0:
        print("collect_child_process: server:",server)
        print("collect_child_process",res["stdout"])
    for p in res["stdout"].split():
        try:
            int(p)
        except:
            continue
        if p not in pid_set:
            pid_set.add(p)
            pid_set = collect_child_process(p,pid_set,server=server)
    return pid_set

def check_if_running(pids,pnames,server=None,debug=0):
    assert len(pids)==len(pnames)
    result=[]
    for pid,pname in zip(pids,pnames):
        pid=str(pid)
        int(pid)
        res=shell_run(["ps","-p",pid,"-o","args="],server=server)
        if debug>1:
            print("check_if_running",res,pid,pname)
        res = res["stdout"].strip()
        if pname is not None and pname==res:
            result.append(True)
        elif pname is None and len(res)>0:
            result.append(True)
        else:
            result.append(False)
    return result

def kill_dependents(pid,server=None,debug=0):
    pid=str(pid)
    int(pid)
    pids=list(collect_child_process(pid,server=server,debug=debug))
    pids=sorted(pids,reverse=True)+[pid]
    print("Kill following pid jobs:",pids)
    if debug>9:
        return shell_run(["echo"]+pids,server=server)
    else:
        return shell_run(["kill","-9"]+pids,server=server)


# Utils

## git

def get_git_state(server=None,cd=None):
    try:
        csub="""git --no-pager log --pretty=format:%h%x09%an%x09%ad%x09%s --date=iso -1"""
        x=shell_run(csub.split(" "),server=server,cd=cd)
        return x["stdout"].strip().replace("\t","  ")
    except:
        raise
        return ""
