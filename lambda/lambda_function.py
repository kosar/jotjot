import os
import logging
import json
import boto3
import time
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr  # Import conditions module
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_model import Response
from ask_sdk_model.ui import AskForPermissionsConsentCard
from ask_sdk_model.services import ServiceException
from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.api_client import DefaultApiClient
from ask_sdk_model.services.ups import UpsServiceClient
from datetime import datetime, timedelta, timezone
from ask_sdk_core.exceptions import AskSdkException

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')
table_name = 'JotJotLogs'

# Get the skill name from an environment variable, with a default fallback
SKILL_NAME = os.environ.get('SKILL_NAME', 'Daily Log')

# Add these environment variables
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'your_verified_email@example.com')

def emit_maintenance_metrics(dynamodb_table_names, lambda_function_names):
    metrics = {}
    logger.info("Starting maintenance metrics collection")
    overall_start_time = time.time()

    # Collect DynamoDB metrics
    dynamodb_client = boto3.client('dynamodb')
    cloudwatch = boto3.client('cloudwatch')
    for table_name in dynamodb_table_names:
        try:
            response = dynamodb_client.describe_table(TableName=table_name)
            metrics[f'DynamoDB_{table_name}_ItemCount'] = response['Table']['ItemCount']

            # Number of unique new rows added to dynamoDB tables (indicates activity)
            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/DynamoDB',
                MetricName='ConsumedWriteCapacityUnits',
                Dimensions=[{'Name': 'TableName', 'Value': table_name}],
                StartTime=datetime.now(timezone.utc) - timedelta(days=1),
                EndTime=datetime.now(timezone.utc),
                Period=86400,
                Statistics=['Sum']
            )
            metrics[f'DynamoDB_{table_name}_ConsumedWriteCapacityUnits'] = response['Datapoints'][0]['Sum'] if response['Datapoints'] else 0

        except ClientError as e:
            logger.error(f"Failed to get DynamoDB metrics for table {table_name}: {e.response['Error']['Message']}")
            metrics[f'DynamoDB_{table_name}_ItemCount'] = 'Error'

    # Collect Lambda metrics for specific functions
    cloudwatch = boto3.client('cloudwatch')
    for function_name in lambda_function_names:
        try:
            start_time = time.time()
            # Duration metrics
            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Duration',
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=datetime.now(timezone.utc) - timedelta(days=1),
                EndTime=datetime.now(timezone.utc),
                Period=86400,
                Statistics=['Average', 'Maximum', 'Sum']
            )
            metrics[f'Lambda_{function_name}_AverageDuration'] = response['Datapoints'][0]['Average'] if response['Datapoints'] else 0
            metrics[f'Lambda_{function_name}_MaximumDuration'] = response['Datapoints'][0]['Maximum'] if response['Datapoints'] else 0
            metrics[f'Lambda_{function_name}_TotalDuration'] = response['Datapoints'][0]['Sum'] if response['Datapoints'] else 0
            logger.info(f"Time taken for last day Duration count: {time.time() - start_time} seconds")

            start_time = time.time()

            # Invocation count for the last day
            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Invocations',
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=datetime.now(timezone.utc) - timedelta(days=1),
                EndTime=datetime.now(timezone.utc),
                Period=86400,
                Statistics=['Sum']
            )
            last_day_invocations = response['Datapoints'][0]['Sum'] if response['Datapoints'] else 0
            metrics[f'Lambda_{function_name}_InvocationCount'] = last_day_invocations
            logger.info(f"Time taken for last day invocation count: {time.time() - start_time} seconds")

            # Invocation counts for the previous 3 days
            seven_day_invocations = []
            for i in range(1, 4):
                start_time = time.time()
                response = cloudwatch.get_metric_statistics(
                    Namespace='AWS/Lambda',
                    MetricName='Invocations',
                    Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                    StartTime=datetime.now(timezone.utc) - timedelta(days=i+1),
                    EndTime=datetime.now(timezone.utc) - timedelta(days=i),
                    Period=86400,
                    Statistics=['Sum']
                )
                seven_day_invocations.append(response['Datapoints'][0]['Sum'] if response['Datapoints'] else 0)
                logger.info(f"Time taken for day {i} invocation count: {time.time() - start_time} seconds")

            # Calculate the average invocation count for the previous 7 days
            average_seven_day_invocations = sum(seven_day_invocations) / len(seven_day_invocations) if seven_day_invocations else 0
            metrics[f'Lambda_{function_name}_Average7DayInvocationCount'] = average_seven_day_invocations

            # Compare last day's invocation count with the average of the previous 7 days
            if isinstance(average_seven_day_invocations, float):
                average_seven_day_invocations = f"{average_seven_day_invocations:.2f}"
            metrics[f'Lambda_{function_name}_InvocationComparison'] = (
                f"Last day: {last_day_invocations}, Average of previous 7 days: {average_seven_day_invocations}"
            )

        except ClientError as e:
            logger.error(f"Failed to get CloudWatch Logs metrics for function {function_name}: {e.response['Error']['Message']}")
            metrics[f'Lambda_{function_name}_Metrics'] = 'Error'

    # Emit metrics
    admin_email = os.getenv('admin_email')
    if admin_email:
        try:
            body = """
            <html>
            <head>
                <style>
                    table { font-family: Arial, sans-serif; border-collapse: collapse; width: 100%; }
                    th, td { border: 1px solid #dddddd; text-align: left; padding: 8px; }
                    th { background-color: #f2f2f2; }
                </style>
            </head>
            <body>
                <h2>Daily Maintenance Metrics</h2>
                <table>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
            """
            for key, value in metrics.items():
                if isinstance(value, float):
                    value = f"{value:.2f}"
                body += f"""
                    <tr>
                        <td>{key}</td>
                        <td>{value}</td>
                    </tr>
                """
            # Add the overall time taken for maintenance metrics collection
            overall_time_taken = time.time() - overall_start_time
            body += f"""
                <tr>
                    <td>Maintenance Task Time Elapsed</td>
                    <td>{overall_time_taken:.2f} seconds</td>
                </tr>
            """            
            body += """
                </table>
            </body>
            </html>
            """
            DailyReportHandler.send_email(SENDER_EMAIL, admin_email, "Daily Maintenance Metrics", body)
            logger.info(f"Metrics emailed to {admin_email}")
        except Exception as e:
            logger.error(f"Failed to send metrics email: {str(e)}")
    else:
        logger.info("Admin email not set, logging metrics")
        for key, value in metrics.items():
            if isinstance(value, float):
                value = f"{value:.2f}"
            logger.info(f"{key}: {value}")

    logger.info("Maintenance metrics collection completed")
    logger.info(f"Overall time taken for maintenance metrics collection: {time.time() - overall_start_time:.2f} seconds")

