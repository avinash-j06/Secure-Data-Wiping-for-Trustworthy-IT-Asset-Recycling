import psutil

def list_drives():
    drives = []
    for part in psutil.disk_partitions(all=False):
        drives.append(f"{part.device} ({part.fstype}) - {part.mountpoint}")
    return drives
