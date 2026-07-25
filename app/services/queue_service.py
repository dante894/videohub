from queue import Queue
from threading import Thread
from app.core.logger import logger



class QueueService:

    def __init__(self):
        self.queue = Queue()
        self.running = False

    def add(self, item):
        self.queue.put(item)

    def start(self, worker):
        if self.running:
            return

        self.running = True
        print("[QUEUE] Iniciando worker...")
        Thread(
            target=self.run,
            args=(worker,),
            daemon=True
        ).start()

    def run(self, worker):
        print("[QUEUE] Worker iniciado")
        while True:
            item = self.queue.get()
            logger.info("Procesando elemento de la cola: %s", item)

            try:
                worker(item)
            except Exception as e:
                logger.exception("Error procesando elemento de la cola: %s", e)
            finally:
                self.queue.task_done()

    def size(self):
        return self.queue.qsize()