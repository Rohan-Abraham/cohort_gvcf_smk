#!/usr/bin/env python3
import re
import subprocess as sp
import shlex
import sys
import time
import logging
from CookieCutter import CookieCutter

logger = logging.getLogger("__name__")

STATUS_ATTEMPTS = 20

jobid = sys.argv[1]

cluster = CookieCutter.get_cluster_option()

status = None

for i in range(STATUS_ATTEMPTS):
    try:
        sacct_res = sp.check_output(shlex.split(f"sacct {cluster} -P -b -j {jobid} -n"))
        res = {
            x.split("|")[0]: x.split("|")[1]
            for x in sacct_res.decode().strip().split("\n")
            if x
        }
        # sacct can succeed but not yet have ingested this jobid (race
        # condition right after submission) -- only treat this as a
        # resolved status if the jobid is actually present, otherwise
        # fall through to scontrol/retry instead of crashing below.
        if jobid in res:
            status = res[jobid]
            break
    except sp.CalledProcessError as e:
        logger.error("sacct process error")
        logger.error(e)
    except IndexError as e:
        logger.error(e)
        pass
    # Try getting job with scontrol instead in case sacct is misconfigured
    # or hasn't ingested the job yet.
    try:
        sctrl_res = sp.check_output(
            shlex.split(f"scontrol {cluster} -o show job {jobid}")
        )
        m = re.search(r"JobState=(\w+)", sctrl_res.decode())
        if m:
            status = m.group(1)
            break
    except sp.CalledProcessError as e:
        logger.error("scontrol process error")
        logger.error(e)

    if i >= STATUS_ATTEMPTS - 1:
        print("failed")
        exit(0)
    else:
        time.sleep(1)

if status is None:
    print("failed")
    exit(0)

if status == "BOOT_FAIL":
    print("failed")
elif status == "OUT_OF_MEMORY":
    print("failed")
elif status.startswith("CANCELLED"):
    print("failed")
elif status == "COMPLETED":
    print("success")
elif status == "DEADLINE":
    print("failed")
elif status == "FAILED":
    print("failed")
elif status == "NODE_FAIL":
    print("failed")
elif status == "PREEMPTED":
    print("failed")
elif status == "TIMEOUT":
    print("failed")
elif status == "SUSPENDED":
    print("running")
else:
    print("running")
