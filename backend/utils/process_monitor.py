import psutil

def get_process_info(pid: int):
    """Return (process_name, executable_path) for given PID.
    If PID does not exist or access is denied, return (None, None).
    """
    try:
        proc = psutil.Process(pid)
        name = proc.name()
        exe = proc.exe() if hasattr(proc, 'exe') else None
        return name, exe
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return None, None
