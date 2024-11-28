from apscheduler.schedulers.tornado import TornadoScheduler

from core.utils.singleton import Singleton


class Scheduler(Singleton):
    def __init__(self):
        self._scheduler = TornadoScheduler()

    def add_task(self, task_func, trigger="cron", *args, **kwargs):
        """添加任务"""
        self._scheduler.add_job(task_func, trigger=trigger, *args, **kwargs)

    def start(self):
        """开启调度器"""
        return self._scheduler.start()

    def stop(self):
        """停止调度器"""
        return self._scheduler.shutdown()
