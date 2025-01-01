import time
import threading
import requests
from flytekit import task, workflow, dynamic, conditional, LaunchPlan, CronSchedule, WorkflowFailurePolicy
from flytekit.remote import FlyteRemote
from flytekit.configuration import Config
from typing import List
import logging
from datetime import timedelta
from flytekit.exceptions.user import FlyteRecoverableException
from minio import Minio
from minio.commonconfig import CopySource
from minio.error import S3Error
from flytekit.models.core.execution import WorkflowExecutionPhase

# Initialize MinIO client
client = Minio(
    endpoint="host.docker.internal:9000",  # Use the service name in Docker
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

# Specify the bucket name and folders
bucket_name = "flyte-project"
backup_folder = "backup"

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Simulated external state management
workflow_state = "running"  # Possible states: running, paused, terminated

import subprocess
import yaml
import time
from flytekit.remote import FlyteRemote
from flytekit.configuration import Config
from flytekit.models.core.execution import WorkflowExecutionPhase

# def monitor_workflow():
#     # Initialize FlyteRemote
#     remote = FlyteRemote(
#         config=Config.auto(),
#         default_project="flytesnacks",
#         default_domain="development",
#     )
#     # Fetch the execution
#     execution_id = input("Please enter the execution ID: ").strip()
#     execution = remote.fetch_execution(name=execution_id)
#     def print_node_executions(node_executions):
#         all_done = True
#         for node_id, node_execution in node_executions.items():
#             phase = node_execution.closure.phase
#             print(f"Node ID: {node_id}, Phase: {phase}")
#             # Check if the node is dynamic or a sub-workflow and has child nodes
#             if node_execution.metadata.is_dynamic or node_execution.metadata.is_parent_node:
#                 # Fetch child node executions using the workflow execution ID
#                 child_node_executions, _ = remote.client.list_node_executions(
#                     workflow_execution_identifier=node_execution.id.execution_id,
#                     unique_parent_id=node_execution.id.node_id
#                 )
#                 # Iterate over the list of child node executions
#                 child_node_dict = {n.id.node_id: n for n in child_node_executions}
#                 if not print_node_executions(child_node_dict):
#                     all_done = False
#             # Check if all nodes are in phase 3
#             if phase != 3:
#                 all_done = False
#         return all_done
#     # Continuously print node executions until all are in phase 3
#     while True:
#         synced_execution = remote.sync(execution, sync_nodes=True)
#         if print_node_executions(synced_execution.node_executions):
#             print("All nodes have completed.")
#             break
#         time.sleep(10)

def fetch_logs_for_execution():
    
    execution_id = input("Please enter the execution ID: ").strip()
    
    namespace = "flytesnacks-development" 
    # Initialize FlyteRemote
    remote = FlyteRemote(
        config=Config.auto(),
        default_project="flytesnacks",
        default_domain="development",
    )
    # Fetch the execution
    execution = remote.fetch_execution(name=execution_id)
    synced_execution = remote.sync(execution, sync_nodes=True)
    # List all pods and filter by execution ID
    pods = subprocess.check_output(['kubectl', 'get', 'pods', '-n', namespace, '-o', 'name']).decode('utf-8').splitlines()
    relevant_pods = [pod for pod in pods if execution_id in pod]
    # Fetch logs for each relevant pod
    for pod in relevant_pods:
        pod_name = pod.split('/')[-1]  # Extract pod name from 'pod/<pod-name>'
        print(f"Fetching logs for pod: {pod_name}")
        try:
            logs = subprocess.check_output(['kubectl', 'logs', pod_name, '-n', namespace])
            print(logs.decode('utf-8'))
        except subprocess.CalledProcessError as e:
            print(f"Error fetching logs for pod {pod_name}: {e}")

def fetch_logs_for_execution():
    execution_id = input("Please enter the execution ID: ").strip()
    namespace = "flytesnacks-development"
    # Initialize FlyteRemote
    remote = FlyteRemote(
        config=Config.auto(),
        default_project="flytesnacks",
        default_domain="development",
    )
    # Fetch the execution
    execution = remote.fetch_execution(name=execution_id)
    # Wait for the execution to reach a terminal state
    while execution.closure.phase not in {WorkflowExecutionPhase.SUCCEEDED, WorkflowExecutionPhase.FAILED, WorkflowExecutionPhase.ABORTED}:
        print(f"Current execution phase: {execution.closure.phase}. Waiting for completion...")
        time.sleep(10)  # Wait for 10 seconds before checking again
        execution = remote.sync(execution)
    print(f"Execution {execution_id} has completed with phase: {execution.closure.phase}. Fetching logs...")
    # List all pods and filter by execution ID
    pods = subprocess.check_output(['kubectl', 'get', 'pods', '-n', namespace, '-o', 'name']).decode('utf-8').splitlines()
    relevant_pods = [pod for pod in pods if execution_id in pod]
    # Fetch logs for each relevant pod
    for pod in relevant_pods:
        pod_name = pod.split('/')[-1]  # Extract pod name from 'pod/<pod-name>'
        print(f"Fetching logs for pod: {pod_name}")
        try:
            logs = subprocess.check_output(['kubectl', 'logs', pod_name, '-n', namespace])
            print(logs.decode('utf-8'))
        except subprocess.CalledProcessError as e:
            print(f"Error fetching logs for pod {pod_name}: {e}")

def check_workflow_state():
    global workflow_state
    while workflow_state == "paused":
        logger.info("Workflow is paused. Waiting to resume...")
        time.sleep(5)  # Wait and check again
    if workflow_state == "terminated":
        raise Exception("Workflow has been terminated.")

def manage_workflow():
    execution_id = input("Please enter the execution ID: ").strip()
    while True:
        action = input("Enter 'terminate' to terminate the workflow or 'recover' to recover it: ").strip().lower()
        if action == "terminate":
            terminate_workflow(execution_id)
        elif action == "recover":
            recover_workflow(execution_id)
        else:
            print("Invalid input. Please enter 'terminate' or 'recover'.")

def terminate_workflow(execution_id):
    remote = FlyteRemote(
        config=Config.auto(),
        default_project="flytesnacks",
        default_domain="development",
    )
    # Fetch the execution using the correct parameter name
    execution = remote.fetch_execution(name=execution_id)
    # Check if the execution is already in a terminal state
    if execution.closure.phase in {WorkflowExecutionPhase.SUCCEEDED, WorkflowExecutionPhase.FAILED, WorkflowExecutionPhase.ABORTED}:
        print(f"Execution {execution_id} is already in a terminal state: {execution.closure.phase}")
        return
    # Attempt to terminate the execution
    try:
        remote.terminate(execution, cause="User requested termination")
        print(f"Execution {execution_id} terminated successfully.")
    except Exception as e:
        print(f"Failed to terminate execution {execution_id}: {e}")

def recover_workflow(execution_id):
    logger.info("Called recover workflow API")
    url = "http://localhost:8088/api/v1/executions/recover"
    data = {
        "id": {
            "project": "flytesnacks",
            "domain": "development",
            "name": execution_id
        }
    }
    headers = {
        "Content-Type": "application/json",
        # Add authorization headers if needed
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        new_execution_id = response.json().get("id", {}).get("name")
        logger.info(f"Workflow execution recovered successfully. New execution ID: {new_execution_id}")
    else:
        logger.error(f"Failed to recover workflow execution: {response.text}")

@task(container_image="sanskruti557/my-flyte-workflow:latest", retries=2, timeout=timedelta(minutes=5))
def event_detection_task(source_folder: str) -> bool:
    check_workflow_state()
    logger.info(f"Starting event detection for folder: {source_folder}")
    try:
        if source_folder == "test_folder":
            raise FlyteRecoverableException("Simulating task failure to test retry logic")
        files_to_update = list_files_task(source_folder=source_folder)
        event_detected = len(files_to_update) > 0
        logger.info(f"Event detection completed for folder: {source_folder}, Event detected: {event_detected}")
        return event_detected
    except Exception as e:
        logger.error(f"Error detecting events in source folder '{source_folder}': {e}")
        return False

@task(container_image="sanskruti557/my-flyte-workflow:latest", retries=2, timeout=timedelta(minutes=5))
def list_files_task(source_folder: str) -> List[str]:
    check_workflow_state()
    attempt = 1  # Track retry attempts
    logger.info(f"Attempt {attempt}: Listing files in source folder: {source_folder}")
    attempt += 1  # Increment attempt for each retry
    if source_folder == "test_folder":
        raise FlyteRecoverableException("Simulating task failure to test retry logic")
    
    files_to_update = []

    if not client.bucket_exists(bucket_name):
        logger.error(f"Bucket '{bucket_name}' does not exist.")
        raise Exception(f"Bucket '{bucket_name}' does not exist.")

    try:
        logger.info("Attempting to list objects in the source folder.")
        source_objects = client.list_objects(bucket_name, prefix=source_folder, recursive=True)

        if not any(source_objects):
            logger.warning(f"Source folder '{source_folder}' does not exist or is empty.")
            return files_to_update
        
        for source_obj in source_objects:
            source_file = source_obj.object_name
            destination_file = source_file.replace(source_folder, backup_folder, 1)

            try:
                dest_obj = client.stat_object(bucket_name, destination_file)
                if source_obj.last_modified > dest_obj.last_modified:
                    files_to_update.append(source_file)
            except S3Error as e:
                if e.code == "NoSuchKey":
                    files_to_update.append(source_file)
    except FileNotFoundError as fnf_error:
        logger.error(f"File not found error: {fnf_error}")
        raise fnf_error

    logger.info(f"Files to update: {files_to_update}")
    return files_to_update

@task(container_image="sanskruti557/my-flyte-workflow:latest", retries=2, timeout=timedelta(minutes=5))
def evaluate_condition(files_to_update: List[str]) -> bool:
    check_workflow_state()
    logger.info("Evaluating condition based on files to update.")
    if len(files_to_update) > 0:
        logger.info(f"{len(files_to_update)} files to update.")
    else:
        logger.warning("No files to update.")
    return len(files_to_update) > 0

@task(container_image="sanskruti557/my-flyte-workflow:latest", retries=2, timeout=timedelta(minutes=5))
def copy_files_task(files_to_update: List[str], source_folder: str):
    check_workflow_state()
    logger.info("Starting file copy task.")
    try:
        for source_file in files_to_update:
            destination_file = source_file.replace(source_folder, backup_folder, 1)
            try:
                client.copy_object(
                    bucket_name,
                    destination_file,
                    CopySource(bucket_name, source_file)
                )
                logger.info(f"File '{source_file}' copied to '{destination_file}'.")
            except S3Error as e:
                logger.error(f"S3 error occurred while copying file {source_file}: {e}")
                raise
            except Exception as e:
                logger.error(f"Error copying file '{source_file}': {e}")
                raise
    except Exception as e:
        logger.error(f"Error during file copy operation: {e}")
        raise

@task(container_image="sanskruti557/my-flyte-workflow:latest")
def noop_task():
    logger.info("No operation task executed.")

@dynamic(container_image="sanskruti557/my-flyte-workflow:latest")
def dynamic_copy_files_workflow(source_folders: List[str]):
    logger.info("Starting dynamic copy files workflow.")
    # Collect results of event detection for all folders
    changes_detected_results = [event_detection_task(source_folder=sf).with_overrides(name=f"event_detection_{sf}") for sf in source_folders]
    
    # Barrier synchronization: Wait for all event detection tasks to complete
    for i, changes_detected in enumerate(changes_detected_results):
        result = (
            conditional("check_changes")
            .if_(changes_detected.is_true())
            .then(conditional_copy_files_workflow(source_folder=source_folders[i], changes_detected=changes_detected))
            .else_()
            .then(noop_task().with_overrides(name=f"noop_task_{i}"))
        )

@workflow
def conditional_copy_files_workflow(source_folder: str, changes_detected: bool):
    logger.info(f"Starting conditional copy files workflow for folder: {source_folder}")
    files_to_update = list_files_task(source_folder=source_folder)
    condition = evaluate_condition(files_to_update=files_to_update).with_overrides(name=f"evaluate_condition_{source_folder}")
    return (
        conditional("conditional_copy")
        .if_(condition.is_true())
        .then(copy_files_task(files_to_update=files_to_update, source_folder=source_folder))
        .else_()
        .then(noop_task().with_overrides(name=f"noop_task_{source_folder}"))
    )

@workflow(failure_policy=WorkflowFailurePolicy.FAIL_AFTER_EXECUTABLE_NODES_COMPLETE)
def copy_files_workflow(source_folders: List[str]):
    logger.info("Starting copy files workflow.")

    monitoring_thread = threading.Thread(target=fetch_logs_for_execution)
    monitoring_thread.start()

    # Trigger the dynamic workflow
    dynamic_copy_files_workflow(source_folders=source_folders)

# Define a Launch Plan with a Schedule
scheduled_launch_plan = LaunchPlan.create(
    name="scheduled_copy_files_workflow",
    workflow=copy_files_workflow,
    schedule=CronSchedule(schedule="0 * * * *"),  # Runs every hour
    default_inputs={"source_folders": ["source1", "source2"]}
)
