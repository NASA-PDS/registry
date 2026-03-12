#!/usr/bin/env python3
"""
AWS Registry Initialization Script

This script initializes an AWS-deployed registry with test data by:
1. Extracting Terraform outputs (OpenSearch endpoint, credentials endpoint)
2. Running registry-loader-test-init container to load test data into AWS
"""

import os
import sys
import subprocess
import re
import tarfile
import zipfile
import urllib.request
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime
from jinja2 import Template


class RegistryInitializer:
    """Handles AWS Registry initialization tasks."""

    def __init__(self):
        self.script_dir = Path(__file__).parent.resolve()
        self.docker_dir = self.script_dir.parent / "docker"
        self.config_dir = self.script_dir / ".registry-loader"

        # Terraform outputs
        self.opensearch_endpoint: Optional[str] = None
        self.credentials_endpoint: Optional[str] = None
        self.aws_region: Optional[str] = None
        self.cognito_idp_url: Optional[str] = None
        self.collection_name: Optional[str] = None

        # Environment variables
        self.env_vars: Dict[str, str] = {}

    def print_header(self, title: str):
        """Print a formatted header."""
        print("\n" + "=" * 50)
        print(title)
        print("=" * 50 + "\n")

    def print_section(self, emoji: str, message: str):
        """Print a formatted section message."""
        print(f"{emoji} {message}")

    def check_terraform_directory(self) -> bool:
        """Check if we're in a valid terraform directory."""
        main_tf = self.script_dir / "main.tf"
        if not main_tf.exists():
            print("Error: This script must be run from the terraform directory or main.tf must exist")
            return False
        return True

    def run_command(self, cmd: list, capture: bool = True, check: bool = True) -> Optional[str]:
        """
        Run a shell command and return output.

        Args:
            cmd: Command as a list of strings
            capture: Whether to capture output
            check: Whether to raise error on failure

        Returns:
            Command output if capture=True, None otherwise
        """
        try:
            if capture:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=check,
                    cwd=self.script_dir
                )
                return result.stdout.strip()
            else:
                subprocess.run(cmd, check=check, cwd=self.script_dir)
                return None
        except subprocess.CalledProcessError as e:
            if check:
                print(f"Error running command: {' '.join(cmd)}")
                if e.stderr:
                    print(f"Error output: {e.stderr}")
                raise
            return None

    def extract_terraform_outputs(self) -> bool:
        """Extract required outputs from Terraform."""
        self.print_section("📋", "Extracting Terraform outputs...")

        # Check if terraform has been applied
        try:
            self.opensearch_endpoint = self.run_command(
                ["terraform", "output", "-raw", "collection_endpoint"]
            )
        except subprocess.CalledProcessError:
            print("Error: Terraform outputs not found. Have you run 'terraform apply'?")
            return False

        self.credentials_endpoint = self.run_command(
            ["terraform", "output", "-raw", "credentials_endpoint"]
        )

        # Extract AWS region from OpenSearch endpoint
        region_match = re.search(
            r'\.([a-z0-9-]+)\.aoss\.amazonaws\.com',
            self.opensearch_endpoint
        )
        if not region_match:
            print("Error: Could not extract AWS region from OpenSearch endpoint")
            return False

        self.aws_region = region_match.group(1)
        self.cognito_idp_url = f"https://cognito-idp.{self.aws_region}.amazonaws.com"

        # Get NODE_REGISTRY from environment
        node_registry = os.environ.get("NODE_REGISTRY", "registry")

        # Print extracted values
        print(f"   OpenSearch Endpoint: {self.opensearch_endpoint}")
        print(f"   Credentials Endpoint: {self.credentials_endpoint}")
        print(f"   Registry Name: {node_registry}")
        print(f"   AWS Region: {self.aws_region}")
        print(f"   Cognito IDP URL: {self.cognito_idp_url}\n")

        return True

    def validate_required_env_vars(self) -> bool:
        """Validate that all required environment variables are set."""
        required_vars = [
            "COGNITO_ADMIN_USERNAME",
            "COGNITO_ADMIN_PASSWORD",
            "COGNITO_WRITER_USERNAME",
            "COGNITO_WRITER_PASSWORD",
            "COGNITO_CLIENT_ID",
            "TEST_DATA_URL",
        ]

        missing_vars = []
        for var in required_vars:
            value = os.environ.get(var)
            if not value:
                missing_vars.append(var)
            else:
                self.env_vars[var] = value

        if missing_vars:
            print("Error: The following required environment variables are not set:")
            for var in missing_vars:
                print(f"  - {var}")
            print("\nPlease export these variables before running this script")
            return False

        print(f"   Using Cognito credentials for user: {self.env_vars['COGNITO_ADMIN_USERNAME']}")
        print(f"   Cognito Client ID: {self.env_vars['COGNITO_CLIENT_ID']}\n")

        return True

    def check_docker_running(self) -> bool:
        """Check if Docker is running."""
        try:
            self.run_command(["docker", "info"], capture=False)
            return True
        except subprocess.CalledProcessError:
            print("Error: Docker is not running. Please start Docker and try again.")
            return False

    def load_env_file(self):
        """Load environment variables from .env file."""
        env_file = self.docker_dir / ".env"

        if env_file.exists():
            self.print_section("📄", "Loading environment variables from .env file...")
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if "=" in line:
                            key, value = line.split("=", 1)
                            # Remove quotes if present
                            value = value.strip('"').strip("'")
                            self.env_vars[key] = value
        else:
            print("⚠️  Warning: .env file not found, using default values")
            self.env_vars.setdefault("REG_LOADER_IMAGE", "nasapds/registry-loader:latest")
            self.env_vars.setdefault("TEST_DATA_URL",
                "https://github.com/NASA-PDS/registry-ref-data/releases/download/Latest/custom-datasets.tar.gz")
            self.env_vars.setdefault("TEST_DATA_LIDVID",
                "urn:nasa:pds:mars2020.spice::1.0 urn:nasa:pds:mars2020.spice::2.0 urn:nasa:pds:mars2020.spice::3.0")
            self.env_vars.setdefault("CONTAINER_HARVEST_DATA_DIR", "/data")
            self.env_vars.setdefault("REG_DATA_VOLUME", "data-volume")

    def generate_registry_config(self):
        """Generate registry connection XML configuration."""
        self.print_section("📝", "Generating registry connection configuration...")

        # Create config directory
        self.config_dir.mkdir(parents=True, exist_ok=True)

        node_registry = os.environ.get("NODE_REGISTRY", "registry")
        config_file = self.config_dir / "registry-connection.xml"

        config_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<registry_connection index="{node_registry}">
  <cognitoClientId endpoint="{self.opensearch_endpoint}"
                   gateway="{self.credentials_endpoint}"
                   IDP="{self.cognito_idp_url}">{self.env_vars['COGNITO_CLIENT_ID']}</cognitoClientId>
