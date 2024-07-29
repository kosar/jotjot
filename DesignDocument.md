# Alexa Skill and Lambda Function Interaction Diagram

## Overview
This document provides a detailed block diagram of the interaction between the Alexa skill "Daily Log Powered By Jot Jot" and the AWS Lambda function. It outlines where the handlers sit, and where the phrases and responses are managed.

## Diagram

```text
+---------------------+
|  Alexa Skill        |
|  (Developer Console)|
+---------------------+
          |
          v
+---------------------+
|  Interaction Model  |
|  - Intents          |
|  - Sample Utterances|
+---------------------+
          |
          v
+---------------------+
|  Distribution       |
|  - Example Phrases  |
+---------------------+
          |
          v
+---------------------+
|  Invocation Name    |
+---------------------+
          |
          v
+---------------------+          +---------------------+
|  Alexa Service      |          |  AWS Lambda         |
|  - Receives Request |          |  - Function         |
|  - Sends to Lambda  |          |  - Handlers         |
+---------------------+          +---------------------+
          |                                |
          v                                v
+---------------------+          +---------------------+
|  Request Envelope   |          |  lambda_function.py |
|  - User ID          |          |  - Handlers         |
|  - Intent           |          |    - LaunchRequest  |
|  - Slots            |          |    - LogActivity    |
+---------------------+          |    - HelpIntent     |
          |                      |    - StopIntent     |
          v                      |    - SessionEnded   |
+---------------------+          |    - Exception      |
|  AWS Lambda         |          +---------------------+
|  - Processes Request|                    |
|  - Interacts with   |                    v
|    DynamoDB         |          +---------------------+
|  - Sends Email via  |          |  DynamoDB           |
|    SES              |          |  - Logs Activity    |
+---------------------+          +---------------------+
          |
          v
+---------------------+
|  Response Envelope  |
|  - Speech Output    |
|  - Card             |
+---------------------+
          |
          v
+---------------------+
|  Alexa Service      |
|  - Sends Response   |
|    to Device        |
+---------------------+
          |
          v
+---------------------+
|  User's Alexa Device|
|  - Speaks Response  |
+---------------------+
```
## Detailed Components

### Alexa Skill (Developer Console)

#### Interaction Model
- **Intents**: Defines the actions the skill can perform.
- **Sample Utterances**: Example phrases users can say to invoke intents.

## Alexa Intents in Jot Jot

Alexa intents are the core building blocks of an Alexa Skill, acting as the bridge between what a user says and what the skill does in response. In essence, an intent represents a user's intention when they interact with Alexa. For example, in the "Daily Log Powered By Jot Jot" skill, intents such as `LogActivityIntent` are defined to capture and process user requests like logging daily activities. Each intent is associated with a set of sample utterances that guide Alexa's natural language understanding (NLU) to match the spoken words to the correct intent. This matching process is crucial for the skill to understand the wide variety of ways users might express the same request.

Once an intent is recognized, the request is forwarded to an AWS Lambda function, where intent handlers, such as `LogActivityIntentHandler`, take over. These handlers are Python functions defined in [`lambda/lambda_function.py`](jotjot/lambda/lambda_function.py) that execute the logic associated with each intent. For instance, when the `LogActivityIntent` is triggered, its handler interacts with AWS services like DynamoDB to log the user's activity. This seamless interaction between Alexa intents and AWS Lambda allows for a dynamic and responsive user experience. The Lambda function acts as the skill's brain, processing input, performing actions (like logging data or fetching reports), and generating spoken responses that Alexa delivers back to the user.

#### Custom Intents
## Custom Intent Handlers in the Lambda Function

The AWS Lambda function for the "Daily Log Powered By Jot Jot" Alexa Skill contains several custom intent handlers. These handlers are responsible for executing the logic associated with each custom intent defined in the Alexa skill's interaction model. Below are the details of all custom intent handlers implemented in the Lambda function.

### LogActivityIntentHandler

- **Purpose**: Handles the `LogActivityIntent` intent. It is responsible for logging user activities as specified by the user's voice command.
- **Functionality**:
  - Extracts the `utterance` slot value from the request, which represents the user's activity to be logged.
  - Interacts with AWS DynamoDB to store the activity log.
  - Generates a response confirming the activity has been logged or an error message if the operation fails.

### TODO: add remaining custom intent handler documentation heres

#### Built-in Intents
1. **AMAZON.HelpIntent**
   - Purpose: Provides help information to the user
   - Triggered by phrases like:
     - "help"
     - "what can I do"
     - "how does this work"

