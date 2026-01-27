from app.api.functions import store_temperature, power_on, shutdown

def register_jobs(scheduler):
  scheduler.add_job(
    id = "temperature_history_csv",
    func = store_temperature,
    trigger = "interval",
    minutes=2,
    max_instances = 1,
    replace_existing=True
  )
  scheduler.add_job(
    id = "power_on",
    func = power_on,
    trigger = "cron",
    minute='0',
    hour='5',
    day_of_week='0', # APScheduler starts week on Monday
     max_instances = 1,
    replace_existing=True
  )
  scheduler.add_job(
    id = "shutdown",
    func = shutdown,
    trigger = "cron",
    minute='0',
    hour='21',
    day_of_week='4', # APScheduler starts week on Monday
     max_instances = 1,
    replace_existing=True
  )