</registry_connection>
"""

        config_file.write_text(config_content)
        print(f"   Created: {config_file}\n")

    def generate_auth_config(self, username_key: str, password_key: str, filename: str) -> Path:
        """
        Generate authentication configuration file.

        Args:
            username_key: Environment variable key for username
            password_key: Environment variable key for password
            filename: Output filename

        Returns:
            Path to the created config file
        """
        config_file = self.config_dir / filename

        config_content = f"""# Generated es-auth.cfg for AWS Cognito authentication
# Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
user = {self.env_vars[username_key]}
password = {self.env_vars[password_key]}
"""

        config_file.write_text(config_content)
        return config_file

    def generate_auth_configs(self):
        """Generate authentication configuration files."""
        self.print_section("📝", "Generating authentication configuration files...")

        admin_config = self.generate_auth_config(
            "COGNITO_ADMIN_USERNAME",
            "COGNITO_ADMIN_PASSWORD",
            "es-admin-auth.cfg"
        )
        print(f"   Created: {admin_config}")

        writer_config = self.generate_auth_config(
            "COGNITO_WRITER_USERNAME",
            "COGNITO_WRITER_PASSWORD",
            "es-writer-auth.cfg"
        )
        print(f"   Created: {writer_config}\n")

    def generate_harvest_config(self, data_path: str = "/config/test-data/extracted"):
        """
        Generate harvest job configuration file from template.

        Args:
            data_path: Path to data directory as seen from inside Docker container
        """
        self.print_section("📝", "Generating harvest job configuration...")

        # Read the template file
        template_file = self.script_dir / "harvest-job-config.xml.template"
        if not template_file.exists():
            raise FileNotFoundError(f"Template file not found: {template_file}")

        template_content = template_file.read_text()
        template = Template(template_content)

        # Render template with Docker container paths
        rendered = template.render(
            auth_file="/config/es-writer-auth.cfg",
            registry_connection_file="/config/registry-connection.xml",
            data_path=data_path
        )

        # Write the generated config
        output_file = self.config_dir / "harvest-job-config.xml"
        output_file.write_text(rendered)
        print(f"   Created: {output_file}\n")

    def run_docker_container(self, purpose: str, command: list):
        """
        Run a Docker container for registry operations.

        Args:
            purpose: Description of what the container will do
            command: Command to run in the container
        """
        self.print_section("🚀", f"Running {purpose}...")
        print(f"   Image: {self.env_vars['REG_LOADER_IMAGE']}")
        print(f"\n📋 Container logs:")
        print("-" * 50)



        docker_cmd = [
            "docker", "run", "--rm", "-it",
            "-v", f"{self.config_dir}:/config",
            self.env_vars["REG_LOADER_IMAGE"]] + command


        self.run_command(docker_cmd, capture=False)
        print("-" * 50 + "\n")

    def cleanup_temp_files(self):
        """Clean up temporary authentication configuration files."""
        temp_files = [
            self.config_dir / "es-admin-auth.cfg",
            self.config_dir / "es-writer-auth.cfg",
        ]

        for temp_file in temp_files:
            if temp_file.exists():
                temp_file.unlink()

        print("   Cleaned up temporary auth config files")

    def download_and_extract_test_data(self, output_dir: Optional[Path] = None) -> Path:
        """
        Download and extract test data from TEST_DATA_URL (.tar.gz format).

        Args:
            output_dir: Directory to extract files to (defaults to config_dir/test-data)

        Returns:
            Path to the extracted data directory
        """
        test_data_url = self.env_vars.get("TEST_DATA_URL")
        if not test_data_url:
            raise ValueError("TEST_DATA_URL environment variable is not set")

        # Set default output directory
        if output_dir is None:
            output_dir = self.config_dir / "test-data"

        output_dir.mkdir(parents=True, exist_ok=True)

        # Determine filename from URL
        filename = test_data_url.split("/")[-1]
        download_path = output_dir / filename

        self.print_section("📥", f"Downloading test data from {test_data_url}")

        # Download file
        try:
            urllib.request.urlretrieve(test_data_url, download_path)
            print(f"   Downloaded to: {download_path}\n")
        except Exception as e:
            raise Exception(f"Failed to download test data: {e}")

        # Extract tar.gz archive
        self.print_section("📦", "Extracting test data...")
        extract_dir = output_dir / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)

        try:
            with tarfile.open(download_path, "r:gz") as tar:
                tar.extractall(path=extract_dir)
                print(f"   Extracted {len(tar.getmembers())} files to: {extract_dir}\n")

            return extract_dir

        except Exception as e:
            raise Exception(f"Failed to extract test data: {e}")

    def print_summary(self):
        """Print a summary of the initialization."""
        self.print_header("✅ Initialization complete!")

        print("Your AWS OpenSearch collection should now be populated with test data.\n")
        print("Configuration files:")
        print(f"   Registry connection: {self.config_dir / 'registry-connection.xml'}\n")
        print("Connection details:")
        print(f"   OpenSearch Endpoint: {self.opensearch_endpoint}")
        print(f"   Credentials Endpoint: {self.credentials_endpoint}")
        if self.collection_name:
            print(f"   Collection/Index: {self.collection_name}")
        print()

    def run(self) -> int:
        """
        Main execution method.

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            self.print_header("AWS Registry Initialization Script")

            self.print_section("🔐", "Note: Make sure you have AWS credentials configured")
            print()

            # Validation steps
            if not self.check_terraform_directory():
                return 1

            if not self.extract_terraform_outputs():
                return 1

            if not self.validate_required_env_vars():
                return 1

            if not self.check_docker_running():
                return 1

            # Setup
            self.load_env_file()
            self.generate_registry_config()
            self.generate_auth_configs()

            # Run Docker containers
            try:
                self.run_docker_container(
                   "registry-manager create-registry",
                   ["registry-manager", "create-registry",
                    "-auth", "/config/es-admin-auth.cfg", "-registry", "file:///config/registry-connection.xml"]
                )
            except subprocess.CalledProcessError:
                print("\n⚠️  OpenSearch indexes probably already created, skip that step\n")

            self.download_and_extract_test_data()
            self.generate_harvest_config()
            self.run_docker_container(
                "harvest",
                ["harvest" , "-c", "/config/harvest-job-config.xml"]
            )

            # Cleanup
            self.cleanup_temp_files()

            # Summary
            self.print_summary()

            return 0

        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user")
            return 130
        except Exception as e:
            print(f"\nError: {e}", file=sys.stderr)
            return 1


def main():
    """Entry point for the script."""
    initializer = RegistryInitializer()
    sys.exit(initializer.run())


if __name__ == "__main__":
    main()
