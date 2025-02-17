from fastapi import FastAPI, Depends, APIRouter, HTTPException
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth, OAuthError
from .config import CLIENT_ID, CLIENT_SECRET, API_KEY
from fastapi.staticfiles import StaticFiles
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from app.youtube_helper import get_user_info, get_subscriptions, get_most_popular_videos
import json
from app.summarize import summarize
from app.visualize import get_categories

from google.oauth2.credentials import Credentials
import app.models as models
from app.database import SessionLocal, engine
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from sqlalchemy import delete


from app.models import FriendRequest, Friendship, Onlyuser
from pydantic import BaseModel
from typing import List
import datetime as _dt
from datetime import datetime

import random
from fastapi.responses import JSONResponse
import os
import numpy as np

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="add any string...")
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_db():
    db = SessionLocal()
    # yield db
    try:
        yield db
    finally:
        db.close()

oauth = OAuth()
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    client_kwargs={
        'scope': 'email openid profile https://www.googleapis.com/auth/youtube.readonly',
        # 'redirect_url': 'http://localhost:8000/auth'
        'redirect_url': 'https://he-bagh-e226a13bbbd3.herokuapp.com/ '
    }
)


templates = Jinja2Templates(directory="templates")


@app.get("/")
def index(request: Request):
    user = request.session.get('user')
    if user:
        return RedirectResponse('get_recommendations')

    return templates.TemplateResponse(
        name="home.html",
        context={"request": request}
    )


@app.get('/welcome')
def welcome(request: Request):
    user = request.session.get('user')
    if not user:
        return RedirectResponse('/')
    return templates.TemplateResponse(
        name='welcome.html',
        context={'request': request, 'user': user}
    )


@app.get("/login")
async def login(request: Request):
    url = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, url)


