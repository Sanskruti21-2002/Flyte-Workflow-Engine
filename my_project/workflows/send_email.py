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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flytekit.exceptions.user import FlyteEntityNotExistException
from flytekit.configuration import Config, SerializationSettings, ImageConfig
import subprocess
import yaml
import time
from io import BytesIO
from flytekit.remote import FlyteRemote
from flytekit.configuration import Config
import re 
from flytekit.models.core.execution import WorkflowExecutionPhase
from flytekit.models.core.identifier import NodeExecutionIdentifier, WorkflowExecutionIdentifier

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

# SMTP configuration
smtp_host = "smtp.gmail.com"
smtp_port = 587
smtp_user = "sanskrutiwakode21@gmail.com"
smtp_pass = "ukpd mrxm rjrp pqhi"

# Email content
sender_email = "sanskrutiwakode21@gmail.com"
receiver_email = "sanskrutiwakode21@gmail.com"
import time 


image_spec = ImageConfig(
    default_image="sanskruti557/my-flyte-workflow:latest"
)


# Function to list folders in a bucket
# @task(container_image="sanskruti557/my-flyte-workflow:latest", retries=2, timeout=timedelta(minutes=5))


def get_minio_client():
   
    client = Minio(
        endpoint="127.0.0.1:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False
    )
    return client

def list_folders():
    print("Inside list folders ")

    # Initialize MinIO client
    client = Minio(
        endpoint="127.0.0.1:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False
    )

    if not client.bucket_exists(bucket_name):
        logger.error(f"Bucket '{bucket_name}' does not exist.")
        raise Exception(f"Bucket '{bucket_name}' does not exist.")

    try:
        source_objects = client.list_objects(bucket_name, recursive=True)
        
        folders = set()
        for source_obj in source_objects:
            # Extract the folder name from the object name
            folder_name = source_obj.object_name.split('/')[0]
            folders.add(folder_name)
        print("Folders:", folders)
        return list(folders)
    except FileNotFoundError as fnf_error:
        print("error!")
        return []


def list_files(prefix):
     # Initialize MinIO client
    client = Minio(
        endpoint="127.0.0.1:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False
    )
    try:
        objects = client.list_objects(bucket_name, prefix=prefix, recursive=True)
        files = [obj.object_name for obj in objects]
        return files
    except S3Error as err:
        print("Error occurred:", err)
        return []
    

# @task(container_image="sanskruti557/my-flyte-workflow:latest", retries=2, timeout=timedelta(minutes=5))
def execute_workflow():
    # Assuming copy_files_workflow is your workflow entity
    print("Inside executw workflow")
    flyte_entity = copy_files_workflow  # one of FlyteTask, FlyteWorkflow, or FlyteLaunchPlan
    remote = FlyteRemote(config=Config.auto(), 
    default_project="flytesnacks",
     default_domain="development")
    try:
        execution = remote.execute(
            flyte_entity,
            inputs={"source_folders": ["source1", "source2"]},
            execution_name="my-execution-12",
            wait=True
        )
        print("Execution -> ", execution)
    except Exception as e:
        print("Error during execution:", e)



def check_execution_status_and_notify(execution_id):
    config = Config.auto()
    remote = FlyteRemote(config=config, 
    default_project="flytesnacks",
     default_domain="development")
    # execution_id = input("Please enter the execution id -> ").strip()
    aborted = False
    try:
        while True:
            execution = remote.fetch_execution(name=execution_id)
            # print("Executuoj - > ",execution)
            phase = execution.closure.phase
            print(" Phase -> ",phase)

            if phase == WorkflowExecutionPhase.SUCCEEDED:
                send_email("Workflow Succeeded", "The workflow execution has succeeded.")
                break
            elif phase == WorkflowExecutionPhase.FAILED:
                send_email("Workflow Failed", "The workflow execution has failed.")
                break
            elif phase == WorkflowExecutionPhase.ABORTED:
                
                send_email("Workflow Aborted", "The workflow execution has been aborted.")
                break
            
                   
            elif phase == WorkflowExecutionPhase.TIMED_OUT:
                send_email("Workflow Timed Out", "The workflow execution has timed out.")
                break
            time.sleep(20) 
    except FlyteEntityNotExistException:
        print("The specified execution does not exist. Please check the execution ID and try again.")


def send_email(subject: str, body: str):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
    finally:
        server.quit()


# Simulated external state management
workflow_state = "running"  # Possible states: running, paused, terminated

