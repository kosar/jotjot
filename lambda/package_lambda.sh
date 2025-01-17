#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

# Define the Python version to use
PYTHON_VERSION=3.9
VENV_NAME=lambda_env

# Function to display messages
function echo_message {
    echo "==> $1"
}

# Function to clean up in case of errors
function cleanup {
    echo_message "central clean up: Cleaning up..."
    if [ -d "$VENV_NAME" ]; then
        source $VENV_NAME/bin/activate && deactivate || true
        rm -rf $VENV_NAME
    else
        echo_message "central clean up: Virtual environment $VENV_NAME not found."
    fi

    echo_message "central cleanup: Removing temporary files..."
    rm -rf requirements.txt __pycache__ *.dist-info *.egg-info ask_sdk_core ask_sdk_model ask_sdk_runtime bin certifi charset_normalizer dateutil idna requests six.py urllib3 pytz
}

# Trap errors and run cleanup
trap cleanup ERR

# Check if Homebrew is installed
if ! command -v brew &> /dev/null
then
    echo_message "Homebrew could not be found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install Python using Homebrew
echo_message "Installing Python $PYTHON_VERSION using Homebrew..."
brew install python@$PYTHON_VERSION

# Ensure the correct Python version is used
export PATH="/usr/local/opt/python@$PYTHON_VERSION/bin:$PATH"

# Create a virtual environment
echo_message "Creating virtual environment $VENV_NAME..."
python3 -m venv $VENV_NAME

# Activate the virtual environment
echo_message "Activating virtual environment $VENV_NAME..."
source $VENV_NAME/bin/activate

# Install dependencies
echo_message "Creating requirements.txt..."
echo "ask-sdk-core" > requirements.txt
# also add pytz to this
echo "pytz" >> requirements.txt
echo_message "Installing dependencies..."
# echo out the current requirements.txt file as we have it
cat requirements.txt
pip install -r requirements.txt -t .

# Package the Lambda function
echo_message "Packaging the Lambda function into lambda_package.zip..."
# skip any files that end in 'accessKeys.csv' as we don't want to package that up
zip -r lambda_package.zip * -x *accessKeys.csv

# Deactivate and remove the virtual environment
echo_message "Deactivating virtual environment..."
deactivate
echo_message "Removing virtual environment $VENV_NAME..."
rm -rf $VENV_NAME

# Clean up
echo_message "Cleaning up temporary files..."
rm -rf requirements.txt __pycache__ *.dist-info *.egg-info ask_sdk_core ask_sdk_model ask_sdk_runtime bin certifi charset_normalizer dateutil idna requests six.py urllib3 pytz

# Upload if requested
if [[ $1 == "--upload" ]]; then
    echo_message "Uploading the package to AWS Lambda..."
    ./deploy_lambda.sh --upload JotJotFunction
fi