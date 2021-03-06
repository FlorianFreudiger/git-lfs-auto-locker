import logging
import time
import argparse

from git import lfs_lock
from git import git_repository
from notification.windows_toast import WindowsToast
from stop_condition.stop_after_program_exit import StopAfterProgramExit

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO, filename="git_lfs_auto_locker.log")
logging.info("Starting GitLFS Auto-Locker")

argument_parser = argparse.ArgumentParser(description="Synchronize lfs locks to modified file list")
argument_parser.add_argument("-C", metavar="<path>",
                             help="Path to git repository instead of using current directory")
argument_parser.add_argument("-u", "--user-name", metavar="<username>",
                             help="Use custom name for comparison to lfs locks author names instead of name from git config")
argument_parser.add_argument("-s", "--stop-after", metavar="<program name>",
                             help="Stop if program name is not found in list of running processes")
argument_parser.add_argument("-lun", "--lock-untracked", action="store_true",
                             help="Lock untracked files, if not supplied untracked files will be unlocked")
arguments = argument_parser.parse_args()
logging.debug("Parsed argparse namespace: %s", arguments)

GitRepositoryPath = arguments.C
GitLfsLockName = arguments.user_name
StopConditions = []
if arguments.stop_after:
    StopConditions.append(StopAfterProgramExit(arguments.stop_after))
LockUntracked = arguments.lock_untracked

#### CONFIG #### #TODO: Config file
# Interval in seconds in which this script compares git status with git lfs locks
refreshDelay = 30

# Every n-th cycle call a "real" lfs locks lookup, otherwise cached lookup will be used. Set to 1 to always refresh from server.
# If a mismatch between locked and modified files is detected on a cached locks lookup, a real lookup always will be made to confirm this.
LfsCachedLocksRefresh = 10

# Whether to only show the file name or the relative git repository path which can be rather long (maybe a bit too long for a win10 toast)
Notification_OnlyShowFilename = True

# Show "Locked/Unlocked x files notification"
Notification_ShowLockAndUnlock = False
#### END OF CONFIG ####

git_repo = git_repository.GitRepository(GitRepositoryPath)
if not git_repo.is_in_work_tree():
    raise RuntimeError("Not inside work tree of a git repo, move script or set path to inside work tree")
if GitLfsLockName is None:
    GitLfsLockName = git_repo.get_config_user_name()

notificator = WindowsToast()

blockNotification_paths_showed = set()
cycle_index = 1
while True:
    if cycle_index >= LfsCachedLocksRefresh:
        cached = False
        cycle_index = 1
    else:
        cached = True
        cycle_index += 1
    logging.debug("Checking git status and git lfs locks. Cached lfs check = %s", cached)

    git_repo.refresh_status(include_untracked_files=LockUntracked)
    git_repo.refresh_lfs_locks(cached=cached)

    gitStatusFiles_Set = set(git_repo.status_files)

    gitOwnLfsLocks = git_repo.get_lfs_locks_own(GitLfsLockName)
    gitOtherLfsLocks = git_repo.get_lfs_locks_other(GitLfsLockName)

    gitOwnLfsLocks_PathSet = set(lfs_lock.LfsLock.lock_list_to_path_list(gitOwnLfsLocks))
    gitOtherLfsLocks_PathSet = set(lfs_lock.LfsLock.lock_list_to_path_list(gitOtherLfsLocks))

    blockingLocks = gitStatusFiles_Set & gitOtherLfsLocks_PathSet - blockNotification_paths_showed
    missingLocks = gitStatusFiles_Set - gitOwnLfsLocks_PathSet - gitOtherLfsLocks_PathSet
    unnecessaryLocks = gitOwnLfsLocks_PathSet - gitStatusFiles_Set

    if cached and (blockingLocks or missingLocks or unnecessaryLocks):
        logging.debug("Detected mismatch but used cached lfs locks, confirming by rerunning with real lookup..")
        cycle_index = LfsCachedLocksRefresh
        continue

    if blockingLocks:
        logging.info("File(s) that were locked by other people were modified: %s", blockingLocks)
        notificator.show_warning("You are modifying {} file(s) that were locked by other people!".format(len(blockingLocks))) #TODO: Show file(s)
        blockNotification_paths_showed = blockNotification_paths_showed | blockingLocks

    if missingLocks:
        logging.debug("Modified files that are not locked: %s", missingLocks)
        for missingLock in missingLocks:
            logging.info("Locking %s", missingLock)
            git_repo.lock_file(missingLock)
        if Notification_ShowLockAndUnlock:
            notificator.show_info("Locked {} modified file(s)".format(len(missingLocks)))

    if unnecessaryLocks:
        logging.debug("Locked files without modification: %s", unnecessaryLocks)
        for unnecessaryLock in unnecessaryLocks:
            logging.info("Unlocking %s", unnecessaryLock)
            git_repo.unlock_file(unnecessaryLock)
        if Notification_ShowLockAndUnlock:
            notificator.show_info("Unlocked {} unmodified file(s)".format(len(unnecessaryLocks)))

    should_stop_bool = False
    for stop_condition in StopConditions:
        if stop_condition.should_stop():
            logging.debug("Stopping because of %s", stop_condition)
            should_stop_bool = True
            break
    if should_stop_bool:
        break

    logging.debug("Sleeping for %s seconds", refreshDelay)
    time.sleep(refreshDelay)

logging.debug("Exiting GitLFS Auto-Locker")
