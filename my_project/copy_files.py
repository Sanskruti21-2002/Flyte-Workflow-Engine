import os

# Set source and destination paths
source_path = "/Users/aasthathorat/Desktop/Flyte/my_project/source2"
destination_path = "my-minio/flyte-project/source2"

# Loop from 1 to 1000 and execute the mc command
for i in range(1, 1001):  # 1 to 1000 inclusive
    source_file = f"{source_path}/source4_file_{i}.txt"
    destination_file = f"{destination_path}/source4_file_{i}.txt"
    
    # Construct the command
    command = f"mc cp {source_file} {destination_file}"
    
    # Print the command (optional, for debugging)
    print(f"Executing: {command}")
    
    # Execute the command
    os.system(command)

print("All files have been copied successfully.")