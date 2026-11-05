from enum import Enum
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import threading


class DependencyError(ValueError):
    pass


class DependencyScheduler:
    """
    An execution engine which coordinates and runs tasks based on a directed dependancy graph.
    """

    class Status(Enum):
        Done = "Done"
        Failed = "Failed"
        Pending = "Pending"

    def __init__(self, max_workers: int):
        if max_workers < 1:
            raise ValueError("max_workers must be at least 1")
        self.max_workers = max_workers
        self.task_ids = {}
        self._lock = threading.RLock()
        self._shutdown = False
        self._has_run = False
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.results = {}

    def add_task(self, task_id, fn: Callable, depends_on: list | None = None, *args, **kwargs):
        with self._lock:
            if self._shutdown:
                raise RuntimeError("Scheduler has been shutdown")
            if self._has_run:
                raise RuntimeError("Cannot add tasks after run()")
            if task_id in self.task_ids:
                raise ValueError(f"Task with id {task_id} exists")
            if depends_on is None:
                dependencies = []
            else:
                dependencies = list(depends_on)

            if "args" in kwargs:
                if args:
                    raise TypeError("Do not combine positional arguments with args=[...]")
                supplied_args = kwargs.pop("args")
                if not isinstance(supplied_args, (list, tuple)):
                    raise TypeError("args must be a list or tuple")
                args = tuple(supplied_args)

            self.task_ids[task_id] = {
                "fn": fn,
                "args": args,
                "kwargs": kwargs,
                "depends_on": dependencies,
                "status": self.Status.Pending,
            }

    def run(self):
        # check for missing dependencies
        # breakpoint()
        tasks = list(self.task_ids.keys())
        for k, v in self.task_ids.items():
            # check for missing dependencies
            if dependencies := v["depends_on"]:
                if not all(i in tasks for i in dependencies):
                    raise ValueError(f"task {k} has missing dependancy(s)")

        # globally track  visited nodes
        visited = set()
        EXIT = "exit"
        ENTER = "enter"

        def dfs(fringe, explored: set):
            # TODO: Refactor DFS to eliminate recursion.
            #
            # Although this implementation uses an explicit stack (fringe) to track
            # traversal events, it still recursively calls dfs() to process each event.
            #
            # Python has a limited recursion depth (typically around 1,000 calls).
            # Large dependency graphs could therefore raise RecursionError, even
            # when the graph contains no cycles.
            #
            # Refactor to use an iterative loop that processes fringe until empty.
            # This will eliminate call-stack growth and make the algorithm suitable
            # for larger dependency graphs.
            #
            # Target complexity:
            # Time:  O(V + E), where V = tasks and E = dependencies.
            # Space: O(V + E) for traversal state and pending events.
            #
            # DEFERRED: Complete functional correctness tests before refactoring.
            if len(fringe) == 0:
                return False
            node = fringe.pop()

            node_state = node[1]

            if node_state == ENTER:
                # check if there is a cycle in node dependencies
                # breakpoint()
                if node[0] in visited:
                    return dfs(fringe=fringe, explored=explored)
                fringe.append((node[0], EXIT))
                explored.add(node[0])
                dependencies = self.task_ids[node[0]]["depends_on"]

                if any(t in dependencies for t in explored):
                    return True
                for i in dependencies:
                    if i not in visited:
                        fringe.append((i, ENTER))
            else:
                explored.remove(node[0])
                # add to visited only when a node has been fully explored otherwise if added
                # while still active, it will not be added, as part of dependencies, to the fringe
                # , thus a cycle will be missed if present
                visited.add(node[0])
            return dfs(fringe=fringe, explored=explored)

        for task in tasks:
            fringe = [(task, ENTER)]
            explored = set()
            if task not in visited:
                if dfs(fringe, explored=explored):
                    raise DependencyError("Circular dependency detected")

        # run functions
        def execute(task_id):
            task = self.task_ids[task_id]
            for t in task["depends_on"]:
                status = task["status"]
                if status == self.Status.Pending:
                    raise RuntimeError("Task dependency failed")
                elif status == self.Status.Failed:
                    break
            future = self.executor.submit(task["fn"], *task["args"], **task["kwargs"])
            task["status"] = self.Status.Done
            return future.result()

        for t in tasks:
            self.results[t] = execute(t)

        self._has_run = True

    def cancel(self, task_id=None):
        if task_id is None:
            self._shutdown = True
        if self.task_ids.get(task_id, None):
            # check if task has been run, if not stop task with its dependencies
            task = self.task_ids[task_id]
            for t in [task_id, *task["depends_on"]]:
                self.task_ids.pop(t)

    def shutdown(self):
        pass
