# # from flytekit import task, workflow, dynamic, conditional
# # from typing import List
# # import subprocess
# # import sys
# # from datetime import timedelta

# # try:
# #     from minio import Minio
# # except ImportError:
# #     print("Minio module not found. Installing...")
# #     subprocess.check_call([sys.executable, "-m", "pip", "install", "minio"])
# #     from minio import Minio

# # from minio.commonconfig import CopySource
# # from minio.error import S3Error

# # # Initialize MinIO client
# # client = Minio(
# #     endpoint="host.docker.internal:9000",  # Use the service name in Docker
# #     access_key="minioadmin",
# #     secret_key="minioadmin",
# #     secure=False
# # )

# # # Specify the bucket name and folders
# # bucket_name = "flyte-project"
# # backup_folder = "backup"

# # @task(container_image="sanskruti557/my-flyte-workflow:latest", retries=2, timeout=timedelta(minutes=5))
# # def list_files_task(source_folder: str) -> List[str]:
# #     print(f"Listing files in source folder: {source_folder}")
# #     files_to_update = []

# #     # List files in the current source folder
# #     source_objects = client.list_objects(bucket_name, prefix=source_folder, recursive=True)

# #     if client.bucket_exists(bucket_name):
# #         print(f"Bucket '{bucket_name}' exists.")
# #     else:
# #         print(f"Bucket '{bucket_name}' does not exist.")
# #         return files_to_update  # Return empty list if the bucket isn't accessible

# #     for source_obj in source_objects:
# #         source_file = source_obj.object_name
# #         destination_file = source_file.replace(source_folder, backup_folder, 1)

# #         try:
# #             # Check if the file already exists in backup
# #             dest_obj = client.stat_object(bucket_name, destination_file)

# #             # Add to list if the source file is newer
# #             if source_obj.last_modified > dest_obj.last_modified:
# #                 files_to_update.append(source_file)
# #         except S3Error as e:
# #             # If the file does not exist in backup, add it to the list
# #             if e.code == "NoSuchKey":
# #                 files_to_update.append(source_file)

# #     return files_to_update

# # @task(container_image="sanskruti557/my-flyte-workflow:latest", retries=2, timeout=timedelta(minutes=5))
# # def evaluate_condition(files_to_update: List[str]) -> bool:
# #     # Example condition: check if there are any files to update
# #     return len(files_to_update) > 0

# # @task(container_image="sanskruti557/my-flyte-workflow:latest", retries=2, timeout=timedelta(minutes=5))
# # def copy_files_task(files_to_update: List[str], source_folder: str):
# #     try:
# #         for source_file in files_to_update:
# #             destination_file = source_file.replace(source_folder, backup_folder, 1)
# #             client.copy_object(
# #                 bucket_name,
# #                 destination_file,
# #                 CopySource(bucket_name, source_file)
# #             )
# #             print(f"File '{source_file}' copied to '{destination_file}'.")
# #     except Exception as e:
# #         print(f"Error during file copy: {e}")
# #         raise

# # @task(container_image="sanskruti557/my-flyte-workflow:latest")
# # def noop_task():
# #     print("No operation task executed.")

# # @dynamic(container_image="sanskruti557/my-flyte-workflow:latest")
# # def dynamic_copy_files_workflow(source_folders: List[str]):
# #     for source_folder in source_folders:
# #         files_to_update = list_files_task(source_folder=source_folder)
# #         condition = evaluate_condition(files_to_update=files_to_update)
        
# #         # Use a workflow to handle the conditional logic
# #         conditional_copy_files_workflow(source_folder, files_to_update, condition)

# # @workflow
# # def conditional_copy_files_workflow(source_folder: str, files_to_update: List[str], condition: bool):
# #     return (
# #         conditional("conditional_copy")
# #         .if_(condition.is_true())
# #         .then(copy_files_task(files_to_update=files_to_update, source_folder=source_folder))
# #         .else_()
# #         .then(noop_task())
# #     )

# # @workflow
# # def copy_files_workflow(source_folders: List[str]):
# #     dynamic_copy_files_workflow(source_folders=source_folders)

# # from flytekit import task, workflow, dynamic, LaunchPlan, WorkflowExecutionPhase, conditional
# # from flytekit.core.notification import Email
# # from typing import List
# # import subprocess
# # import sys
# # from datetime import timedelta

# # try:
# #     from minio import Minio
# # except ImportError:
# #     print("Minio module not found. Installing...")
# #     subprocess.check_call([sys.executable, "-m", "pip", "install", "minio"])


# # from minio import Minio
# # from minio.commonconfig import CopySource
# # from minio.error import S3Error