2. **AMAZON.CancelIntent**
   - Purpose: Cancels the current operation
   - Triggered by phrases like:
     - "cancel"
     - "never mind"

3. **AMAZON.StopIntent**
   - Purpose: Stops the skill and ends the session
   - Triggered by phrases like:
     - "stop"
     - "exit"

4. **AMAZON.FallbackIntent**
   - Purpose: Handles utterances that don't match any other intent
   - Provides a fallback response to help guide the user

#### System Intents
1. **LaunchRequest**
   - Purpose: Handles the initial launch of the skill
   - Triggered when the user says:
     - "Alexa, open Daily Log"

2. **SessionEndedRequest**
   - Purpose: Handles cleanup when the session ends
   - Triggered when:
     - The user says "exit"
     - The user is silent for too long
     - An error occurs

## Alexa Intents in Jot Jot

Alexa intents are the core building blocks of an Alexa Skill, acting as the bridge between what a user says and what the skill does in response. In essence, an intent represents a user's intention when they interact with Alexa. For example, in the "Daily Log Powered By Jot Jot" skill, intents such as `LogActivityIntent` are defined to capture and process user requests like logging daily activities. Each intent is associated with a set of sample utterances that guide Alexa's natural language understanding (NLU) to match the spoken words to the correct intent. This matching process is crucial for the skill to understand the wide variety of ways users might express the same request.

Once an intent is recognized, the request is forwarded to an AWS Lambda function, where intent handlers, such as `LogActivityIntentHandler`, take over. These handlers are Python functions defined in [`lambda/lambda_function.py`](jotjot/lambda/lambda_function.py) that execute the logic associated with each intent. For instance, when the `LogActivityIntent` is triggered, its handler interacts with AWS services like DynamoDB to log the user's activity. This seamless interaction between Alexa intents and AWS Lambda allows for a dynamic and responsive user experience. The Lambda function acts as the skill's brain, processing input, performing actions (like logging data or fetching reports), and generating spoken responses that Alexa delivers back to the user.

In this project, the design and implementation of Alexa intents and their handlers in the Lambda function are meticulously planned to ensure a natural and efficient interaction flow. By leveraging intents, the skill can accurately interpret user requests and provide meaningful responses, making daily activity logging with voice commands a reality.

### Intent Handlers in Lambda Function

The `lambda_function.py` file contains handlers for each of these intents:

- `LaunchRequestHandler`: Processes the LaunchRequest
- `LogActivityIntentHandler`: Processes the LogActivityIntent
- `HelpIntentHandler`: Processes the AMAZON.HelpIntent
- `CancelOrStopIntentHandler`: Processes both AMAZON.CancelIntent and AMAZON.StopIntent
- `SessionEndedRequestHandler`: Processes the SessionEndedRequest
- `CatchAllExceptionHandler`: Catches any unhandled exceptions

Each handler contains the logic to:
1. Determine if it can handle the incoming request
2. Process the request and interact with DynamoDB if necessary
3. Generate an appropriate response for Alexa to speak back to the user

#### Distribution
- **Example Phrases**: Phrases shown in the Alexa app to help users understand how to interact with the skill.
- **Invocation Name**: The name users say to invoke the skill.

### AWS Lambda Function

#### lambda_function.py
- **Handlers**
  - LaunchRequestHandler: Handles the launch of the skill.
  - LogActivityIntentHandler: Handles logging activities.
  - HelpIntentHandler: Provides help information.
  - CancelOrStopIntentHandler: Handles stop and cancel requests.
  - SessionEndedRequestHandler: Handles session end events.
  - CatchAllExceptionHandler: Catches and handles exceptions.
- **Interactions**
  - DynamoDB: Logs user activities.
  - SES: Sends email reports.

### Request and Response Flow
1. **User Interaction**: User speaks to their Alexa device.
2. **Alexa Service**: Receives the request and sends it to the AWS Lambda function.
3. **AWS Lambda Function**: Processes the request, interacts with DynamoDB and SES, and generates a response.
4. **Response**: The response is sent back to the Alexa service, which then delivers it to the user's device.

### Example Phrases and Responses

#### Example Phrases:
- "Alexa, ask Daily Log to log my activity"
- "Alexa, tell Daily Log I'm taking 650 of Tylenol"
- "Alexa, open Daily Log and show me yesterday's log"

#### Responses:
- "Welcome to Daily Log. You can log your activity by saying something like, I'm taking 650 of Tylenol now."
- "Got it, I logged: I'm taking 650 of Tylenol"
- "You can log your activity in Daily Log by saying something like, I'm taking 650 of Tylenol now, or I'm applying the balm. What would you like to do?"