def phase_to_string(phase_int):
    phase_mapping = {
        0: "UNDEFINED",
        1: "QUEUED",
        2: "RUNNING",
        3: "SUCCEEDING",
        4: "SUCCEEDED",
        5: "FAILING",
        6: "FAILED",
        7: "ABORTED",
        8: "TIMED_OUT",
        9: "ABORTING"
    }
    return phase_mapping.get(phase_int)


def parse_logs_for_file_count(logs):
    # Use a regular expression to find all occurrences of the file copy message
    file_copy_pattern_1 = re.compile(r"File 'source1.' copied to '.'\.")
    file_copy_pattern_2 = re.compile(r"File 'source4.' copied to '.'\.")
    matches_1 = file_copy_pattern_1.findall(logs)
    matches_2 = file_copy_pattern_2.findall(logs)
    return [len(matches_1),len(matches_2)]

def fetch_task_status_and_logs(execution_id, namespace):
    
    # Initialize FlyteRemote
    remote = FlyteRemote(
        config=Config.auto(),
        default_project="flytesnacks",
        default_domain="development",
    )
    # Fetch the execution
    execution = remote.fetch_execution(name=execution_id)
    phase = execution.closure.phase
    phase_str = phase_to_string(phase)
    print(f"\nWorkflow Status: {phase_str}\n")

    # Define a mapping from node execution IDs to task names
    node_to_task_name = {
        "n0": "dynamic_copy_files_workflow",
        "n0-0-dn0": "event_detection_task (source1)",
        "n0-0-dn1": "event_detection_task (source2)",
        "n0-0-dn2": "check_changes (source1)",
        "n0-0-dn3": "check_changes (source2)",
        "n0-0-dn2-0-dn2-dn0": "conditional_copy_files_workflow (source1)",
        "n0-0-dn3-0-dn3-dn0": "conditional_copy_files_workflow (source2)",
        "fuv166tq": "list_files_task (source1)",
        "fsc6oyiq": "list_files_task (source2)",
        "fuz2acyi": "copy_files_task (source1)",
        "fsg6o2ni": "copy_files_task (source2)",
        "n0-0-dn2-0-dn2-dn1": "noop_task (source1)",
        "n0-0-dn3-0-dn3-dn1": "noop_task (source2)"
    }
    # Define a mapping from pod names to task names
    pod_to_task_name = {
        "n0-0": "dynamic_copy_files_workflow",
        "n0-0-dn0-0": "event_detection_task (source1)",
        "n0-0-dn1-0": "event_detection_task (source2)",
        "n0-0-dn2-0": "check_changes (source1)",
        "n0-0-dn3-0": "check_changes (source2)",
        "n0-0-dn2-0-dn2-dn0-0": "conditional_copy_files_workflow (source1)",
        "n0-0-dn3-0-dn3-dn0-0": "conditional_copy_files_workflow (source2)",
        "fuv166tq-0": "list_files_task (source1)",
        "fsc6oyiq-0": "list_files_task (source2)",
        "fuz2acyi-0": "copy_files_task (source1)",
        "fsg6o2ni-0": "copy_files_task (source2)",
        "n0-0-dn2-0-dn2-dn1-0": "noop_task (source1)",
        "n0-0-dn3-0-dn3-dn1-0": "noop_task (source2)"
    }


    # Sync to get node executions
    synced_execution = remote.sync(execution, sync_nodes=True)
    node_executions = synced_execution.node_executions
    
        

    # Fetch logs
    pods = subprocess.check_output(['kubectl', 'get', 'pods', '-n', namespace, '-o', 'name']).decode('utf-8').splitlines()
    relevant_pods = [pod for pod in pods if execution_id in pod]
    logs = ""
    for pod in relevant_pods:
        print("\n\n\t")
        pod_name = pod.split('/')[-1]
        node_execution_id = pod_name.replace(f"{execution_id}-", "")
        node_name = pod_to_task_name.get(node_execution_id)
        parts = node_execution_id.rsplit('-', 1)
        
        
        node_execution_idd = '-'.join(parts[:-1])
        # task_name = node_to_task_name.get(node_id)
        task_name = pod_to_task_name.get(node_execution_id)

        print(f"Fetching logs for pod: {pod_name} (Task: {task_name})")
        
                 # Define the node execution identifier
        node_execution_iden = NodeExecutionIdentifier(
            node_id=node_execution_idd,
            execution_id=WorkflowExecutionIdentifier(
                project='flytesnacks',
                domain='development',
                name=execution_id
            )
        )
        # Fetch the node execution
        node_execution = remote.client.get_node_execution(node_execution_iden)
        # Get the phase of the node execution
        phase = node_execution.closure.phase
        task_phase = phase_to_string(phase)
        print(f" Node : {node_name}, Status: {task_phase}")
        


        try:
            logs += subprocess.check_output(['kubectl', 'logs', pod_name, '-n', namespace]).decode('utf-8')
        except subprocess.CalledProcessError as e:
            print(f"Error fetching logs for pod {pod_name}: {e}")
    return phase_str, logs
    

