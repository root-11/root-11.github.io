import math
import random
from collections import defaultdict
from itertools import count
from datetime import datetime, date, timedelta
from datetime import time as daytime

td, dt = timedelta, datetime


def _str(v):
    return v.isoformat() if isinstance(v, (datetime, date)) else v


class Job(object):
    ids = count()

    def __init__(self, available, deadline, size, _id=None):
        self.id = next(self.ids) if _id is None else _id
        if not size > 0:
            raise ValueError
        if not available < deadline:
            raise ValueError
        if not deadline - available >= size:
            raise ValueError

        self.available = available  # earliest start
        self.deadline = deadline  # latest finish
        self.size = size  # time to complete the job
        self.start = None  # scheduled start
        self.end = None  # scheduled finish
        self.bins = []  # candidate bins
        self.bin = None  # assigned bin (open, close) time
        self.processor = None  # assigned processor.

    @property
    def begin(self):
        return self.bin[0]

    @property
    def end(self):
        return self.bin[1]

    @property
    def window(self):
        return min(self.end, self.deadline) - max(self.begin, self.available)

    def copy(self):
        job = Job(self.available, self.deadline, self.size)
        job.bins = self.bins[:] if self.bins else []
        return job

    def __str__(self) -> str:
        a = self.id
        b = _str(self.available)
        c = _str(self.start)
        d = _str(self.size)
        e = _str(self.end)
        f = _str(self.deadline)
        return f"{a} {b} {c} {d} {e} {f}"


def bin_packing(jobs, bins):
    """bin packing of jobs to level the workload across available bins"""
    assert all(isinstance(i, Job) for i in jobs)
    jobs = [j.copy() for j in jobs]

    workload = defaultdict(float)
    for job in jobs:
        for bin in bins:
            begin, end = bin
            if end <= job.available or begin > job.deadline:
                continue
            job.bins.append((begin, end))

        default_assignment = job.bins[0]
        workload[default_assignment] += job.size

    peak_workload = max(workload.values())
    score = sum(peak_workload - day for day in workload.values())

    # sort by biggest job with fewest options
    jobs.sort(key=lambda job: (job.size, -len(job.bins)), reverse=True)

    workload.clear()
    for job in jobs:
        L = [(workload[bin], bin) for bin in job.bins]
        L.sort()
        job.bin = L[0][1]
        workload[job.bin] += job.size

    peak_workload = max(workload.values())
    score2 = sum(peak_workload - day for day in workload.values())

    assert math.isclose(sum(workload.values()), sum(j.size for j in jobs))
    print(f"peak workload dropped from {score} to {score2}")
    return jobs


def is_valid(sequence):
    """helper: verifies a sequence"""
    assert all(isinstance(i, Job) for i in sequence)
    begin = None
    for item in sequence:
        assert isinstance(item, Job)
        start = item.available if begin is None else max(begin, item.available)
        end = start + item.size
        if start > item.available:
            return False
        if end > item.deadline:
            return False
    return True


def schedule(jobs):
    processors_required = math.ceil(sum(j.size / (j.end - j.begin) for j in jobs))
    jobs = [j.copy() for j in jobs]
    jobs.sort(key=lambda job: (job.window, job.size))  # smallest window, biggest task
    # simple distributed assignment:
    job_queues = {i: [] for i in range(processors_required)}
    for i, job in enumerate(jobs):
        job_queues[i % processors_required].append(job)

    schedules = []
    for processor, job_queue in job_queues.items():
        plan = single_processor_schedule(job_queue)
        for job in plan:
            assert isinstance(job, Job)
            job.processor = processor
            schedules.append(job)
    schedules.sort(key=lambda job: (job.processor, job.start))
    return schedules


def single_processor_schedule(jobs):
    jobs = [j.copy() for j in jobs]
    jobs.sort(key=lambda job: (job.window, job.size))  # smallest window, biggest task

    job_queue = [([0], 0)]
    while job_queue:
        seq, order_index = job_queue.pop()

        if len(seq) == len(jobs):
            if is_valid([jobs[ix] for ix in seq]):
                break
            else:
                continue
        new_order_index = order_index + 1

        end, start = None, None
        for ix in seq + [order_index]:
            job = jobs[ix]
            assert isinstance(job, Job)
            start = min(job.available, start) if start is not None else job.available
            end = max(job.deadline, end) if end is not None else end

        for i in range(len(seq) + 1):
            new_seq = seq[:]  # shallow copy
            new_seq.insert(i, new_order_index)

            if is_valid([jobs[ix] for ix in seq]):
                job_queue.append((new_seq, new_order_index))
            else:
                pass
    if not len(seq) == len(jobs):
        raise ValueError("No valid schedule found")


def schedule_old(jobs):
    """creates a schedule"""

    jobs = [j.copy() for j in jobs]
    jobs.sort(key=lambda job: (job.window, job.size))  # smallest window, biggest task

    job_queue = [([0], 0)]
    while job_queue:
        seq, order_index = job_queue.pop()

        if len(seq) == len(jobs):
            if is_valid([jobs[ix] for ix in seq]):
                break
            else:
                continue
        new_order_index = order_index + 1

        end, start = None, None
        for ix in seq + [order_index]:
            job = jobs[ix]
            assert isinstance(job, Job)
            start = min(job.available, start) if start is not None else job.available
            end = max(job.deadline, end) if end is not None else end

        for i in range(len(seq) + 1):
            new_seq = seq[:]  # shallow copy
            new_seq.insert(i, new_order_index)

            if is_valid([jobs[ix] for ix in seq]):
                job_queue.append((new_seq, new_order_index))
            else:
                pass
    if not len(seq) == len(jobs):
        raise ValueError("No valid schedule found")

    # Create the final schedule
    schedule = []
    begin = None
    for index in seq:
        original_job = jobs[index]
        assert isinstance(original_job, Job)
        job = original_job.copy()
        job.start = job.available if begin is None else max(job.available, begin)
        job.end = job.start + job.size
        begin = job.end
        schedule.append(job)
    return schedule


def test():
    n_jobs = 200

    workday_start, workday_end = daytime(9), daytime(17)
    starts, ends = dt(2000, 1, 1), dt(2000, 1, 10)
    duration = (ends - starts).days
    time_window = int((ends - starts).total_seconds())

    day_bins = []
    for n in range(duration):
        begin = starts + td(days=n) + td(workday_start.hour)
        ends = starts + td(days=n) + td(workday_end)
        day_bins.append([begin, ends])

    jobs = []
    while len(jobs) < n_jobs:
        A = td(seconds=random.randint(0, time_window))
        B = td(seconds=random.randint(0, time_window))
        A, B = min(A, B), max(A, B)
        job = Job(available=starts + A, deadline=starts + B, size=random.random() * B - A)

        jobs.append(job)

    binned_jobs = bin_packing(jobs, day_bins)

    bins = defaultdict(list)
    for job in binned_jobs:
        bins[job.bin].append(job)
    schedules = []
    for bin, jobs in bins.items():
        plan = schedule(bin)
        schedules.extend(plan)
