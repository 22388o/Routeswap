from threading import Thread
from dotenv import load_dotenv
from os import environ

# Loads the variables of environments in the .env file
# of the current directory.
load_dotenv(environ.get("ENV_PATH", ".env"))

from services import lnd
import api

def start():
    threads = []

    thread = Thread(target=api.start)
    thread.start()
    threads.append(thread)

    thread = Thread(target=lnd.start)
    thread.start()
    threads.append(thread)
    
    for t in threads:
        t.join()
    
if __name__ == "__main__":
    start()