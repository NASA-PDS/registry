#!/usr/bin/env python

"""
This script is used to run a stress test Harvest

To stress test Harvest with 25 simultaneous writes, run the following command:
python harvest_stress_test.py "harvest_command_here" 25
"""

import argparse
import concurrent.futures
import subprocess


# Function to run the subprocess command
def run_command(command):
    try:
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return f"Command: {command}\nStdout: {result.stdout}\nStderr: {result.stderr}"
    except Exception as e:
        return f"Command: {command}\nError: {str(e)}"


def main():
    parser = argparse.ArgumentParser(description="Run stress tests with user-provided command and number of simultaneous runs.")
    parser.add_argument("command", help="The command to run (use 'YOUR_COMMAND_HERE' as a placeholder)")
    parser.add_argument("num_processes", type=int, help="The number of processes to run")

    args = parser.parse_args()

    command = args.command
    num_processes = args.num_processes

    # List of commands
    commands = [command.replace("YOUR_COMMAND_HERE", f"your_actual_command_{i}") for i in range(num_processes)]

    # Create a ThreadPoolExecutor with the desired number of workers
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_processes) as executor:
        # Submit the commands for execution
        futures = [executor.submit(run_command, command) for command in commands]

        # Wait for all the commands to complete and retrieve the results
        results = [future.result() for future in concurrent.futures.as_completed(futures)]

    # Print the results
    for result in results:
        print(result)


if __name__ == "__main__":
    main()
