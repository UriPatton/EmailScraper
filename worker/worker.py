# worker.py
import os
from rq import Worker, Queue
from redis import Redis

# Step 1: Define Job Functions
# Assume job functions are defined in a separate module, e.g., `tasks.py`

# Step 2: Setup Redis Connection
redis_conn = Redis(host='redis', port=6379, db=0)  # Adjust connection parameters as needed

# Step 3: Create Worker Instance
# Assuming there's a default queue jobs are submitted to
queue_names = ['default']  # List of queue names to listen to
queues = [Queue(name, connection=redis_conn) for name in queue_names]

# Step 4: Start Worker
if __name__ == '__main__':
    worker = Worker(queues=queues, connection=redis_conn)
    worker.work()
