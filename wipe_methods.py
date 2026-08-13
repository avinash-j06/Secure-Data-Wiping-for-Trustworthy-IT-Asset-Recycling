# wipe_methods.py
import os

CHUNK_SIZE = 4 * 1024 * 1024  # 4 MB per write (tunable)


def overwrite_file_stream(file_path: str, passes: int, per_chunk_callback=None):
    """
    Overwrite file `passes` times in streaming chunks.
    per_chunk_callback(chunk_bytes) is called after each chunk is written.
    """
    if not os.path.isfile(file_path):
        return False

    size = os.path.getsize(file_path)
    # if file is empty, nothing to write; just call callback once with 0 and return
    if size == 0:
        if per_chunk_callback:
            per_chunk_callback(0)
        return True

    try:
        with open(file_path, "r+b") as f:
            for p in range(passes):
                f.seek(0)
                written = 0
                while written < size:
                    to_write = min(CHUNK_SIZE, size - written)
                    f.write(os.urandom(to_write))
                    # flush & fsync to help ensure data reaches the disk
                    f.flush()
                    try:
                        os.fsync(f.fileno())
                    except OSError:
                        # fsync may not be available for all file systems; ignore if it fails
                        pass
                    written += to_write
                    if per_chunk_callback:
                        per_chunk_callback(to_write)
                # ensure pointer back to start next pass
                f.seek(0)
        return True
    except Exception:
        return False


def secure_delete_file(file_path: str, passes: int, progress_callback=None):
    """
    For single-file operations. progress_callback(percent, status_text)
    """
    if not os.path.isfile(file_path):
        return False

    size = os.path.getsize(file_path)
    processed = [0]

    def per_chunk(cbytes):
        processed[0] += cbytes
        percent = (processed[0] / (size * passes)) * 100 if size > 0 else 100
        if progress_callback:
            # status shows pass-level progress roughly
            progress_callback(min(percent, 100.0), f"Wiping {os.path.basename(file_path)}...")

    ok = overwrite_file_stream(file_path, passes, per_chunk)
    try:
        if ok:
            os.remove(file_path)
            return True
    except Exception:
        pass
    return ok


def wipe_folder_recursive(folder_path: str, passes: int, progress_callback=None):
    """
    Overwrite every file in folder_path (recursively) with aggregated progress.
    progress_callback(percent, status_text)
    """
    if not os.path.isdir(folder_path):
        return False

    # build list of files and total bytes
    file_list = []
    total_bytes = 0
    for root, _, files in os.walk(folder_path):
        for fname in files:
            fpath = os.path.join(root, fname)
            try:
                sz = os.path.getsize(fpath)
            except OSError:
                sz = 0
            file_list.append((fpath, sz))
            total_bytes += sz

    # if no data to wipe (zero total bytes), just remove files/folders
    if total_bytes == 0:
        # delete files and directories
        for fpath, _ in file_list:
            try:
                os.remove(fpath)
            except Exception:
                pass
        try:
            # remove directories
            for root, dirs, _ in os.walk(folder_path, topdown=False):
                for d in dirs:
                    try:
                        os.rmdir(os.path.join(root, d))
                    except Exception:
                        pass
            os.rmdir(folder_path)
        except Exception:
            pass
        if progress_callback:
            progress_callback(100.0, "No data to overwrite — folder removed")
        return True

    processed_bytes = [0]  # mutable closure

    def make_per_chunk_cb(fpath):
        # returns a callback that will be passed to overwrite_file_stream
        def per_chunk(cbytes):
            processed_bytes[0] += cbytes
            percent = (processed_bytes[0] / (total_bytes * passes)) * 100
            if progress_callback:
                status = f"Wiping {os.path.basename(fpath)}..."
                progress_callback(min(percent, 100.0), status)
        return per_chunk

    # process each file
    for fpath, fsize in file_list:
        try:
            cb = make_per_chunk_cb(fpath)
            overwrite_file_stream(fpath, passes, cb)
            try:
                os.remove(fpath)
            except Exception:
                pass
        except Exception:
            # skip file on error and continue
            continue

    # try removing empty directories
    try:
        for root, dirs, _ in os.walk(folder_path, topdown=False):
            for d in dirs:
                try:
                    os.rmdir(os.path.join(root, d))
                except Exception:
                    pass
        # finally remove the root folder
        try:
            os.rmdir(folder_path)
        except Exception:
            pass
    except Exception:
        pass

    if progress_callback:
        progress_callback(100.0, "Wipe complete")
    return True
