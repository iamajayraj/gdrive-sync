# Google Drive Service Account Setup Guide

This guide will help you set up a Google Drive service account for the Google Drive Sync application.

## What is a Service Account?

A service account is a special type of Google account that belongs to your application rather than to an individual end user. Your application calls Google APIs on behalf of the service account, so users aren't directly involved.

## Advantages of Service Accounts

- No browser-based authentication flow required
- Can be used in headless environments
- No user interaction needed
- More suitable for automated processes

## Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top of the page
3. Click on "New Project"
4. Enter a name for your project and click "Create"
5. Wait for the project to be created and then select it from the project dropdown

## Step 2: Enable the Google Drive API

1. In the Google Cloud Console, go to the "APIs & Services" > "Library" section
2. Search for "Google Drive API"
3. Click on the "Google Drive API" result
4. Click "Enable"

## Step 3: Create a Service Account

1. In the Google Cloud Console, go to the "APIs & Services" > "Credentials" section
2. Click "Create Credentials" and select "Service account"
3. Enter a name for the service account
4. Click "Create and Continue"
5. In the "Grant this service account access to project" section, select "Editor" role
6. Click "Continue"
7. Click "Done"

## Step 4: Create a Service Account Key

1. In the "Service accounts" section, click on the service account you just created
2. Go to the "Keys" tab
3. Click "Add Key" and select "Create new key"
4. Choose "JSON" as the key type
5. Click "Create"
6. The key file will be downloaded to your computer

## Step 5: Share Your Google Drive Folder

For the service account to access your Google Drive folder, you need to share the folder with the service account email address:

1. Find the service account email address in the Google Cloud Console
   - It will look like `service-account-name@project-id.iam.gserviceaccount.com`
2. Go to Google Drive and open the folder you want to monitor
3. Right-click on the folder and select "Share"
4. Enter the service account email address
5. Make sure the service account has at least "Viewer" access
6. Click "Share"

## Step 6: Configure the Application

1. Run the service account test script:
   ```
   python test_service_auth.py
   ```
2. When prompted, enter the path to the downloaded service account key file
3. Enter the ID of the Google Drive folder you shared with the service account
4. The script will test the authentication and list files in the folder
5. You can choose to save these settings to the config.yaml file

## Troubleshooting

- If you get a "Permission denied" error, make sure you've shared the folder with the service account
- If you get a "File not found" error, make sure the folder ID is correct
- If you get an authentication error, make sure the service account key file is correct and the Google Drive API is enabled
