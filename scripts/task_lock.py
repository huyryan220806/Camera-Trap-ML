"""Single-writer lock released by the OS even when Python is killed."""
from contextlib import contextmanager
import os
from pathlib import Path
import re
import uuid

from download_subset import utc_now


def process_alive(pid):
    if pid <= 0:
        raise ValueError('Invalid lock PID; inspect the lock manually')
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
        kernel.CloseHandle.restype = wintypes.BOOL
        handle = kernel.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE
        if not handle:
            error = ctypes.get_last_error()
            if error == 87:  # ERROR_INVALID_PARAMETER: PID no longer exists.
                return False
            raise OSError(error, 'Cannot prove the lock owner has stopped')
        try:
            result = kernel.WaitForSingleObject(handle, 0)
            if result not in (0, 258):
                raise OSError('Cannot determine whether the lock owner has stopped')
            return result == 258
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


@contextmanager
def state_lock(state):
    state = Path(state)
    state.mkdir(parents=True, exist_ok=True)
    # Never unlink the guard: another process may already have this inode open.
    with (state / 'writer.guard').open('a+b') as guard:
        guard.seek(0, os.SEEK_END)
        if guard.tell() == 0:
            guard.write(b'0')
            guard.flush()
        guard.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(guard.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(guard.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise RuntimeError('Another week-2 job is active; wait for it instead of starting a second copy') from exc
        active = state / 'active.lock'
        owns_active = False
        try:
            if active.exists():
                match = re.fullmatch(r'pid=(\d+) started=\S+\s*', active.read_text(encoding='utf-8'))
                if not match:
                    raise ValueError('Unreadable active.lock; inspect it manually, do not remove an unknown lock')
                if process_alive(int(match[1])):
                    raise RuntimeError('The previous lock owner is still running; leave its files untouched')
                archive = active.with_name('active.interrupted-' + uuid.uuid4().hex + '.lock')
                active.rename(archive)
                print('Recovered stopped process; preserved lock: ' + str(archive), flush=True)
            with active.open('x', encoding='utf-8') as f:
                f.write(f'pid={os.getpid()} started={utc_now()}\n')
                f.flush()
                os.fsync(f.fileno())
            owns_active = True
            yield
        finally:
            if owns_active:
                active.unlink(missing_ok=True)
            guard.seek(0)
            if os.name == 'nt':
                msvcrt.locking(guard.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(guard.fileno(), fcntl.LOCK_UN)
