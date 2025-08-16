from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import Callable


class ScrapeScheduler:
    def __init__(self) -> None:
        self.scheduler = BackgroundScheduler()

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()

    def add_job(self, func: Callable, cron: str = "*/30 * * * *") -> None:
        minute, hour, day, month, dow = cron.split()
        self.scheduler.add_job(func, CronTrigger(minute=minute, hour=hour, day=day, month=month, day_of_week=dow))

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown()


scheduler = ScrapeScheduler()