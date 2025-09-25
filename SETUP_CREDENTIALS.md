# 🔐 Credentials Setup Guide

This guide explains how to set up the required API credentials for the YouTube Autopilot system.

## 📋 Required Files

You need to create these files in the `configs/` directory:

### 1. `configs/client_secrets.json`
Copy `configs/client_secrets.json.template` to `configs/client_secrets.json` and fill in your OAuth credentials from Google Cloud Console.

### 2. `configs/api_key.txt`
Copy `configs/api_key.txt.template` to `configs/api_key.txt` and add your Google API key.

### 3. `configs/service_account.json` (Optional)
If using service account authentication, place your service account key file here.

## 🚀 Quick Setup

```bash
# Copy template files
cp configs/client_secrets.json.template configs/client_secrets.json
cp configs/api_key.txt.template configs/api_key.txt

# Edit the files with your actual credentials
nano configs/client_secrets.json
nano configs/api_key.txt
```

## 🔑 Where to Get Credentials

1. **Google Cloud Console**: https://console.cloud.google.com/
2. **APIs & Services** → **Credentials**
3. Create OAuth 2.0 Client ID and API Key
4. Download the OAuth credentials as JSON
5. Copy the API key

## ⚠️ Security Note

These files are automatically ignored by Git (.gitignore) to prevent accidental commits of sensitive data.

**Never commit actual credentials to version control!**
