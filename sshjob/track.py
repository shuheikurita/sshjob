import os,re
from time import sleep
from sshjob.sshjob import *
import traceback

def printjob(info,first=20,end=20):
    jobname=info["jobname"]
    print("***** "+jobname,end="")
    #if info["state"] in ["","qw"]:
    #    print(" ...seems not runing")
    #else:
    if True:
        print()
        try:
            fne=jobname+".e"+info["jobid"]
            print("*** E "+fne)
            lines=open(fne,"r").readlines()
            lines = lines if len(lines)<first+end else \
                        lines[:first]+\
                        ["-----------------------[PYRAIDEN]-------------------------------\n"]+\
                        lines[-end:]
            for line in lines:
                print(line,end="")
        except:
            print("[PYRAIDEN] NOT FOUND: ",fne)
            #traceback.print_exc()
        print()
        try:
            fno=jobname+".o"+info["jobid"]
            print("*** O "+fno)
            lines=open(fno,"r").readlines()
            lines = lines if len(lines)<first+end else \
                        lines[:first]+\
                        ["-----------------------[PYRAIDEN]-------------------------------\n"]+\
                        lines[-end:]
            for line in lines:
                print(line,end="")
        except:
            print("[PYRAIDEN] NOT FOUND: ",fno)
            #traceback.print_exc()
        print()


def track(raiden=None,jobname=None,jobid=None,updating=True,last=-1,line=20):
    if raiden:
        if "jobid" in raiden and "jobname" in raiden:
            printjob(raiden)
        else:
            assert type(raiden) in [dict,list,set,pyjobs]
            if updating:
                update(raiden)
            for jobname,info in raiden.items():
                printjob(info,first=line,end=line)
    else:
        if jobid is None and jobname:
            fs=listjobfile(jobname)
            print("[PYRAIDEN] track(): MATCH FILE (num:%d) IS "%len(fs),fs)
            jobidx=getjobidx(query_or_filelist=fs)
            print("[PYRAIDEN] track(): JOBIDX IS ",jobidx)
            if last is None:
                for jobid in jobidx:
                    track(jobname=jobname,jobid=jobid)
            else:
                last = -1 if last is True else last
                assert type(last)==int
                track(jobname=jobname,jobid=jobidx[last])
        elif jobid and jobname is None:
            jobid=str(jobid)
            fs=listjobfile(jobid)
            print("[PYRAIDEN] track(): MATCH FILE (num:%d) IS "%len(fs),fs)
            jobnames=list(getjobname(query_or_filelist=fs))
            for jobname in jobnames:
                print(jobname)
                track(jobname=jobname,jobid=jobid)
        elif jobname and jobid:
            printjob({"jobname":jobname,"jobid":jobid},first=line,end=line)
        else:
            print("[PYRAIDEN] track(): either raiden, jobname or jobid required!")

def listjobfile(query):
    if query is None: return []
    query=str(query) if type(query)==int else query
    fs=os.listdir(".")
    #print(query,fs)
    fs=list(filter(lambda x:re.search(query,x),fs))
    return fs

def getjobidx(query_or_filelist): # get jobid from query
    if type(query_or_filelist)==str:
        fs=listjobfile(query_or_filelist)
    else:
        fs=query_or_filelist
    jobids=set()
    for f in fs:
        m=re.search("[0-9]{7}",f)
        if m:
            jobids.add(m.group())
    return sorted(list(jobids))
def getjobname(query_or_filelist): # get jobname from query such as jobidx
    if type(query_or_filelist)==str:
        fs=listjobfile(query_or_filelist)
    else:
        fs=query_or_filelist
    shellfile=set()
    for f in fs:
        #print(f)
        f=re.sub(".(e|o)[0-9]{7}","",f)
        #print(f)
        shellfile.add(f)
        #m=re.search(r'(?<=\.sh.(e|o))[0-9]+', f)
    return shellfile

def catjobfile(query): # query can be jobid
    shellfile=getjobname(query)
    for f in shellfile:
        print("**** ",f)
        sleep(1)
        print(open(f,"r").read())
    return shellfile

def trackjobid(jobid):
    shellfile=list(getjobname(query=jobid))
    try:
        assert len(shellfile)==1
    except:
        print(len(shellfile))
        raise
    track(jobname=shellfile[0],jobid=jobid)

def extract_jobid_like(fs):
    ids=set()
    for f in fs:
        #m=re.search(r'(?<=\.sh.(e|o))[0-9]+', f)
        m=re.search(r'[0-9]{7}', f)
        if m:
            ids.add(m.group())
    return sorted(list(ids))