# # # Initialize MinIO client
# # client = Minio(
# #     endpoint="host.docker.internal:9000",  # Use the service name in Docker
# #     access_key="minioadmin",
# #     secret_key="minioadmin",
# #     secure=False
# # )

# # # Specify the bucket name and folders
# # bucket_name = "flyte-project"
# # backup_folder = "backup"


# # @task(container_image="sanskruti557/my-flyte-workflow:latest", retries=2, timeout=timedelta(minutes=5))
# # def list_files_task(source_folder: str) -> List[str]:
# #     """List files that need to be updated in the backup."""
# #     files_to_update = []
# #     print(f"Listing files in source folder: {source_folder}")

# #     try:
# #         # List files in the current source folder
# #         source_objects = client.list_objects(bucket_name, prefix=source_folder, recursive=True)

# #         # Check if the bucket exists
# #         if client.bucket_exists(bucket_name):
# #             print(f"Bucket '{bucket_name}' exists.")
# #         else:
# #             print(f"Bucket '{bucket_name}' does not exist.")
# #             return files_to_update  # Return empty list if the bucket isn't accessible

# #         # Iterate over objects and check if they need to be updated
# #         for source_obj in source_objects:
# #             source_file = source_obj.object_name
# #             destination_file = source_file.replace(source_folder, backup_folder, 1)
# #             try:
# #                 # Check if the file already exists in the backup
# #                 dest_obj = client.stat_object(bucket_name, destination_file)
# #                 # Add to list if the source file is newer
# #                 if source_obj.last_modified > dest_obj.last_modified:
# #                     files_to_update.append(source_file)
# #             except S3Error as e:
# #                 # If the file does not exist in backup, add it to the list
# #                 if e.code == "NoSuchKey":
# #                     files_to_update.append(source_file)
# #     except Exception as e:
# #         print(f"Error occurred while listing files: {e}")

# #     return files_to_update


# # @task(container_image="sanskruti557/my-flyte-workflow:latest", retries=2, timeout=timedelta(minutes=5))
# # def evaluate_condition(files_to_update: List[str]) -> bool:
# #     """Evaluate if there are files to update."""
# #     return len(files_to_update) > 0


# # @task(container_image="sanskruti557/my-flyte-workflow:latest", retries=2, timeout=timedelta(minutes=5))
# # def copy_files_task(files_to_update: List[str], source_folder: str):
# #     """Copy updated files to the backup location."""
# #     for source_file in files_to_update:
# #         destination_file = source_file.replace(source_folder, backup_folder, 1)
# #         try:
# #             client.copy_object(
# #                 bucket_name,
# #                 destination_file,
# #                 CopySource(bucket_name, source_file)
# #             )
# #             print(f"File '{source_file}' copied to '{destination_file}'.")
# #         except Exception as e:
# #             print(f"Error occurred while copying file '{source_file}': {e}")


# # @task(container_image="sanskruti557/my-flyte-workflow:latest")
# # def noop_task():
# #     """No operation task."""
# #     raise Exception("Intentional failure for testing email notifications.")


# # @dynamic(container_image="sanskruti557/my-flyte-workflow:latest")
# # def dynamic_copy_files_workflow(source_folders: List[str]):
# #     """Dynamically process files for each source folder."""
# #     for source_folder in source_folders:
# #         files_to_update = list_files_task(source_folder=source_folder)
# #         condition = evaluate_condition(files_to_update=files_to_update)
# #         conditional_copy_files_workflow(source_folder, files_to_update, condition)


# # @workflow
# # def conditional_copy_files_workflow(source_folder: str, files_to_update: List[str], condition: bool):
# #     """Conditional copy based on files that need updating."""
# #     return (
# #         conditional("conditional_copy")
# #         .if_(condition.is_true())
# #         .then(copy_files_task(files_to_update=files_to_update, source_folder=source_folder))
# #         .else_()
# #         .then(noop_task())
# #     )

# # @workflow
# # def copy_files_workflow(source_folders: List[str]):
# #     """Main workflow to trigger the dynamic copy operation."""
# #     dynamic_copy_files_workflow(source_folders=source_folders)


# # # Create a launch plan with email notifications for workflow execution failure
# # copy_files_lp = LaunchPlan.create(
# #     name="copy_files_workflow_with_notifications",
# #     workflow=copy_files_workflow,
# #     notifications=[
# #         Email(
# #             phases=[WorkflowExecutionPhase.FAILED],
# #             recipients_email=["sanskrutiwakode21@gmail.com"],
# #         )
# #     ],
# # )

