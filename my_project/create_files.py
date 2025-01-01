import os

# Define the directory name
directory = "source2"

# Create the directory if it doesn't exist
if not os.path.exists(directory):
    os.makedirs(directory)

# Generate 1000 files with 50 bytes each
for i in range(1, 1001):
    file_name = f"source2_file_{i}.txt"  # Define the file name
    file_path = os.path.join(directory, file_name)  # Get the full file path
    
    # Define content that is exactly 50 bytes long
    content = f"File {i}: This file contains exactly 50 bytes of data.\n"
    
    # Ensure the content length is exactly 50 bytes
    content = content[:50]
    
    # Write the content to the file
    with open(file_path, "w") as file:
        file.write(content)

print(f"1000 files of size 50 bytes have been created in the directory '{directory}'.")