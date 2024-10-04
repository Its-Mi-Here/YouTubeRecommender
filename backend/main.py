from fastapi import FastAPI, Depends

import json
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from fastapi.middleware.cors import CORSMiddleware
from youtube_helper import get_liked_videos, get_subscriptions, get_user_info
from summarize import summarize
from visualize import get_categories

from sqlalchemy.orm import Session

import models
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency
def get_db():
    db = SessionLocal()
    # yield db
    try:
        yield db
    finally:
        db.close()


# Disable OAuthlib's HTTPS verification when running locally.
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

@app.get("/get_data")
async def get_youtube_data(db: Session = Depends(get_db)):
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
    print(f"user_info: {user_info}")
    etag = user_info.get('etag')
    
    try:
        name=user_info.get('items')[0].get('snippet').get('title')
    except:
        name = f'Anon_{etag}'


    if db.query(models.Onlyuser).filter(models.Onlyuser.user_id == user_info.get('etag')).first():
        # name=user_info.get('items')[0].get('snippet').get('title')
        print(f"Welcome Back {name}!")
        return {"message": f"Welcome Back {name}!"}

    else:
        print(f"Welcome {name}!")
        db_onlyuser = models.Onlyuser(user_id=user_info.get('etag'), name=name)
        db.add(db_onlyuser)
        db.commit()


    subscriptions = get_subscriptions(youtube, max_results=50000)
    liked_videos = get_liked_videos(youtube, max_results=50000)


    for item in subscriptions:
        channel_name = item["title"]
        channel_id = item["channelId"]
        
        db_subscription = models.Subscriptions(id=channel_id, title=channel_name, description=item["description"])
        if db.query(models.Subscriptions).filter(models.Subscriptions.id == channel_id).first():
            continue
        db.add(db_subscription)

        db_user = models.User(user_id=user_info.get('etag'), subscription=channel_id)
        db.add(db_user)

    db.commit()
    return {"message": f"Hello {name}! Your data was saved to the database."}
    
    # with open(f"youtube_subscriptions_{user_info.get('etag')}.json", 'w') as json_file:
    #     json.dump(subscriptions, json_file, indent=4)

@app.get("/summarize")
async def retrive_summarize_from_doc():
    with open(f'youtube_subscriptions_RuuXzTIr0OoDqI4S0RU6n4FqKEM.json', 'r') as f:
        subscriptions = json.load(f)
    summary = summarize(subscriptions)

    with open(f"summary_RuuXzTIr0OoDqI4S0RU6n4FqKEM.txt", 'w') as json_file:
        json_file.write(summary)
    
    return summary

@app.get("/visualize")
async def retrive_summarize_from_doc():
    with open(f'youtube_subscriptions_RuuXzTIr0OoDqI4S0RU6n4FqKEM.json', 'r') as f:
        subscriptions = json.load(f)
    # summary = summarize(subscriptions)
    categories = get_categories(subscriptions)

    # with open(f"summary_RuuXzTIr0OoDqI4S0RU6n4FqKEM.txt", 'w') as json_file:
    #     json_file.write(categories)
    
    return categories