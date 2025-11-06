# Deploying to Render

This guide provides step-by-step instructions for deploying the Google Drive Sync application to Render.

## Prerequisites

1. A [Render account](https://render.com/)
2. Your Google Drive service account key file (JSON format)
3. Your Dify API credentials

## Deployment Steps

### 1. Fork or Clone the Repository

If you haven't already, fork or clone this repository to your GitHub account.

### 2. Connect to Render

1. Log in to your [Render Dashboard](https://dashboard.render.com/)
2. Click on "New +" and select "Blueprint"
3. Connect your GitHub account if you haven't already
4. Select the repository containing your Google Drive Sync application
5. Render will detect the `render.yaml` file and set up the service automatically

### 3. Configure Environment Variables

After the service is created, you'll need to set up these sensitive environment variables:

1. Go to your new service in the Render dashboard
2. Click on "Environment" in the left sidebar
3. Add the following environment variables:

| Variable Name | Description | Example |
|---------------|-------------|---------|
| `GDRIVE_SYNC_GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE` | The entire contents of your Google service account JSON key file | `{"type": "service_account", "project_id": "your-project", ...}` |
| `GDRIVE_SYNC_GOOGLE_DRIVE_FOLDER_ID` | Your Google Drive folder ID | `1aaV4TBjLPDnWeN26Rk7H-H_Gy8kn0oKf` |
| `GDRIVE_SYNC_DIFY_API_URL` | Your Dify API URL | `https://api.dify.ai/v1/datasets/{dataset_id}/document/create-by-file` |
| `GDRIVE_SYNC_DIFY_DATASET_ID` | Your Dify dataset ID | `4e960820-fbd7-40ae-a8fe-ea39e3b0d998` |
| `GDRIVE_SYNC_DIFY_API_KEY` | Your Dify API key | `dataset-NmmhuDlzJBsjSPGlUJDmKSje` |

### 4. Deploy Your Application

1. Click "Save Changes" after configuring environment variables
2. Render will automatically deploy your application
3. You can view logs by clicking on the "Logs" tab

## File Storage on Render

Since Render's file system is ephemeral (temporary), the application is configured to use `/tmp` directories for:

1. Database storage: `/tmp/file_metadata.db`
2. Downloaded files: `/tmp/downloads`

This means that if the service restarts, the database and downloaded files will be reset. This is generally acceptable because:

1. The database only stores file metadata for change detection
2. Downloaded files are temporary and are deleted after being uploaded to Dify

## Monitoring Your Deployment

1. **View Logs**: Check the "Logs" tab in your Render dashboard
2. **Check Status**: The service status will be displayed in the dashboard
3. **Set Up Alerts**: Configure alerts in Render for service failures

## Troubleshooting

If you encounter issues:

1. **Check Logs**: Most errors will be visible in the logs
2. **Verify Environment Variables**: Make sure all required variables are set correctly
3. **Check Resource Limits**: Ensure your service has enough memory and CPU resources

## Updating Your Deployment

When you push changes to your GitHub repository, Render will automatically redeploy your application if `autoDeploy` is set to `true` in the `render.yaml` file.

## Cost Considerations

The application is configured to use Render's "Starter" plan, which costs $7/month. This should be sufficient for most use cases. If you need more resources, you can upgrade to a higher plan in the Render dashboard.
