import threading 
import time

def ThreadsExemplo(parametro):
    time.sleep(10)
    thread = threading.Thread(target=ThreadsExemplo, args=(parametro,))
    thread.start()
    