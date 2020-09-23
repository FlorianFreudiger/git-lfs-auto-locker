import json
import logging
import subprocess
from typing import List

from git import lfs_lock


class GitRepository:  # TODO Verify that we are indeed in a git repo (git rev-parse --is-inside-work-tree or maybe find root via --git-dir)
    def __init__(self, path: str = ""):
        self.path = path
        self.status_files = []
        self.lfs_locks = []

    def _run_command(self, arguments: List[str], strip_output: bool = True) -> str:
        git_command = ['git']
        if self.path is not None and self.path != "":
            git_command.append('-C')
            git_command.append(self.path)
        git_command.extend(arguments)

        git_process = subprocess.run(git_command, stdout=subprocess.PIPE, check=True)
        output = git_process.stdout.decode('utf-8')
        if strip_output:
            output = output.strip()

        logging.debug("%s -> %s", git_command, output)
        return output

    def refresh_status(self) -> None:
        """Refresh status of git repository via "git status", results will be saved to status_files"""
        output = self._run_command(['status', '--porcelain=1'])

        lines = output.splitlines()
        self.status_files = []
        for line in lines:
            self.status_files.append(line.split(maxsplit=1)[1])

    def refresh_lfs_locks(self, cached: bool) -> None: # TODO: Process Server errors
        # While we could cache it ourselves, reducing process calls
        # using the cached flag has the benefit of potentially returning results of a more recent lookup another software made.
        git_lfs_locks_output = self._run_command(['lfs', 'locks', '--json', '--cached'] if cached else
                                                 ['lfs', 'locks', '--json'], strip_output=False)
        git_lfs_locks_json = json.loads(git_lfs_locks_output)

        self.lfs_locks = []
        for lock_dict in git_lfs_locks_json:
            self.lfs_locks.append(lfs_lock.LfsLock.from_dict(lock_dict))

    def get_lfs_locks_own(self, username: str) -> List[lfs_lock.LfsLock]:
        own_locks = []
        for lock in self.lfs_locks:
            if lock.owner == username:
                own_locks.append(lock)
        return own_locks

    def get_lfs_locks_other(self, username: str) -> List[lfs_lock.LfsLock]:
        other_locks = []
        for lock in self.lfs_locks:
            if lock.owner != username:
                other_locks.append(lock)
        return other_locks

    def lock_file(self, lock: str) -> None:  # TODO: Check json output if successful
        output = self._run_command(['lfs', 'lock', lock])
        logging.debug("Locking path %s output: %s", lock, output)

    def unlock_file(self, lock: str) -> None:
        output = self._run_command(['lfs', 'unlock', lock])
        logging.debug("Unlocking path %s output: %s", lock, output)
