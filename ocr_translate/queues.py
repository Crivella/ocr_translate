import os

from .messaging import WorkerMessageQueue

num_main_workers = int(os.environ.get('NUM_MAIN_WORKERS', 4))
num_box_workers = int(os.environ.get('NUM_BOX_WORKERS', 1))
num_ocr_workers = int(os.environ.get('NUM_OCR_WORKERS', 1))
num_tsl_workers = int(os.environ.get('NUM_TSL_WORKERS', 1))

main_queue = WorkerMessageQueue(num_workers=num_main_workers)
box_queue = WorkerMessageQueue(num_workers=num_box_workers)
ocr_queue = WorkerMessageQueue(num_workers=num_ocr_workers)
tsl_queue = WorkerMessageQueue(
    num_workers=num_tsl_workers,
    allow_batching=True,
    # batch_timeout=15,
    batch_args= (0,)
    )

main_queue.start_workers()
box_queue.start_workers()
ocr_queue.start_workers()
tsl_queue.start_workers()

