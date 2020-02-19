def remote(commands, shellname, jc="+cpu", basedir="", baseshell="", opts=[], raiden={}, hold_jid=None, n=False,
         range=[0], ssh=None):
  opt_er = get_opt() + get_jcac(jc)
  opt_er = "\n".join(opt_er)
  header = open(pyraiden_base + "header_cpu.sh", "r").read() if "gpu" not in opt_er \
    else open(pyraiden_base + "header_gpu.sh", "r").read()
  footer = open(pyraiden_base + "footer.sh", "r").read()
  if type(commands) == str:
    commands = [commands]
  #     if type(hold_jid)==str:
  #         hold_jid=[hold_jid for _ in commands]
  #     elif type(hold_jid)==list:
  #         hold_jid+=[None for _ in range(len(commands)-len(hold_jid))]
  now = datetime.datetime.now().isoformat()
  for i in range:
    shellname = shellname if type(shellname) == str else shellname(i, basedir, baseshell)
    print(shellname)
    with open(shellname, "w") as f:
      f.write(opt_er)
      for opt in opts:
        opt = opt if type(opt) == str else opt(i, basedir, baseshell)
        f.write(opt)
        f.write("\n")
      f.write(header)
      f.write("\n")
      for command in commands:
        command = command if type(command) == str else command(i, basedir, baseshell)
        f.write(command)
        f.write("\n")
      f.write(footer)
      f.write("\n")
    # command=["qsub",shellname]
    prefix = []
    if ssh:
      prefix.append("ssh")
      prefix.append(ssh)
    if n:  # test
      raiden[shellname] = open(shellname, "r").read()
    else:
      if hold_jid is None:
        res = subprocess.run(prefix + ["qsub", shellname], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
      else:
        res = subprocess.run(prefix + ["qsub", "--hold_jid", hold_jid, shellname], stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
      res2 = parse_qsub_output(res)
      raiden[shellname] = {"qsub": res2, "jobid": res2["jobid"], "jobname": shellname, "state": "", "jc": jc,
                           "startat": now}  # res,state
  return raiden