#!/usr/bin/env python

"""
This script is used to run a stress test Harvest

To stress test Harvest with 25 simultaneous writes, run the following command:
python harvest_stress_test.py --command "harvest_command_here" --runs 25
"""

import argparse
import concurrent.futures
import subprocess


def run_command(command):
    """
    Runs the provided command as a subprocess and returns the result
    """
    try:
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return f"Command: {command}\nStdout: {result.stdout}\nStderr: {result.stderr}"
    except Exception as e:
        return f"Command: {command}\nError: {str(e)}"


def main():
    parser = argparse.ArgumentParser(description="Stress test Harvest with user-provided simultaneous runs.")
    parser.add_argument("command", help="The command to run")
    parser.add_argument("runs", type=int, help="The number of times to run Harvest simultaneously")

    args = parser.parse_args()

    command = args.command
    runs = args.runs

    # List of commands
    # use command.replace if you want to alter part of the command string for each process
    # commands = [command.replace("part to replace", "replace with this") for i in range(runs)]
    commands = [command for i in range(runs)]

    # Create a ThreadPoolExecutor with the desired number of workers
    with concurrent.futures.ThreadPoolExecutor(max_workers=runs) as executor:
        # Submit the commands for execution
        futures = [executor.submit(run_command, command) for command in commands]

        # Wait for all the commands to complete and retrieve the results
        results = [future.result() for future in concurrent.futures.as_completed(futures)]

    # Print the results
    for result in results:
        print(result)


if __name__ == "__main__":
    main()
