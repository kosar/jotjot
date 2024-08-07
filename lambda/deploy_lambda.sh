
#!/bin/bash

# Script: deploy_lambda.sh
# Description: Deploy a package to AWS Lambda
# Best practice is to store AWS credentials in the ~/.aws/credentials file
# If the credentials are not found in ~/.aws/credentials, the script will prompt for them
# Usage: ./deploy_lambda.sh --upload <function_name>
# Usage: ./deploy_lambda.sh --upload <function_name> --dryrun

AWS_REGION=us-east-1
VENV_NAME=lambda_deploy_env

# set -e will cause the script to exit if any command returns a non-zero exit code
set -e

# Trap errors and run cleanup. This will run the cleanup function if any command returns a non-zero exit code
trap cleanup ERR

# Function to echo messages
echo_message() {
    echo "$(basename "$0"): $1"
}

# Function to configure the aws cli 
function configure_aws_cli {
    echo_message "Configuring AWS CLI..."
    # Check if the accessKeys.csv file exists
    if [ ! -f "$ACCESS_KEY_FILENAME" ]; then
        echo_message "Please provide the accessKeys.csv file in the same directory."
        exit 1
    fi

    # Read the accessKeys.csv file (header row is skipped)
    tail -n +2 "$ACCESS_KEY_FILENAME" | while IFS=, read -r key_id secret_key; do
        # Trim whitespace and new lines
        key_id=$(echo "$key_id" | xargs)
        secret_key=$(echo "$secret_key" | xargs)
        
        # Set the AWS Access Key ID and Secret Access Key
        aws configure set aws_access_key_id "$key_id"
        aws configure set aws_secret_access_key "$secret_key"
        aws configure set region "$AWS_REGION"
    done
}

# Function to clean up in case of errors
function cleanup {
    echo_message "Central clean up: Cleaning up..."
    if [ -d "$VENV_NAME" ]; then
        echo_message "Central clean up: Deactivating and removing virtual environment $VENV_NAME..."
        source $VENV_NAME/bin/activate && deactivate || true
        rm -rf $VENV_NAME
    else
        echo_message "central clean up: Virtual environment $VENV_NAME not found."
    fi

    echo_message "central cleanup: Removing temporary files..."
    rm -rf requirements.txt __pycache__ *.dist-info *.egg-info ask_sdk_core ask_sdk_model ask_sdk_runtime bin certifi charset_normalizer dateutil idna requests six.py urllib3 pytz
}


# If user provides the --upload flag, upload the package to AWS Lambda
if [ "$1" == "--upload" ]; then
    echo_message "Uploading the package to AWS Lambda..."
    echo_message "Checking for function name..."

    # Check if user has provided second argument which is function name to update
    if [ -z "$2" ]; then
        echo_message "Please provide the function name to update."        
        echo_message "Usage: $0 --upload <function_name>"
        echo_message "If you do not have aws credentials in your home ./aws folder, provide AWS credentials in accessKeys.csv in same folder."
        echo_message "You can also run a dry run by providing the --dryrun flag."
        echo_message "Example: $0 --upload <function_name> --dryrun"
        exit 1
    fi

    # clean up any existing venv and crud left behind
    echo_message "Cleaning up before installing awscli..."  
    cleanup

    python3 -m venv $VENV_NAME # create a new virtual environment
    source $VENV_NAME/bin/activate

    # check if the user has the awscli installed globally already before installing it in the venv
    if ! command -v aws &> /dev/null
    then
        echo_message "awscli could not be found. Installing awscli..."
        pip install awscli
    fi

    # configure the aws cli
    # TODO: here we shouldl read from the accessKeys.csv file and set the aws credentials in the home folder ~/.aws/credentials
    # if the user has not provided the accessKeys.csv file in the same directory as the script we should prompt for it

    # check if there are credentials in the home folder under .aws/credentials where they are usually stored
    if [ -f ~/.aws/credentials ]; then
        echo_message "Using credentials from ~/.aws/credentials..."
    else
        echo_message "Using credentials from accessKeys.csv..."
        # TODO: this path is not yet fully tested. 
        configure_aws_cli
    fi

    echo_message "Updating the Lambda function $2..."
    # if there is a --dryrun flag on the command line then just echo out the command
    if [ "$3" == "--dryrun" ]; then
        echo_message "dry run: aws lambda update-function-code --function-name $2 --zip-file fileb://lambda_package.zip"
        # check basic lambda operation list functions
        echo_message "Listing functions to check credentials..."
        aws lambda list-functions
    else
        echo_message "***** Executing command: aws lambda update-function-code --function-name $2 --zip-file fileb://lambda_package.zip"
        sleep 3
        aws_binary=$(which aws)
        $aws_binary lambda update-function-code --function-name $2 --zip-file fileb://lambda_package.zip
        fi
    fi

    # Check the exit status of the AWS CLI command
    if [ $? -eq 0 ]; then
        echo "Lambda function code updated successfully."
    else
        echo "Failed to update Lambda function code."
        cleanup
        exit 1
    fi

    echo_message "Cleaning up before exiting..."
    cleanup
    exit 0

else
    echo_message "Please provide the --upload flag to upload the package to AWS Lambda."
    echo_message "Usage: ./deploy_lambda.sh --upload <function_name>"
    echo_message "Be sure to provide the CSV file with AWS credentials, named accessKeys.csv, in the same directory."
    echo_message "You can also run a dry run by providing the --dryrun flag."
    echo_message "If you have aws credentials in ~/.aws/credentials, they will be used and you do not need to provide accessKeys.csv."
    echo_message "Example: ./deploy_lambda.sh --upload <function_name> --dryrun"
    exit 1
fi