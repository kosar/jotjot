#!/bin/bash

# AWS CLI Setup Script
#
# Usage:
#   ./setup_aws_cli.sh [OPTIONS]
#
# Options:
#   --help     Show this help message and exit
#   --dry-run  Perform a dry run without making any changes
#
# This script sets up the AWS CLI on macOS, including:
# - Installing Homebrew if not present
# - Installing Python3 if not present
# - Creating a Python virtual environment
# - Installing AWS CLI
# - Setting up AWS credentials
# - Testing AWS CLI authentication
# - Creating an activation script for easy environment setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    color=$1
    message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to show help message
show_help() {
    cat << EOF
Usage: ./setup_aws_cli.sh [OPTIONS]

Options:
  --help     Show this help message and exit
  --dry-run  Perform a dry run without making any changes

This script sets up the AWS CLI on macOS, including:
- Installing Homebrew if not present
- Installing Python3 if not present
- Creating a Python virtual environment
- Installing AWS CLI
- Setting up AWS credentials
- Testing AWS CLI authentication
- Creating an activation script for easy environment setup

AWS Credential Setup:
1. Obtain your AWS Access Key ID and Secret Access Key:
   - Sign in to the AWS Management Console.
   - In the navigation bar, choose your account name, and then choose My Security Credentials.
   - Choose the Access keys (access key ID and secret access key) section.
   - Choose Create New Access Key, and then download the key file or copy the keys.
2. Run 'aws configure' when prompted by this script to enter your credentials.

For more detailed information, visit:
https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html
EOF
}

# Parse command line arguments
DRY_RUN=false
for arg in "$@"
do
    case $arg in
        --help)
        show_help
        exit 0
        ;;
        --dry-run)
        DRY_RUN=true
        print_color $YELLOW "Running in dry run mode. No changes will be made."
        ;;
    esac
done

# Install Homebrew if not found
if ! command_exists brew; then
    print_color $YELLOW "Homebrew not found. Installing Homebrew..."
    if [ "$DRY_RUN" = false ]; then
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    else
        print_color $YELLOW "[DRY RUN] Would install Homebrew"
    fi
else
    print_color $GREEN "Homebrew is already installed."
fi

# Check for Python
if ! command_exists python3; then
    print_color $YELLOW "Python3 not found. Installing via Homebrew..."
    if [ "$DRY_RUN" = false ]; then
        brew install python
    else
        print_color $YELLOW "[DRY RUN] Would install Python3 via Homebrew"
    fi
else
    print_color $GREEN "Python3 is already installed."
fi

# Create a directory for AWS CLI
AWS_DIR="$HOME/aws_cli_env"
if [ ! -d "$AWS_DIR" ]; then
    print_color $YELLOW "Creating directory for AWS CLI environment..."
    if [ "$DRY_RUN" = false ]; then
        mkdir -p "$AWS_DIR"
    else
        print_color $YELLOW "[DRY RUN] Would create directory: $AWS_DIR"
    fi
else
    print_color $GREEN "AWS CLI directory already exists."
fi

# Create and activate virtual environment
print_color $YELLOW "Creating and activating virtual environment..."
if [ "$DRY_RUN" = false ]; then
    python3 -m venv "$AWS_DIR/venv"
    source "$AWS_DIR/venv/bin/activate"
else
    print_color $YELLOW "[DRY RUN] Would create and activate virtual environment in $AWS_DIR/venv"
fi

# Install AWS CLI
print_color $YELLOW "Installing AWS CLI..."
if [ "$DRY_RUN" = false ]; then
    pip install awscli
else
    print_color $YELLOW "[DRY RUN] Would install AWS CLI using pip"
fi

# Set up AWS credentials
print_color $YELLOW "Setting up AWS credentials..."
print_color $YELLOW "Please have your AWS Access Key ID and Secret Access Key ready."
if [ "$DRY_RUN" = false ]; then
    aws configure
else
    print_color $YELLOW "[DRY RUN] Would run 'aws configure' to set up credentials"
fi

# Test AWS CLI installation
print_color $YELLOW "Testing AWS CLI installation..."
if [ "$DRY_RUN" = false ]; then
    aws --version
else
    print_color $YELLOW "[DRY RUN] Would test AWS CLI by running 'aws --version'"
fi

# Test AWS CLI authentication
print_color $YELLOW "Testing AWS CLI authentication..."
if [ "$DRY_RUN" = false ]; then
    if aws s3 ls &> /dev/null; then
        print_color $GREEN "AWS CLI authentication successful!"
    else
        print_color $RED "AWS CLI authentication failed. Please check your credentials and try again."
        print_color $YELLOW "You can update your credentials by running 'aws configure'"
        exit 1
    fi
else
    print_color $YELLOW "[DRY RUN] Would test AWS CLI authentication by running 'aws s3 ls'"
fi

# Create activation script
ACTIVATE_SCRIPT="$AWS_DIR/activate_aws_cli.sh"
print_color $YELLOW "Creating activation script..."
if [ "$DRY_RUN" = false ]; then
    cat << EOF > "$ACTIVATE_SCRIPT"
#!/bin/bash
source "$AWS_DIR/venv/bin/activate"
export AWS_CLI_ACTIVE=true
print_color() {
    color=\$1
    message=\$2
    echo -e "\${color}\${message}\${NC}"
}
print_color '\033[0;32m' "AWS CLI environment activated. Run 'deactivate' to exit."
EOF
    chmod +x "$ACTIVATE_SCRIPT"
else
    print_color $YELLOW "[DRY RUN] Would create activation script: $ACTIVATE_SCRIPT"
fi

print_color $GREEN "AWS CLI installation and setup complete!"
print_color $YELLOW "To activate the AWS CLI environment, run:"
print_color $NC "source $ACTIVATE_SCRIPT"
print_color $YELLOW "To deactivate, simply run 'deactivate' or close the terminal."

# Guidance on credentials and usage
print_color $YELLOW "\nImportant Notes:"
print_color $NC "1. Your AWS credentials are stored in ~/.aws/credentials"
print_color $NC "2. To update your credentials, run 'aws configure' again"
print_color $NC "3. For security, never share your AWS credentials"
print_color $NC "4. To use a specific profile, set the AWS_PROFILE environment variable:"
print_color $NC "   export AWS_PROFILE=your_profile_name"
print_color $NC "5. To test your setup, try running: aws s3 ls"
print_color $NC "6. For more information, visit: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html"

# Deactivate virtual environment if not in dry run mode
if [ "$DRY_RUN" = false ]; then
    deactivate
fi