@app.get('/auth')
async def auth(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as e:
        return templates.TemplateResponse(
            name='error.html',
            context={'request': request, 'error': e.error}
        )
    userinfo = token.get('userinfo')
    if userinfo:
        request.session['user'] = dict(userinfo)

    # Also store the actual token
    request.session['google_token'] = token
    return RedirectResponse('get_recommendations')


@app.get('/logout')
def logout(request: Request):
    request.session.pop('user')
    request.session.clear()
    return RedirectResponse('/')

# Pydantic model for response
class OnlyuserResponse(BaseModel):
    user_id: str
    global_user: str
    name: str
    last_accessed: datetime
    last_downloaded: datetime

    class Config:
        from_attributes = True  # Allows Pydantic to read from ORM objects

class FriendRequestCreate(BaseModel):
    sender_id: str
    receiver_id: str

class FriendRequestResponse(BaseModel):
    id: int
    sender_id: str
    receiver_id: str
    status: str
    created_at: _dt.datetime

@app.post("/friend-requests/", response_model=FriendRequestResponse)
def create_friend_request(friend_request: FriendRequestCreate, db: Session = Depends(get_db)):
    db_friend_request = FriendRequest(**friend_request.dict())
    db.add(db_friend_request)
    db.commit()
    db.refresh(db_friend_request)
    return db_friend_request

@app.get("/friend-requests/{user_id}", response_model=List[FriendRequestResponse])
def get_friend_requests(user_id: str, db: Session = Depends(get_db)):
    return db.query(FriendRequest).filter(FriendRequest.receiver_id == user_id).all()

@app.post("/friend-requests/{request_id}/accept")
def accept_friend_request(request_id: int, db: Session = Depends(get_db)):
    db_request = db.query(FriendRequest).filter(FriendRequest.id == request_id).first()
    if not db_request:
        raise HTTPException(status_code=404, detail="Friend request not found")
    db_request.status = "accepted"
    friendship = Friendship(user1_id=db_request.sender_id, user2_id=db_request.receiver_id)
    db.add(friendship)
    db.commit()
    return {"message": "Friend request accepted"}

@app.post("/friend-requests/{request_id}/reject")
def reject_friend_request(request_id: int, db: Session = Depends(get_db)):
    db_request = db.query(FriendRequest).filter(FriendRequest.id == request_id).first()
    if not db_request:
        raise HTTPException(status_code=404, detail="Friend request not found")
    db_request.status = "rejected"
    db.commit()
    return {"message": "Friend request rejected"}


@app.get("/api/friends/", response_model=List[OnlyuserResponse])
def get_friends_api(db: Session = Depends(get_db), request: Request = None):
    etag = request.session.get('etag')
    if not etag:
        etag = db.query(models.Onlyuser.user_id).filter(models.Onlyuser.global_user == request.session['user']['email']).first()
        user_id = etag[0]
        if not etag:
            return {"error": "User not authenticated"}


    print(f"in get_friends_api")
    # Get accepted friends
    friends = db.query(Onlyuser).join(Friendship, (Friendship.user1_id == Onlyuser.user_id) | (Friendship.user2_id == Onlyuser.user_id)).filter((Friendship.user1_id == user_id) | (Friendship.user2_id == user_id)).all()

    # Convert SQLAlchemy objects to dictionaries
    friends_list = [
        {
            "user_id": friend.user_id,
            "global_user": friend.global_user,
            "name": friend.name,
            "last_accessed": friend.last_accessed,
            "last_downloaded": friend.last_downloaded
        }
        for friend in friends
    ]

    return friends_list


@app.get("/friends/")
def get_friends_page(request: Request, db: Session = Depends(get_db)):
    etag = request.session.get('etag')
    if not etag:
        etag = db.query(models.Onlyuser.user_id).filter(models.Onlyuser.global_user == request.session['user']['email']).first()
        etag = etag[0]
        if not etag:
            return {"error": "User not authenticated"}

    user_id = etag
    # Get accepted friends
    friends = db.query(Onlyuser).join(Friendship, (Friendship.user1_id == Onlyuser.user_id) | (Friendship.user2_id == Onlyuser.user_id)).filter((Friendship.user1_id == user_id) | (Friendship.user2_id == user_id)).all()

    # Get pending friend requests
    pending_requests = db.query(FriendRequest).filter(FriendRequest.receiver_id == user_id, FriendRequest.status == "pending").all()

    user = request.session.get('user')
    print(f"user_id etag: {user_id}")
    # print(f"user: {user}")
    return templates.TemplateResponse(
        name='friends.html',
        context={'request': request, 'user': user, 'friends': friends, 'pending_requests': pending_requests, 'etag': user_id}
    )

@app.get("/search-users/", response_model=List[OnlyuserResponse])
def search_users(name: str, db: Session = Depends(get_db)):
    # Search users
    users = db.query(Onlyuser).filter(Onlyuser.name.ilike(f"%{name}%")).all()

    # Convert each SQLAlchemy object to a dictionary
    users_list = [user.__dict__ for user in users]

    # Remove SQLAlchemy internal attribute
    for user in users_list:
        user.pop('_sa_instance_state', None)

    return users_list


@app.post("/send-friend-request/")
def send_friend_request(request: FriendRequestCreate, db: Session = Depends(get_db)):
    # Validate existence of sender and receiver
    print(f"INSIDE send friend request")

    sender = db.query(Onlyuser).filter_by(user_id=request.sender_id).first()
    receiver = db.query(Onlyuser).filter_by(user_id=request.receiver_id).first()

    print(f"sender: {sender}")
    print(f"reciever: {receiver}")


    if not sender or not receiver:
        raise HTTPException(status_code=404, detail="Sender or receiver not found")

    # Check for existing friend request
    existing_request = db.query(FriendRequest).filter_by(sender_id=request.sender_id, receiver_id=request.receiver_id).first()
    if existing_request:
        raise HTTPException(status_code=400, detail="Friend request already sent")

    # Create new friend request
    new_request = FriendRequest(sender_id=request.sender_id, receiver_id=request.receiver_id, status="pending")
    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    return {"message": f"Friend request sent from {request.sender_id} to {request.receiver_id}"}


@app.get('/get_youtube_data')
def get_youtube_data(request: Request, db: Session = Depends(get_db)):
    # 1) Check that user is logged in
    user = request.session.get('user')
    if not user:
        return RedirectResponse('/login')
    
    # 2) Retrieve token from session
    token = request.session.get('google_token')
    if not token:
        return {"error": "No token found; user has not granted YouTube access"}

    # 3) Convert session token to Credentials
    creds = Credentials(
        token['access_token'],
        refresh_token=token.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=['https://www.googleapis.com/auth/youtube.readonly']
    )

    # 4) Use credentials to build the YouTube client
    youtube = googleapiclient.discovery.build(
        "youtube", "v3", credentials=creds
    )

    # 5) Now you can call your get_user_info, get_subscriptions, etc.
    user_info = get_user_info(youtube)
    etag = user_info.get('etag')
    request.session['etag'] = etag
    
    try:
        name=user_info.get('items')[0].get('snippet').get('title')
    except:
        name = f'Anon_{etag}'

    print(f"ETAG: {etag} & name: {name}")
    print(f"request.session: {request.session}")

    subscriptions = get_subscriptions(youtube, max_results=50000)

    for item in subscriptions:
        channel_name = item["title"]
        channel_id = item["channelId"]
        
        db_subscription = models.Subscriptions(id=channel_id, title=channel_name, description=item["description"])
        if db.query(models.Subscriptions).filter(models.Subscriptions.id == channel_id).first():
            continue
        db.add(db_subscription)

        db_user = models.User(user_id=user_info.get('etag'), subscription=channel_id)
        # if db.query(models.User).filter(models.User.user_id == channel_id).first():
        #     continue
        db.add(db_user)

    db.commit()
    with open(f"youtube_subscriptions_{user_info.get('etag')}.json", 'w') as json_file:
        json.dump(subscriptions, json_file, indent=4)
    
    user = request.session.get('user')
    print(f"user: {user}")
    print(f"surname: {user['family_name']}")

    numbered_titles = []
    if os.path.exists('recommendations.npy'):
        numbered_titles = np.load('recommendations.npy', allow_pickle=True)

    return templates.TemplateResponse(
        name='recommendation.html',
        context={'request': request, 'user': user, 'recommendations': numbered_titles}
        )

# @app.get("/summarize")
def retrive_summarize_from_doc(request: Request, db: Session = Depends(get_db)):
    etag = request.session.get('etag')
    print(f"Request: {request.session}, etag: {etag}")

    if not etag:
        # if db.query(models.Onlyuser).filter(models.Onlyuser.global_user == request.session['user']['email']):
            # etag = db.query(models.Onlyuser)
        etag = db.query(models.Onlyuser.user_id).filter(models.Onlyuser.global_user == request.session['user']['email']).first()
        # etag = user_from_db.
        print(f"user_from_db: {type(etag)}")
        etag = etag[0]
        if not etag:
            return {"error": "User not authenticated"}

    with open(f'youtube_subscriptions_{etag}.json', 'r') as f:
        subscriptions = json.load(f)
    
    try:
        summary = summarize(subscriptions[:50])
    except:
        summary = "There was something wrong with summarization"
    # summary = "This is your summary from the NLP module. You like Tech videos, Pets and all."

    with open(f"summary_{etag}.txt", 'w') as json_file:
        json_file.write(summary)

    request.session['summary'] = summary    
    # return summary

    user = request.session.get('user')
    if not user:
        return RedirectResponse('/')

    return summary

def visualize_dictionary(request: Request, db: Session = Depends(get_db)):

    print(f"request: {request.session['user']}")
    etag = request.session.get('etag')
    print(f"Request: {request.session}, etag: {etag}")

    if not etag:
        # if db.query(models.Onlyuser).filter(models.Onlyuser.global_user == request.session['user']['email']):
            # etag = db.query(models.Onlyuser)
        etag = db.query(models.Onlyuser.user_id).filter(models.Onlyuser.global_user == request.session['user']['email']).first()
        # etag = user_from_db.
        print(f"user_from_db: {type(etag)}")
        etag = etag[0]
        if not etag:
            return {"error": "User not authenticated"}
    
    print(f"etag: {etag}")
    
    categories_arr = db.query(models.ComputedPreferences.preference, models.ComputedPreferences.weight).filter(models.ComputedPreferences.user_id==etag)
    categories = dict(categories_arr)

    # categories = {}
    if len(categories) == 0:    
        with open(f'youtube_subscriptions_{etag}.json', 'r') as f:
            subscriptions = json.load(f)
        categories = get_categories(subscriptions)
        # print(f"categories: {categories}")
        with open(f'categories_{etag}.json', 'w') as json_file:
            json.dump(categories, json_file, indent=4)
        total_channels = sum(categories.values())
        db.execute(delete(models.ComputedPreferences).where(models.ComputedPreferences.user_id == etag))
        db.commit()
        for category, num in categories.items():
            # for item in subscriptions:
            db_preference = models.ComputedPreferences(user_id=etag, preference=category, weight=num/total_channels)
            # db_subscription = models.Subscriptions(id=channel_id, title=channel_name, description=item["description"])
            # if db.query(models.Subscriptions).filter(models.Subscriptions.id == channel_id).first():
            #     continue
            db.merge(db_preference)

            # db_user = models.User(user_id=user_info.get('etag'), subscription=channel_id)
            # db.add(db_user)
        db.commit()

    top_n = 8
    # Sort the categories by value in descending order and get the top N categories
    sorted_categories = sorted(categories.items(), key=lambda item: item[1], reverse=True)

    # Separate top N categories
    top_categories = dict(sorted_categories[:top_n])

    # Calculate the sum of the remaining categories
    others_value = sum(value for _, value in sorted_categories[top_n:])

    # Add 'Others' category if there are remaining categories
    if others_value > 0:
        top_categories['Others'] = others_value

    # categories = {'Education': 4, 'News & Politics': 1, 'Entertainment': 2, 'Gaming': 3, 'History & Geography': 1, 'Comedy': 2, 'Howto & Style': 1, 'Science & Technology': 1}
    user = request.session.get('user')
    # return categories
    # return templates.TemplateResponse(
    #     name='visualize.html',
    #     context={'request': request, 'user': user, 'categories': top_categories}
    # )
    return top_categories


@app.get("/analyze")
async def retrieve_analysis(request: Request, db: Session = Depends(get_db)):
    top_categories = visualize_dictionary(request, db)
    summary = retrive_summarize_from_doc(request, db)
    user = request.session.get('user')

    return templates.TemplateResponse(
            name='user-analysis.html',
            context={'request': request, 'user': user, 'categories': top_categories, 'summary': summary}
        )


def get_random_subscriptions(db: Session, limit: int = 5):
    return db.query(models.Subscriptions).order_by(func.random()).limit(limit).all()


@app.get("/get_recommendations")
async def recommendations(request: Request, db: Session = Depends(get_db)):
    print(f"request: {request.session['user']}")
    etag = request.session.get('etag')
    print(f"Request: {request.session}, etag: {etag}")
    user = request.session.get('user')


    if os.path.exists('recommendations.npy'):
        numbered_titles = np.load('recommendations.npy', allow_pickle=True)
        return templates.TemplateResponse(
            name='recommendation.html',
            context={'request': request, 'user': user, 'recommendations': numbered_titles}
        )

    print(f"GOING INTO recommendations")
    if not etag:
        # if db.query(models.Onlyuser).filter(models.Onlyuser.global_user == request.session['user']['email']):
            # etag = db.query(models.Onlyuser)
        etag = db.query(models.Onlyuser.user_id).filter(models.Onlyuser.global_user == request.session['user']['email']).first()
        # etag = user_from_db.
        print(f"user_from_db: {type(etag)}")
        etag = etag[0]

        if not etag:
            return {"error": "User not authenticated"}
    
    random_subscriptions = get_random_subscriptions(db, limit=20)
    titles = []
    for sub in random_subscriptions:
        # print(sub.title, sub.id, sub.description)
        # titles.append(sub.title)
        info = get_most_popular_videos(sub.id, sub.title, max_results=1)
        titles.extend(info)
    
    print(f"titles: {titles}")
    

    numbered_titles = [(i+1, title, link, channel, thumbnail) for i, (title, link, channel, thumbnail) in enumerate(titles)]

    np.save('recommendations.npy', numbered_titles)

    return templates.TemplateResponse(
        name='recommendation.html',
        context={'request': request, 'user': user, 'recommendations': numbered_titles}
    )


def get_channel_recommendation(request: Request, db: Session = Depends(get_db)):
    user = request.session['user']
    etag = db.query(models.Onlyuser.user_id).filter(models.Onlyuser.global_user == request.session['user']['email']).first()
    etag = etag[0]

    # preferences = db.query(models.Preferences.preference).filter(models.Preferences.user_id == etag).all()
    computed_preferences = db.query(models.ComputedPreferences.preference, models.ComputedPreferences.weight).filter(models.ComputedPreferences.user_id == etag).all()

    # user_categories_list = list(preferences)
    computed_categories = dict(computed_preferences)