def poll_logs_and_status(interval=60):


    previous_files_copied_source1 = 0
    previous_files_copied_source4 = 0
    execution_id = input("Please enter the execution ID: ").strip()
    
    namespace = "flytesnacks-development" 

    while True:
        phase_str, logs = fetch_task_status_and_logs(execution_id, namespace)

        # Check if the workflow is in a terminal state
        if phase_str in ["SUCCEEDED", "FAILED", "ABORTED"]:
            
            print(f"Workflow has reached a terminal state: {phase_str}")
            break

       
        current_files_copied = parse_logs_for_file_count(logs)
        files_copied_since_last_poll_source1 = current_files_copied[0] - previous_files_copied_source1
        previous_files_copied_source1 = current_files_copied[0]
        files_copied_since_last_poll_source4 = current_files_copied[1] - previous_files_copied_source4
        previous_files_copied_source4 = current_files_copied[1]
        # Append the files copied info to the logs
        logs += f"\nFiles copied since last poll for source1: {files_copied_since_last_poll_source1}\n\nFiles copied since last poll for source1: {files_copied_since_last_poll_source4}\n"
        time.sleep(20)

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

def fetch_running_executions():
    # Initialize FlyteRemote
    remote = FlyteRemote(
        config=Config.auto(),
        default_project="flytesnacks",
        default_domain="development",
    )
    # Fetch all executions
    executions = remote.client.list_executions(
        project="flytesnacks",
        domain="development",
        limit=100  # Adjust the limit as needed
    )
    # Filter running executions
    running_executions = [
        execution for execution in executions if execution.closure.phase == WorkflowExecutionPhase.RUNNING
    ]
    for execution in running_executions:
        print(f"Running Execution ID: {execution.id.name}")

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
    url = "http://localhost:30080/api/v1/executions/recover"
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
    try:
        response = requests.post(url, json=data, headers=headers)
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response body: {response.text}")
        if response.status_code == 200:
            new_execution_id = response.json().get("id", {}).get("name")
            logger.info(f"Workflow execution recovered successfully. New execution ID: {new_execution_id}")
            return new_execution_id
        else:
            logger.error(f"Failed to recover workflow execution: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exception occurred: {e}")
        return None
    
def relaunch_workflow(execution_id):
    logger.info("Called relaunch workflow API")
    url = "http://localhost:30080/api/v1/executions/relaunch"
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
    try:
        response = requests.post(url, json=data, headers=headers)
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response body: {response.text}")
        if response.status_code == 200:
            new_execution_id = response.json().get("id", {}).get("name")
            logger.info(f"Workflow execution relaunched successfully. New execution ID: {new_execution_id}")
            return new_execution_id
        else:
            logger.error(f"Failed to relaunch workflow execution: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exception occurred: {e}")
        return None
    
@task(container_image="sanskruti557/my-flyte-workflow:latest", retries=2, timeout=timedelta(minutes=5))
def event_detection_task(source_folder: str) -> bool:
    check_workflow_state()
    logger.info(f"Starting event detection for folder: {source_folder}")
    # Check if the source folder exists in the bucket
    try:
        # Attempt to list objects in the source folder to check existence
        source_objects = client.list_objects(bucket_name, prefix=source_folder, recursive=True)
        if not any(source_objects):
            error_message = f"Source folder '{source_folder}' does not exist in the bucket."
            logger.error(error_message)
            send_email("Event Detection Failed", error_message)
            return False
        # Proceed with event detection if the folder exists
        files_to_update = list_files_task(source_folder=source_folder)
        event_detected = len(files_to_update) > 0
        logger.info(f"Event detection completed for folder: {source_folder}, Event detected: {event_detected}")
        return event_detected
    except Exception as e:
        error_message = f"Error detecting events in source folder '{source_folder}': {e}"
        logger.error(error_message)
        send_email("Event Detection Error", error_message)
        return False

@task(container_image="sanskruti557/my-flyte-workflow:latest", retries=2, timeout=timedelta(minutes=10))
def list_files_task(source_folder: str) -> List[str]:
    logger.info(f"\n\n List Files Task for folder: {source_folder}\n\n")
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
        error_message = f"Error during file listing for folder '{source_folder}': {e}"
        logger.error(error_message)
        send_email("Task(list_files_task) Failed", error_message)
        raise
        

    logger.info(f"Files to update: {files_to_update}")
    
    return files_to_update

