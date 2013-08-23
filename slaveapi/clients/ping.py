from subprocess import check_output, STDOUT

def ping(host, count=4, deadline=None):
    """Tries to ping "host". Returns True if all request packets recieve a
       a reply and False otherwise."""
    cmd = ["ping", "-c", str(count)]
    if deadline:
        cmd += ["-w", str(deadline)]
    cmd += [host]
    for line in check_output(cmd, stderr=STDOUT):
        if "0% packet loss" in line:
            return True
    return False
