# -*- mode: python; indent-tabs-mode: nil; python-indent-level: 4 -*-
# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python

import os
from concurrent.futures import ThreadPoolExecutor, as_completed


def get_max_workers():
    """Determine the number of workers based on available CPUs.

    Returns half the CPU count, matching the Perl fork-based approach.
    Minimum of 1 worker.
    """
    cpus = os.cpu_count() or 2
    return max(1, cpus // 2)


def run_parallel_jobs(jobs, worker_fn, max_workers=None):
    """Execute jobs in parallel using a thread pool.

    Replaces the Perl fork-based pattern where child processes are
    forked up to max_forked_jobs at a time.

    Args:
        jobs: iterable of job arguments (each passed to worker_fn)
        worker_fn: callable that processes a single job
        max_workers: number of parallel workers (default: half CPU count)

    Returns:
        list of (job, result) tuples in completion order
    """
    if max_workers is None:
        max_workers = get_max_workers()

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_job = {executor.submit(worker_fn, job): job for job in jobs}
        for future in as_completed(future_to_job):
            job = future_to_job[future]
            try:
                result = future.result()
                results.append((job, result))
            except Exception as exc:
                results.append((job, exc))

    return results
