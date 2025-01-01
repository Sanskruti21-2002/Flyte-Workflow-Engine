from django.shortcuts import render, redirect
from flytekit.remote import FlyteRemote  # Add this import for FlyteRemote
from flytekit.configuration import Config
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from my_project.workflows.send_email import terminate_workflow, relaunch_workflow
from my_project.workflows.send_email import fetch_task_status_and_logs
from my_project.workflows.send_email import recover_workflow
from my_project.workflows.send_email import execute_workflow  # Adjust the import pat
from my_project.workflows.send_email import list_folders  # Adjust the import pat
from my_project.workflows.send_email import list_files  # Adjust the import pat
from my_project.workflows.send_email import get_minio_client  # Adjust the import pat
import json
from minio.error import S3Error



bucket_name = 'flyte-project'
@csrf_exempt
def trigger_workflow(request):
    if request.method == 'POST':
        try:
            # Initialize FlyteRemote
            remote = FlyteRemote(
                config=Config.auto(),
                default_project="flytesnacks",
                default_domain="development",
            )
            # Fetch the workflow
            flyte_workflow = remote.fetch_workflow(name="send_email.copy_files_workflow", version="v1")
            # Execute the workflow
            execution = remote.execute(
                flyte_workflow, 
                inputs={"source_folders": ["source1", "source2"]}, 
                execution_name="workflow-execution", 
                wait=False
            )
            # Return the execution link
            execution_link = f"http://flyte.example.net/console/projects/flytesnacks/domains/development/executions/{execution.id.name}"
            return JsonResponse({"status": "success", "link": execution_link})
        except Exception as e:
            return JsonResponse({"status": "error", "error": str(e)})
    else:
        return JsonResponse({"status": "error", "error": "Invalid request method."})
def get_folders(request):
    # Get the list of folders
    folders = list_folders()
    print("Folders -> ", folders)

    # Fetch files for each folder
    files_data = {}
    for folder in folders:
        files = list_files(folder)  # Fetch files for the current folder
        files_data[folder] = files  # Store in a dictionary by folder name

    # Pass folders and files to the template
    return render(request, "base.html", {"folders": folders, "files_data": files_data})


def get_files_for_folder(request,prefix):
    files = list_files(prefix)
    return render(request,"base.html", {"files": files})


# to delete a selected file for backup folder
@csrf_exempt
def delete_file(request):
    if request.method == 'POST':
        try:
            # Parse the incoming JSON request
            data = json.loads(request.body)
            folder = data.get('folder')  # e.g., "source1", "source2", or "backup"
            filename = data.get('filename')  # The name of the file to delete
          

            # Validate the input
            if not folder or not filename:
                return JsonResponse({"status": "error", "error": "Folder or filename is missing."})

            # Construct the object name (e.g., "source1/file1.txt")
            object_name = filename
            print(" onject nane-> ",object_name)

            # Remove the object from MinIO
            client = get_minio_client()
            client.remove_object(bucket_name, object_name)


            return JsonResponse({"status": "success", "message": f"File '{filename}' deleted successfully from '{folder}'."})
        except S3Error as e:
            return JsonResponse({"status": "error", "error": f"MinIO error: {str(e)}"})
        except Exception as e:
            return JsonResponse({"status": "error", "error": str(e)})
    else:
        return JsonResponse({"status": "error", "error": "Invalid request method. Only POST is allowed."})

def new_page(request):
    return render(request, "new_page.html")

def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')


@csrf_exempt
def terminate_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        execution_id = data.get('execution_id')
        try:
            terminate_workflow(execution_id)
            return JsonResponse({"message": f"Execution {execution_id} terminated successfully."})
        except Exception as e:
            return JsonResponse({"message": f"Failed to terminate execution {execution_id}: {e}"})

def recover_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            execution_id = data.get('execution_id')
            if execution_id:
                new_execution_id = recover_workflow(execution_id)
                if new_execution_id:
                    execution_url = f"http://localhost:30080/console/projects/flytesnacks/domains/development/executions/{new_execution_id}"
                    return JsonResponse({
                        "message": f"Execution {execution_id} recovered successfully.",
                        "execution_url": execution_url
                    })
                else:
                    return JsonResponse({"message": "Failed to recover execution."}, status=500)
            else:
                return JsonResponse({"message": "Execution ID is required."}, status=400)
        except Exception as e:
            return JsonResponse({"message": f"Failed to recover execution: {e}"}, status=500)
    else:
        return JsonResponse({"message": "Invalid request method."}, status=405)
def relaunch_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            execution_id = data.get('execution_id')
            if execution_id:
                new_execution_id = relaunch_workflow(execution_id)
                if new_execution_id:
                    execution_url = f"http://localhost:30080/console/projects/flytesnacks/domains/development/executions/{new_execution_id}"
                    return JsonResponse({
                        "message": f"Execution {execution_id} relaunched successfully.",
                        "execution_url": execution_url
                    })
                else:
                    return JsonResponse({"message": "Failed to relaunch execution."}, status=500)
            else:
                return JsonResponse({"message": "Execution ID is required."}, status=400)
        except Exception as e:
            return JsonResponse({"message": f"Failed to relaunch execution: {e}"}, status=500)
    else:
        return JsonResponse({"message": "Invalid request method."}, status=405)
    

def fetch_running_executions_view(request):
    if request.method == 'GET':
        try:
            remote = FlyteRemote(
                config=Config.auto(),
                default_project="flytesnacks",
                default_domain="development",
            )
            executions = remote.client.list_executions(
                project="flytesnacks",
                domain="development",
                limit=100
            )
            running_executions = [
                execution.id.name for execution in executions if execution.closure.phase == WorkflowExecutionPhase.RUNNING
            ]
            return JsonResponse({"message": f"Running Executions: {', '.join(running_executions)}"})
        except Exception as e:
            return JsonResponse({"message": f"Error fetching running executions: {e}"})
        
def fetch_logs(request):
    execution_id = request.GET.get('execution_id')
    namespace = "flytesnacks-development"
    phase_str, logs = fetch_task_status_and_logs(execution_id, namespace)
    return JsonResponse({'phase': phase_str, 'logs': logs})