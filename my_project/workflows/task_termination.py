# from flytekit import task, workflow
# import signal
# import time

# def handle_termination(signum, frame):
#     print("Task is being terminated. Cleaning up...")
#     # Perform any cleanup actions here
#     exit(0)

# # Register the signal handler
# signal.signal(signal.SIGTERM, handle_termination)

# @task
# def long_running_task():
#     try:
#         while True:
#             print("Task is running...")
#             time.sleep(1)
#     except KeyboardInterrupt:
#         print("Task interrupted by user.")

# @workflow
# def termination_workflow():
#     long_running_task()
