import asyncio
import heapq
import time


class ScheduledTask:
    def __init__(self, run_at, coro):
        self.run_at = run_at
        self.coro = coro

    def __lt__(self, other):
        return self.run_at < other.run_at


class AsyncScheduler:
    def __init__(self, timedelay=5, log=False):
        self.tasks = []
        self._started = False
        self.timedelay = timedelay
        self.log = log

    def schedule(self, delay_seconds, coro_func):
        run_at = time.time() + delay_seconds
        heapq.heappush(self.tasks, ScheduledTask(run_at, coro_func))

    async def _run_loop(self):
        while True:
            if not self.tasks:
                await asyncio.sleep(self.timedelay)
                continue

            now = time.time()
            next_task = self.tasks[0]

            if next_task.run_at <= now:
                task = heapq.heappop(self.tasks)
                if self.log:
                    print(f"Scheduler POP: {task.coro} at {task.run_at}")
                await task.coro()
            else:
                await asyncio.sleep(min(self.timedelay, next_task.run_at - now))

    def start(self):
        if not self._started:
            asyncio.create_task(self._run_loop())
            if self.log:
                print(f"asyncio task created: _run_loop()")
            self._started = True
            print(f"Scheduler.start completed")
        else:
            print(f"WARNING: Scheduler.start called while already running")