@task(container_image="sanskruti557/my-flyte-workflow:latest", retries=2, timeout=timedelta(minutes=20))
def copy_files_task(files_to_update: List[str], source_folder: str):
    logger.info(f"Starting Copy Files Task for folder: {source_folder}")
    check_workflow_state()
    logger.info("Starting file copy task.")
    copied_files = []
    count = 1
    try:
        # raise Exception("sjdhfg")
        for source_file in files_to_update:
            count+=1
            destination_file = source_file.replace(source_folder, backup_folder, 1)
            try:
                client.copy_object(
                    bucket_name,
                    destination_file,
                    CopySource(bucket_name, source_file)
                )
                logger.info(f"File '{source_file}' copied to '{destination_file}'.")
                copied_files.append(source_file)
            except S3Error as e:
                logger.error(f"S3 error occurred while copying file {source_file}: {e}")
                raise
            except Exception as e:
                logger.error(f"Error copying file '{source_file}': {e}")
                raise
    except Exception as e:
        error_message = f"Error during Copying Files for folder '{source_folder}': {e}"
        send_email("Task(copy_files_task) Failed", error_message)
        raise
    finally:
        if copied_files:
            send_email(
                "Files Copied Successfully",
                f"Total {count} files were copied from '{source_folder}':\n" + "\n".join(copied_files)
            )

        

@task(container_image="sanskruti557/my-flyte-workflow:latest")
def noop_task(message:str):
    logger.info("No operation task executed.")
    send_email(
        "No Operation Executed",
        f"""
        The workflow executed the noop task. Details: {message}
        """
    )

@task(container_image="sanskruti557/my-flyte-workflow:latest")
def has_files_to_update(files_to_update: List[str]) -> bool:
    return len(files_to_update) > 0

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
            .then(noop_task(message=f"No changes detected in folder: {source_folders[i]}"))
        )
    

@dynamic(container_image="sanskruti557/my-flyte-workflow:latest")
def conditional_copy_files_workflow(source_folder: str, changes_detected: bool):
    logger.info(f"Starting conditional copy files workflow for folder: {source_folder}")
    files_to_update = list_files_task(source_folder=source_folder)
    copy_files_task(files_to_update,source_folder)
    # condition = evaluate_condition(files_to_update=files_to_update).with_overrides(name=f"evaluate_condition_{source_folder}")
    # return (
    #     conditional("conditional_copy")
    #     .if_(condition.is_true())
    #     .then(copy_files_task(files_to_update=files_to_update, source_folder=source_folder))
    #     .else_()
    #     .then(noop_task(message=f"No changes detected in folder : {source_folder}"))
    # )


def store_execution_id():
    # Configure MinIO client
    execution_id = input("Please enter the execution id here -> ")
    client = Minio(
        "127.0.0.1:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False
    )
    # Define the bucket name and object name
    bucket_name = "flyte-project"
    object_name = "execution-id.txt"
    # Create a BytesIO object from the file content
    file_content = execution_id
    file_data = BytesIO(file_content.encode('utf-8'))
    # Reset the BytesIO object's position to the beginning
    file_data.seek(0)
    # Upload the file to the bucket
    client.put_object(
        bucket_name,
        object_name,
        file_data,
        length=len(file_content.encode('utf-8')),
        content_type="text/plain"
    )
    print(f"File '{object_name}' created in bucket '{bucket_name}'.")


@workflow(failure_policy=WorkflowFailurePolicy.FAIL_AFTER_EXECUTABLE_NODES_COMPLETE)
def copy_files_workflow(source_folders: List[str]):
    logger.info("Starting copy files workflow.")
    # email_thread = threading.Thread(target = check_execution_status_and_notify)
    # email_thread.start()

    # email_thread = threading.Thread(target = list_files_task)
    # email_thread.start()
    
    
    # # Start user input thread
    # user_input_thread = threading.Thread(target=manage_workflow)
    # user_input_thread.start()

    # Start monitoring thread
    # monitoring_thread = threading.Thread(target=monitor_workflow)
    # monitoring_thread.start()

    monitoring_thread = threading.Thread(target=poll_logs_and_status)
    monitoring_thread.start()

    # Trigger the dynamic workflow
    
    dynamic_copy_files_workflow(source_folders=source_folders)

# Define a Launch Plan with a Schedule
scheduled_launch_plan = LaunchPlan.create(
    name="scheduled_copy_files_workflow",
    workflow=copy_files_workflow,
    schedule=CronSchedule(schedule="0 * * * *"),  # Runs every hour
    default_inputs={"source_folders": ["source1","source2"]}
)