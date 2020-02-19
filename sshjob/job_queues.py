
def sge_default(short,jc=None,docker=""):
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
