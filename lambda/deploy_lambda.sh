
#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e


ACCESS_KEY_FILENAME=accessKeys.csv
AWS_REGION=us-east-1


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

# Function to echo messages
echo_message() {
    echo "$1"
}

# If user provides the --upload flag, upload the package to AWS Lambda
if [ "$1" == "--upload" ]; then
    echo_message "Uploading the package to AWS Lambda..."
    echo_message "Checking for function name..."

    # Check if user has provided second argument which is function name to update
    if [ -z "$2" ]; then
        echo_message "Please provide the function name to update."
        echo_message "Usage: ./package_lambda.sh --upload <function_name>"
        echo_message "Be sure to provide the CSV file with AWS credentials, named accessKeys.csv, in the same directory."
        echo_message "You can also run a dry run by providing the --dryrun flag."
        echo_message "Example: ./package_lambda.sh --upload <function_name> --dryrun"
        exit 1
    fi

    # Check if the CSV file with AWS credentials is provided
    if [ ! -f "$ACCESS_KEY_FILENAME" ]; then
        echo_message "CSV file with AWS credentials not found. Please provide the CSV file. Exiting..."
        exit 1
    fi

    # Read the access key and secret access key from the CSV file
    ACCESS_KEY_ID=$(awk -F, 'NR==2 {print $1}' $ACCESS_KEY_FILENAME | xargs)
    SECRET_ACCESS_KEY=$(awk -F, 'NR==2 {print $2}' $ACCESS_KEY_FILENAME | xargs)

    # Export the AWS credentials as environment variables
    export AWS_ACCESS_KEY_ID=$ACCESS_KEY_ID
    export AWS_SECRET_ACCESS_KEY=$SECRET_ACCESS_KEY
    export AWS_DEFAULT_REGION=$AWS_REGION
    echo "Env variables:"
    echo $AWS_ACCESS_KEY_ID
    echo $AWS_SECRET_ACCESS_KEY
    echo $AWS_DEFAULT_REGION

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

    # Configure AWS CLI with the provided credentials and region
    aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID
    aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY
    aws configure set region $AWS_DEFAULT_REGION

    echo_message "Updating the Lambda function $2..."
    # if there is a --dryrun flag on the command line then just echo out the command
    if [ "$3" == "--dryrun" ]; then
        echo_message "dry run: aws lambda update-function-code --function-name $2 --zip-file fileb://lambda_package.zip"
    else
        # check basic lambda operation list functions
        echo_message "Listing functions..."
        aws lambda list-functions --debug

        echo_message "Executing command: aws lambda update-function-code --function-name $2 --zip-file fileb://lambda_package.zip"
        # get full path by using 'which' and put it in a variable to use in the command next
        # this is to ensure we are using the correct awscli for the user's environment
        aws_binary=$(which aws)
        $aws_binary lambda update-function-code --function-name $2 --zip-file fileb://lambda_package.zip --debug
    fi

    echo_message "Cleaning up before exiting..."

    # clean up the venv and crud left behind
    cleanup

fi