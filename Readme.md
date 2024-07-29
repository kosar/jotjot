# Jot Jot - Your Personal Voice-Activated Logger Technology

<p align="center">
  <img src="./assets/DailyLog-SmallIcon.png" alt="Daily Log Icon">
</p>

Imagine never having to scramble for a pen and paper or unlock your phone to log your daily activities. With Jot Jot technology, your voice is all you need to keep track of everything from medication schedules to your latest workout achievements. It's like having a personal assistant dedicated solely to remembering the little details of your day, so you don't have to.

Jot Jot is an innovative voice-activated logging technology designed to simplify the process of recording daily activities and important information. The name "Jot Jot" was chosen to evoke the idea of quickly jotting down notes, but in this case, using voice commands instead of pen and paper. This technology aims to make logging as effortless and intuitive as speaking.

## Daily Log, The Alexa Skill Powered by Jot Jot
Daily Log is the specific Alexa skill that utilizes Jot Jot technology. It brings the power of voice-activated logging to Amazon Alexa devices, allowing users to easily keep track of their daily activities, medication schedules, workouts, and more. The name "Daily Log" clearly communicates its purpose: to maintain a daily record of user-specified events and activities.

By combining Jot Jot's advanced voice recognition and logging capabilities with Alexa's widespread accessibility, Daily Log offers users a seamless and hands-free way to maintain accurate records of their daily lives. This integration makes it easier than ever for users to stay organized and track important information without interrupting their daily routines.

This repository houses the technology behind Daily Log, the Alexa skill designed to make logging your daily activities as easy as speaking. Whether you're tracking medication, skincare routines, or any other daily task, Jot Jot technology offers a hands-free way to keep accurate records.

## Features

- **Voice-Activated Logging**: Log your activities using simple voice commands powered by Jot Jot technology.
- **Custom Intent Handlers**: Tailored responses for logging activities, getting help, and managing your logs, all made possible by Jot Jot.
- **AWS Integration**: Built on AWS to securely process and store your logs, ensuring they're accessible whenever you need them, thanks to Jot Jot's robust architecture.
- **Email Reports**: Get daily or on-demand reports sent directly to your own email, with easy setup through the Alexa app, facilitated by Jot Jot technology.

## Setting Up Daily Log on Your Alexa Device

To start using Daily Log (powered by Jot Jot technology) on your Alexa-enabled device, follow these steps:

1. Open the Alexa app on your mobile device.
2. Navigate to "Skills & Games".
3. Search for "Daily Log" and select it.
4. Click "Enable to Use".

### Working with Email Permissions

For Daily Log to send you daily reports via email, you need to grant permission to access your email address. Here's how:

- After enabling Daily Log, say, "Alexa, open Daily Log and send me a report."
- If permissions are not yet granted, Daily Log will guide you through the process, sending a card to your Alexa app to grant email access permissions.
- Follow the instructions on the card to grant the necessary permissions.

## How to Use Daily Log

Once enabled, activate Daily Log by saying, "Alexa, open Daily Log." You can then log activities by stating your activity, such as:

- "I took my morning vitamins."
- "Log that I did my morning workout."
- "I'm applying my night skincare."

The voice interface will confirm back what it heard you say and then persist that to a log. If you have email permissions set up, you will see a daily log of your activities in your inbox, allowing you to maintain history of your logs. 

## Minimal Retention Principle
Minimal Retention is an important aspect of Daily Log. Our intention is to keep only about a week of historical logs within the application itself. This deliberate design choice allows users to have control over their own information. By relying on email reports as the long-term storage solution, users can maintain a historical record of their logs in their own email inboxes. This approach ensures that users have easy access to their logs while also respecting their privacy and data ownership.
