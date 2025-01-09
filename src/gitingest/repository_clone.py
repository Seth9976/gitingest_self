""" This module contains functions for cloning a Git repository to a local path. """

import asyncio
from dataclasses import dataclass
from typing import Callable, Optional

from gitingest.utils import async_timeout
from config import CLONE_TIMEOUT


@dataclass
class CloneProgress:
    """克隆进度信息"""
    phase: str
    current: int = 0
    total: int = 0
    message: str = ""


@dataclass
class CloneConfig:
    """
    Configuration for cloning a Git repository.

    This class holds the necessary parameters for cloning a repository to a local path, including
    the repository's URL, the target local path, and optional parameters for a specific commit or branch.

    Attributes
    ----------
    url : str
        The URL of the Git repository to clone.
    local_path : str
        The local directory where the repository will be cloned.
    commit : str | None, optional
        The specific commit hash to check out after cloning (default is None).
    branch : str | None, optional
        The branch to clone (default is None).
    progress_callback : Callable[[CloneProgress], None] | None, optional
        The callback function to update the progress of the cloning process.
    """

    url: str
    local_path: str
    commit: Optional[str] = None
    branch: Optional[str] = None
    progress_callback: Optional[Callable[[CloneProgress], None]] = None


@async_timeout(CLONE_TIMEOUT)
async def clone_repo(config: CloneConfig) -> tuple[bytes, bytes]:
    """
    Clones a repository to a local path based on the provided configuration.

    This function handles the process of cloning a Git repository to the local file system.
    It can clone a specific branch or commit if provided, and it raises exceptions if
    any errors occur during the cloning process.

    Parameters
    ----------
    config : CloneConfig
        A dictionary containing the following keys:
            - url (str): The URL of the repository.
            - local_path (str): The local path to clone the repository to.
            - commit (Optional[str]): The specific commit hash to checkout.
            - branch (Optional[str]): The branch to clone. Defaults to 'main' or 'master' if not provided.

    Returns
    -------
    tuple[bytes, bytes]
        A tuple containing the stdout and stderr of the git commands executed.

    Raises
    ------
    ValueError
        If the 'url' or 'local_path' parameters are missing, or if the repository is not found.
    """
    # Extract and validate query parameters
    url: str = config.url
    local_path: str = config.local_path
    commit: str | None = config.commit
    branch: str | None = config.branch

    if not url:
        raise ValueError("The 'url' parameter is required.")

    if not local_path:
        raise ValueError("The 'local_path' parameter is required.")

    # Check if the repository exists
    if not await _check_repo_exists(url):
        raise ValueError("Repository not found, make sure it is public")

    if commit:
        # Scenario 1: Clone and checkout a specific commit
        # Clone the repository without depth to ensure full history for checkout
        clone_cmd = ["git", "clone", "--single-branch", url, local_path]
        await _run_git_command(*clone_cmd, config=config)

        # Checkout the specific commit
        checkout_cmd = ["git", "-C", local_path, "checkout", commit]
        return await _run_git_command(*checkout_cmd, config=config)

    if branch and branch.lower() not in ("main", "master"):

        # Scenario 2: Clone a specific branch with shallow depth
        clone_cmd = ["git", "clone", "--depth=1", "--single-branch", "--branch", branch, url, local_path]
        return await _run_git_command(*clone_cmd, config=config)

    # Scenario 3: Clone the default branch with shallow depth
    clone_cmd = ["git", "clone", "--depth=1", "--single-branch", url, local_path]
    return await _run_git_command(*clone_cmd, config=config)


async def _check_repo_exists(url: str) -> bool:
    """
    Check if a repository exists at the given URL using an HTTP HEAD request.

    Parameters
    ----------
    url : str
        The URL of the repository.

    Returns
    -------
    bool
        True if the repository exists, False otherwise.
    """
    proc = await asyncio.create_subprocess_exec(
        "curl",
        "-I",
        url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    if proc.returncode != 0:
        return False
    # Check if stdout contains "404" status code
    stdout_str = stdout.decode()
    return "HTTP/1.1 404" not in stdout_str and "HTTP/2 404" not in stdout_str


async def _run_git_command(*args: str, config: CloneConfig) -> tuple[bytes, bytes]:
    """
    Executes a git command asynchronously and captures its output.

    Parameters
    ----------
    *args : str
        The git command and its arguments to execute.

    Returns
    -------
    tuple[bytes, bytes]
        A tuple containing the stdout and stderr of the git command.

    Raises
    ------
    RuntimeError
        If the git command exits with a non-zero status.
    """
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    
    if config.progress_callback:
        progress = CloneProgress(phase="克隆中")
        while True:
            if proc.stderr:
                line = await proc.stderr.readline()
                if not line:
                    break
                    
                line_str = line.decode().strip()
                if "Receiving objects:" in line_str:
                    try:
                        # 解析类似 "Receiving objects:  67% (910/1363)"
                        percent = int(line_str.split("%")[0].split(":")[-1].strip())
                        current, total = map(int, line_str.split("(")[-1].strip(")").split("/"))
                        progress.current = current
                        progress.total = total
                        progress.message = f"接收对象: {percent}%"
                        config.progress_callback(progress)
                    except (ValueError, IndexError):
                        pass
                        
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        error_message = stderr.decode().strip()
        raise RuntimeError(f"Git命令失败: {' '.join(args)}\n错误: {error_message}")

    return stdout, stderr
