import multiprocessing
from time import sleep

from typing import List

from conf import create_logger
from bde_parser import kolesa

logger = create_logger('main')


WORKERS = 2
process_queue: List[multiprocessing.Process] = []
logger.info("Start program for scraping Kolesa.kz")
for brand in kolesa.brands:
    logger.debug(f"Create process for {brand}")
    p = multiprocessing.Process(
        name=brand,
        target=kolesa.start_sraping,
        args=(brand,)
    )
    process_queue.append(p)
        

active_process: List[multiprocessing.Process] = []
while len(process_queue):
    for ap in active_process:
        if not ap.is_alive():
            ap.terminate()
            active_process.remove(ap)
            sleep(180)

    for p in process_queue:
        if len(active_process) < WORKERS:
            p.start()
            active_process.append(p)
            process_queue.remove(p)
            sleep(60)