def get_user_email_preference(user_id):
    try:
        table = dynamodb.Table('jotjot_UserEmailPreferences')
        # check if we got a table back else let's end early
        if not table:
            logger.error(f"Table not found: jotjot_UserEmailPreferences")
            return False
        response = table.get_item(Key={'user_id': user_id})
        if 'Item' in response:
            return response['Item'].get('email_summary_enabled', False)
        else:
            return False
    except Exception as e:
        logger.error(f"Error fetching email preference for user {user_id}: {str(e)}")
        return False

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # DynamoDB setup
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('jotjot_UserEmailPreferences')
        
        # Get user ID
        user_id = handler_input.request_envelope.context.system.user.user_id
        
        # Attempt to retrieve the user's entry from DynamoDB
        response = table.get_item(Key={'user_id': user_id})
        
        if 'Item' not in response:
            # User is new, create entry in DynamoDB
            table.put_item(Item={
                'user_id': user_id,
                'email_summary_enabled': False,
                'first_seen': datetime.utcnow().isoformat()
            })
            # Full welcome message for first-time users
            speak_output = f"Welcome to {SKILL_NAME}. Log anything by starting with 'Log that...' For example, you can say 'Open Daily Log, and log that I am taking my vitamins'."
        else:
            # Shorter message for repeat users
            speak_output = "Welcome back. What are you doing?"
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("Log something starting with 'I am...' or ask for help.")
                .set_should_end_session(False)
                .response
        )

class LogActivityIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("LogActivityIntent")(handler_input)

    def handle(self, handler_input):
        user_id = handler_input.request_envelope.session.user.user_id
        full_utterance = handler_input.request_envelope.request.intent.slots["utterance"].value
        timestamp = datetime.now().isoformat()

        parsed_data = self.basic_parse(full_utterance)        
        
        try:
            table = dynamodb.Table(table_name)
            item = {
                'user_id': user_id,
                'timestamp': timestamp,
                'date': timestamp.split('T')[0],  # Extract date from ISO format
                'utterance': full_utterance,
                'parsed_data': json.dumps(parsed_data) # experimental storing of parsed data to attempt to create some structure for later querying
            }
            response = table.put_item(Item=item)
            logger.info(f"Successfully logged to DynamoDB: {json.dumps(response)}")
            
            speak_output = f"Got it! Here is what I logged: {full_utterance}"

            try:
                # update email permissions for this user given the handler_input
                logger.info("LogActivityIntentHandler: Attempting to update email permissions")
                update_status = self.update_email_permissions(handler_input)
                logger.info(f"LogActivityIntentHandler: Email permission update status: {update_status}")
            except Exception as e:
                logger.error(f"LogActivityIntentHandler: Error updating email permissions: {str(e)}")
                # keep going even if email permission update fails, logging will catch and fix it later
                # TODO: is this a good place to remind the user to enable their email permissions?
            
            # Check if the user has set up email preferences 
            # TODO: refactor this to a separate function that is not annoying every time asking for email permission
            if False:
                email_preference = get_user_email_preference(user_id)
                if not email_preference:
                    speak_output += " By the way, if you'd like to receive daily report emails, please say 'use my email' to grant permission."
  
        except ClientError as e:
            logger.error(f"Error logging to DynamoDB: {e.response['Error']['Message']}")
            speak_output = f"Sorry, there was an error logging your activity. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

    def get_user_email(self, handler_input):
        try:
            email = handler_input.service_client_factory.get_ups_service().get_profile_email()
            return email
        except Exception as e:
            logger.warn(f"Error getting user's email: {str(e)}")
            return None

    def basic_parse(self, utterance):
        words = utterance.lower().split()
        parsed = {}
        for i, word in enumerate(words):
            if word.isdigit():
                parsed['amount'] = word
                if i+1 < len(words):
                    parsed['unit'] = words[i+1]
            elif word in ['taking', 'applying', 'took', 'applied']:
                parsed['action'] = word
            elif word not in ['i\'m', 'i', 'am', 'the', 'a', 'an']:
                parsed['substance'] = word
        
        # for development purposes, emit a detailed log of the parsed data here
        logger.info(f"Parsed data: {parsed}")

        return parsed
    
    def update_email_permissions(self, handler_input):
        logger.info("Updating email permissions for user")

        # Get user ID
        user_id = handler_input.request_envelope.context.system.user.user_id
        logger.info(f"User ID: {user_id}")

        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('jotjot_UserEmailPreferences')  # Move to an Env var

        try:
            # Attempt to get the user's email
            service_client_factory = handler_input.service_client_factory
            ups_service = service_client_factory.get_ups_service()
            email = ups_service.get_profile_email()
            
            logger.info(f"Successfully retrieved user email: {email}")
            update_expression = 'SET email_summary_enabled = :val, email = :email, last_updated_email_permissions = :timestamp'
            expression_values = {':val': True, ':email': email, ':timestamp': datetime.now(timezone.utc).isoformat()}
            
        except AskSdkException as ask_exception:
            logger.info(f"Error getting user email: {str(ask_exception)}")
            update_expression = 'SET email_summary_enabled = :val, email = :email, last_updated_email_permissions = :timestamp'
            expression_values = {':val': False, ':email': '', ':timestamp': datetime.now(timezone.utc).isoformat()}

        try:
            # Perform the DynamoDB update
            response = table.update_item(
                Key={'user_id': user_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ReturnValues="UPDATED_NEW"
            )

            logger.info(f"DynamoDB update response: {response}")
            logger.info(f"Updated email_summary_enabled to: {expression_values[':val']}")
            logger.info(f"Updated email to: {expression_values[':email']}")
            logger.info(f"Updated last_updated_email_permissions to: {expression_values[':timestamp']}")

        except ClientError as e:
            logger.info(f"Error updating DynamoDB: {str(e)}")
        except Exception as e:
            logger.info(f"Unexpected error: {str(e)}")

        logger.info("Email permission update process completed.")

class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = f"You can log your activity in {SKILL_NAME} by saying something like, I'm taking 650 of Tylenol now, or I'm applying the balm. What would you like to do?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        speak_output = f"Thank you for using {SKILL_NAME}. Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # Any cleanup logic goes here
        return handler_input.response_builder.response

class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.error(exception, exc_info=True)

        speak_output = f"Sorry, I had trouble doing what you asked. Please try again or ask for help in {SKILL_NAME}."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class DailyReportHandler:
    @staticmethod
    def send_daily_report(dry_run=False, user_id=None):
        try:
            # Scan the email preferences table for users who have enabled email summaries
            preferences_table = dynamodb.Table('jotjot_UserEmailPreferences')
            
            if user_id:  # If user_id is provided, fetch email preference for that user
                response = preferences_table.get_item(Key={'user_id': user_id})
                eligible_users = [response['Item']] if 'Item' in response and response['Item'].get('email_summary_enabled', False) else []
            else:  # Otherwise, fetch all users with email summaries enabled
                response = preferences_table.scan(
                    FilterExpression=boto3.dynamodb.conditions.Attr('email_summary_enabled').eq(True)
                )
                eligible_users = response['Items']
            
            logger.info(f"send_daily_report: Found {len(eligible_users)} users with email summaries enabled")
            
            # Loop through eligible users
            for user in eligible_users:
                user_id = user['user_id']
                email = user.get('email')
                if not email:
                    logger.error(f"send_daily_report: User {user_id} has no email address set up")
                    continue
                
                # Fetch logs for the user from yesterday
                yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                response_items = DailyReportHandler.get_all_user_log_entries_for_date(yesterday, user_id=user_id)
                logger.info(f"send_daily_report: Found {len(response_items)} logs for user {user_id} on {yesterday}")
                
                # If there are logs, send the email report
                if response_items:
                    logger.info(f"send_daily_report: Creating daily report for {yesterday} to {email} consisting of {len(response_items)} items")
                    body = DailyReportHandler.create_html_email_body(yesterday, response_items, SKILL_NAME, "https://github.com/kosar/jotjot/issues/new")
                    
                    if dry_run:
                        status_email = True
                        logger.info(f"send_daily_report (dryrun): Skipping email send for email {email}")
                    else:
                        status_email = DailyReportHandler.send_email(SENDER_EMAIL, email, f"{SKILL_NAME} Report", body)
                    
                    if not status_email:
                        logger.error(f"send_daily_report: Failed to send daily report to {email} for user {user_id}")
                    else:
                        if not dry_run:
                            logger.info(f"send_daily_report: Successfully sent daily report to {email}")
                        else:
                            logger.info(f"send_daily_report (dryrun): Successful dry run to: {email}")
                            logger.info(f"send_daily_report (dryrun): body: {body}")
                            
        except Exception as e:
            logger.error(f"send_daily_report: Exception. Failed to send daily report: {str(e)}")

    @staticmethod
    def get_all_user_log_entries_for_date(date, user_id=None):
        try:
            table = dynamodb.Table(table_name)
            key_condition = Key('date').eq(date)
            
            query_params = {
                'IndexName': 'date-index',
                'KeyConditionExpression': key_condition
            }
            
            if user_id:
                query_params['FilterExpression'] = Attr('user_id').eq(user_id)  # Use FilterExpression for user_id
            
            response = table.query(**query_params)
            items = response['Items']
            logger.info(f"get_all_user_log_entries_for_date: Found {len(items)} log entries for date {date}")
            try:
                items.sort(key=lambda x: x['timestamp'])  # Added sorting by timestamp
            except Exception as e:
                logger.error(f"get_all_user_log_entries_for_date: Error sorting items by timestamp: {str(e)}")
                # continuing even if sorting fails

            return items
        except Exception as e:
            logger.error(f"get_all_user_log_entries_for_date: Error fetching log entries for date {date}: {str(e)}")
            return []

    @staticmethod
    def get_all_user_log_entries(user_id=None, table_name='JotJotLogs'):
        try:
            table = dynamodb.Table(table_name)
            # get all the entries for that table right now
            response = table.scan()

            # return the length of the items in the response
            logger.info (f"Number of response['Items']: {len(response['Items'])}")
            return response['Items']

        except Exception as e:
            logger.error(f"Error fetching log entries: {str(e)}")
            return []

    @staticmethod
    def get_user_email_address(user_id):
        try:
            table = dynamodb.Table('jotjot_UserEmailPreferences')
            response = table.get_item(Key={'user_id': user_id})
            if 'Item' in response:
                return response['Item'].get('email')
            else:
                return None
        except Exception as e:
            logger.error(f"Error fetching email for user {user_id}: {str(e)}")
            return None

    @staticmethod
    def send_email(source, to_address, subject, body):
        try:
            source_with_name = f"Alexa Skill - {SKILL_NAME} - <{source}>"
            response = ses.send_email(
                Source=source_with_name,
                Destination={'ToAddresses': [to_address]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Html': {'Data': body}}
                }
            )
            logger.info(f"Email sent to {to_address}! Message ID: {response['MessageId']}")
            logger.info(f"Response in send_email: {response}")
            return response['MessageId']
        except ClientError as e:
            logger.error(f"An error occurred sending email to {to_address}: {e.response['Error']['Message']}")
            return False
    
    @staticmethod
    def create_html_email_body(date, logs, skill_name, github_issues_link):
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: #f8f9fa; padding: 10px; text-align: center; }}
                .content {{ margin: 20px; }}
                .footer {{ background-color: #f8f9fa; padding: 10px; text-align: center; font-size: 12px; }}
                .log-entry {{ margin-bottom: 10px; }}
                .timestamp {{ font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>{skill_name} Daily Report</h2>
            </div>
            <div class="content">
                <p>Hello! Here's a summary of your activity from {date}:</p>
                <ul>
        """
        for item in logs:
            timestamp = item['timestamp']
            parsed_timestamp = datetime.fromisoformat(timestamp)
            formatted_timestamp = parsed_timestamp.strftime('%B %d, %Y at %I:%M %p')
            body += f"""
                <li class="log-entry">
                    <span class="timestamp">{formatted_timestamp}:</span> {item['utterance']}
                </li>
            """
        body += f"""
                </ul>
                <p>To disable these reports from {skill_name}, say 'Disable sending daily reports email' when using the skill.'</p>
            </div>
            <div class="footer">
                <p>If you encounter any issues, please <a href="{github_issues_link}">file an issue</a>.</p>
            </div>
        </body>
        </html>
        """
        return body

class StopReportsIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("StopReportsIntent")(handler_input)

    def handle(self, handler_input):
        user_id = handler_input.request_envelope.session.user.user_id
        speak_output=""

        try:
            logger.info(f"StopReportsIntentHandler - User ID: {user_id}")
            if get_user_email_preference(user_id):
                table = dynamodb.Table('jotjot_UserEmailPreferences')
                response = table.update_item(
                    Key={'user_id': user_id},
                    UpdateExpression="SET email_summary_enabled = :val",
                    ExpressionAttributeValues={':val': False},
                    ReturnValues="UPDATED_NEW"
                )
                speak_output = "I've stopped sending daily reports to your email. You can always ask me to start sending them again by saying 'send daily log reports to my email'."
                logger.info(f"DynamoDB Response Object: {json.dumps(response)}")

        except ClientError as e:
            logger.error(f"Error updating DynamoDB: {e.response['Error']['Message']}")
            speak_output = "Sorry, there was an error processing your request. Please try again later."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class GrantEmailPermissionIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("GrantEmailPermissionIntent")(handler_input)

    def handle(self, handler_input):
        user_id = handler_input.request_envelope.session.user.user_id
        
        try:
            logger.info(f"GrantEmailPermissionIntentHandler - User ID: {user_id}")
            
            # Check if the user has granted permission to access their email already using our own functions to check DynamoDB
            email_preference = get_user_email_preference(user_id)
            if email_preference:
                logger.info("Incorrect Detection Of Intent -- Email preference already set up!")
                return (
                    handler_input.response_builder
                        .speak("Hmm, I'm not sure what you're asking for. Let's try something else.")
                        .set_should_end_session(False)  # Keep the session open for further interaction
                        .response
                )

            # Check if the user has granted permission to access their email already using the Alexa API
            service_client_factory = handler_input.service_client_factory
            if not service_client_factory:
                logger.error("ServiceClientFactory not available")
                return self.handle_permission_required(handler_input)

            ups_service = service_client_factory.get_ups_service()
            
            try:
                logger.info("Getting email from profile")
                email = ups_service.get_profile_email()
                logger.info(f"Email: {email}")
                if not email:
                    logger.info("Email is None, requesting permission")
                    return self.handle_permission_required(handler_input)

                # check if it's a valid email address in the email field before persisting to DynamoDB
                if email and '@' in email:
                    # Persist email preference
                    table = dynamodb.Table('jotjot_UserEmailPreferences')
                    response = table.put_item(
                        Item={
                            'user_id': user_id,
                            'email': email,
                            'email_summary_enabled': True
                        }
                    )
                    logger.info(f"Successfully set up email preference: {json.dumps(response)}")
                    speak_output = "Great! I've set up daily log emails for you."

            except Exception as se:
                logger.error(f"Exception when getting email: {str(se)}")
                return self.handle_permission_required(handler_input)
       
        except Exception as e:
            logger.error(f"GrantEmailPermissionIntentHandler: Error setting up email preference for user {user_id}\n{str(e)}")
            speak_output = "I'm sorry, there was an error setting up your email preference. Please try again later."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

    def handle_permission_required(self, handler_input):
        permissions = ["alexa::profile:email:read"]
        return (
            handler_input.response_builder
                .speak("To send you daily reports, I need permission to access your email address. I've sent a card to your Alexa app to grant this permission.")
                .set_card(AskForPermissionsConsentCard(permissions=permissions))
                .response
        )

sb = CustomSkillBuilder(api_client=DefaultApiClient())
# sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(LogActivityIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(GrantEmailPermissionIntentHandler())
sb.add_request_handler(StopReportsIntentHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

def lambda_handler(event, context):
    # logger.info out the intent name for debugging
    if 'request' in event and 'intent' in event['request']:
        logger.info(f"Intent name: {event['request']['intent']['name']}")

    if event.get('daily_report'):
        dry_run_flag = event.get('dry_run', False)
        if dry_run_flag:
            logger.info('Dry run flag enabled for daily report event')
        DailyReportHandler.send_daily_report(dry_run=dry_run_flag)
        logger.info('Daily report event handled.', extra={'event': event})
        return {'statusCode': 200, 'body': 'Daily report process completed'}
    elif event.get('email_summary_flag'):
        email_summary_enabled = get_user_email_preference(event['user_id'])
        logger.info(f"Email summary enabled flag: {email_summary_enabled}")
        return {'statusCode': 200, 'body': f'Email summary enabled: {email_summary_enabled}'}
    elif event.get('daily_maintenance'):
        # TODO: fetch these next two constants from the event which will be supplied in eventbridge schedule payload
        dynamodb_table_names = event.get('dynamodb_table_names', ['jotjot_UserEmailPreferences', 'JotJotLogs'])
        lambda_function_names = event.get('lambda_function_names', ['JotJotFunction'])
        logger.info('dynamodb_table_names: ' + str(dynamodb_table_names) + ' lambda_function_names: ' + str(lambda_function_names))
        emit_maintenance_metrics(dynamodb_table_names, lambda_function_names)
        logger.info('Daily maintenance task event handled.', extra={'event': event})
        return {'statusCode': 200, 'body': 'Daily maintenance task process completed.'}
    elif event.get('test_user_id_email_report'):
        user_id = event.get('user_id')
        if user_id:
            logger.info(f"test_user_id_email_report: Sending daily report for user_id: {user_id}")
            DailyReportHandler.send_daily_report(user_id=user_id)
            return {'statusCode': 200, 'body': f'Daily report sent for user_id: {user_id}'}
        else:
            logger.error('test_user_id_email_report: user_id not provided in the event')
            return {'statusCode': 400, 'body': 'user_id not provided'}
    else:
        logger.info('Normal skill invocation.')

    return sb.lambda_handler()(event, context) # Call the SkillBuilder instance to route the request