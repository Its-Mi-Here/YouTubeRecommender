from fastapi import FastAPI
from pydantic import BaseModel

import json
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from fastapi.middleware.cors import CORSMiddleware
from youtube_helper import get_liked_videos, get_subscriptions, get_user_info
from summarize import summarize

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Disable OAuthlib's HTTPS verification when running locally.
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
CREDS = None

@app.get("/auth")
def google_oauth():
    scopes = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl"
    ]
    
    client_secrets_file = "client_secret_860774433001-ojb91ftpisr9gb8jj6thtcvo9qdl53t9.apps.googleusercontent.com.json"

    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes, redirect_uri='http://localhost:8080/')
    
    # Run the local server and authenticate
    credentials = flow.run_local_server(port=8080)
    CREDS = credentials
    # print(f"CREDS in oauth: {CREDS}")
    # return credentials

@app.get("/get_data")
async def get_youtube_data():
    api_service_name = "youtube"
    api_version = "v3"
    scopes = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl"
    ]
    
    client_secrets_file = "client_secret_860774433001-ojb91ftpisr9gb8jj6thtcvo9qdl53t9.apps.googleusercontent.com.json"

    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes, redirect_uri='http://localhost:8080/')
    
    # Run the local server and authenticate
    credentials = flow.run_local_server(port=8080)

    # print(f"CREDS in get_youtube_data: {CREDS}")    
    youtube = googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)

    user_info = get_user_info(youtube)

    subscriptions = get_subscriptions(youtube, max_results=50000)
    liked_videos = get_liked_videos(youtube, max_results=50000)

    with open(f"youtube_subscriptions_{user_info.get('etag')}.json", 'w') as json_file:
        json.dump(subscriptions, json_file, indent=4)

@app.get("/summarize")
async def retrive_summarize_from_doc():
    with open(f'youtube_subscriptions_RuuXzTIr0OoDqI4S0RU6n4FqKEM.json', 'r') as f:
        subscriptions = json.load(f)
    summary = summarize(subscriptions)

    with open(f"summary_RuuXzTIr0OoDqI4S0RU6n4FqKEM.txt", 'w') as json_file:
        json_file.write(summary)
    
    return summary