# from flytekit import task, workflow, dynamic, LaunchPlan, WorkflowExecutionPhase, conditional
# from flytekit.core.notification import Email
# from typing import List
# import subprocess
# import sys
# from datetime import timedelta

# try:
#     from minio import Minio
# except ImportError:
#     print("Minio module not found. Installing...")
#     subprocess.check_call([sys.executable, "-m", "pip", "install", "minio"])

# from minio import Minio
# from minio.commonconfig import CopySource
# from minio.error import S3Error

# # Initialize MinIO client
# client = Minio(
#     endpoint="host.docker.internal:9000",  # Use the service name in Docker
#     access_key="minioadmin",
#     secret_key="minioadmin",
#     secure=False
# )

# # Specify the bucket name and folders
# bucket_name = "flyte-project"
# backup_folder = "backup"


# @task(container_image="sanskruti557/my-flyte-workflow:latest", retries=2, timeout=timedelta(minutes=5))
# def list_files_task(source_folder: str) -> List[str]:
#     """List files that need to be updated in the backup."""
#     files_to_update = []
#     print(f"Listing files in source folder: {source_folder}")

#     try:
#         # Check if the bucket exists
#         if not client.bucket_exists(bucket_name):
#             print(f"Bucket '{bucket_name}' does not exist.")
#             return files_to_update  # Return empty list if the bucket isn't accessible

#         print(f"Bucket '{bucket_name}' exists.")
#         source_objects = client.list_objects(bucket_name, prefix=source_folder, recursive=True)

#         # Iterate over objects and check if they need to be updated
#         for source_obj in source_objects:
#             source_file = source_obj.object_name
#             destination_file = source_file.replace(source_folder, backup_folder, 1)
#             try:
#                 # Check if the file already exists in the backup
#                 dest_obj = client.stat_object(bucket_name, destination_file)
#                 # Add to list if the source file is newer
#                 if source_obj.last_modified > dest_obj.last_modified:
#                     files_to_update.append(source_file)
#             except S3Error as e:
#                 # If the file does not exist in backup, add it to the list
#                 if e.code == "NoSuchKey":
#                     files_to_update.append(source_file)
#     except Exception as e:
#         print(f"Error occurred while listing files: {e}")

#     return files_to_update


# @task(container_image="sanskruti557/my-flyte-workflow:latest", retries=2, timeout=timedelta(minutes=5))
# def evaluate_condition(files_to_update: List[str]) -> bool:
#     """Evaluate if there are files to update."""
#     return len(files_to_update) > 0


# @task(container_image="sanskruti557/my-flyte-workflow:latest", retries=2, timeout=timedelta(minutes=5))
# def copy_files_task(files_to_update: List[str], source_folder: str):
#     """Copy updated files to the backup location."""
#     for source_file in files_to_update:
#         destination_file = source_file.replace(source_folder, backup_folder, 1)
#         try:
#             client.copy_object(
#                 bucket_name,
#                 destination_file,
#                 CopySource(bucket_name, source_file)
#             )
#             print(f"File '{source_file}' copied to '{destination_file}'.")
#         except Exception as e:
#             print(f"Error occurred while copying file '{source_file}': {e}")


# @task(container_image="sanskruti557/my-flyte-workflow:latest")
# def noop_task():
#     """No operation task."""
#     raise Exception("Intentional failure to test email notifications.")


# @dynamic(container_image="sanskruti557/my-flyte-workflow:latest")
# def dynamic_copy_files_workflow(source_folders: List[str]):
#     """Dynamically process files for each source folder."""
#     for source_folder in source_folders:
#         files_to_update = list_files_task(source_folder=source_folder)
#         condition = evaluate_condition(files_to_update=files_to_update)
#         conditional_copy_files_workflow(source_folder, files_to_update, condition)


# @workflow
# def conditional_copy_files_workflow(source_folder: str, files_to_update: List[str], condition: bool):
#     """Conditional copy based on files that need updating."""
#     return (
#         conditional("conditional_copy")
#         .if_(condition.is_true())
#         .then(copy_files_task(files_to_update=files_to_update, source_folder=source_folder))
#         .else_()
#         .then(noop_task())
#     )


# @workflow
# def copy_files_workflow(source_folders: List[str]):
#     """Main workflow to trigger the dynamic copy operation."""
#     return dynamic_copy_files_workflow(source_folders=source_folders)


# copy_files_lp = LaunchPlan.create(
#     name="copy_files_workflow_with_notifications",
#     workflow=copy_files_workflow,
#     notifications=[
#         Email(
#             phases=[WorkflowExecutionPhase.FAILED],
#             recipients_email=["sanskrutiwakode21@gmail.com"],
#         )
#     ],
# )