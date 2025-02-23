from fastapi import FastAPI, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth, OAuthError
from .config import CLIENT_ID, CLIENT_SECRET
from fastapi.staticfiles import StaticFiles
import googleapiclient.discovery
import googleapiclient.errors
from app.youtube_helper import get_user_info, get_subscriptions, get_most_popular_videos, get_random_videos
import json
from app.summarize import summarize
from app.visualize import get_categories

from google.oauth2.credentials import Credentials
import app.models as models
from app.models import Subscriptions, Friendship, User
from app.database import SessionLocal, engine
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from sqlalchemy import delete


from app.models import FriendRequest, Friendship, Onlyuser
from pydantic import BaseModel
from typing import List
import datetime as _dt
from datetime import datetime
import os
import numpy as np
import uuid
from uuid import UUID



models.Base.metadata.create_all(bind=engine)
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="add any string...")
app.mount("/static", StaticFiles(directory="static"), name="static")

oauth = OAuth()
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    client_kwargs={
        'scope': 'email openid profile https://www.googleapis.com/auth/youtube.readonly',
        'redirect_url': 'http://localhost:8000/auth'
    }
)
templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
async def auth(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as e:
        return templates.TemplateResponse(
            name='error.html',
            context={'request': request, 'error': e.error}
        )

    userinfo = token.get('userinfo')
    if not userinfo:
        return RedirectResponse('/')

    email = userinfo.get('email')
    name = userinfo.get('name', "Anonymous User")

    # Check if the user already exists in the DB
    db_user = db.query(Onlyuser).filter(Onlyuser.global_user == email).first()

    if not db_user:
        new_user = Onlyuser(user_id=str(uuid.uuid4()), global_user=email, name=name)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        user_id = new_user.user_id
    else:
        user_id = db_user.user_id

    # Store UUID in the session instead of eTag
    request.session['user'] = {"email": email, "name": name, "user_id": str(user_id), 
                               "given_name": userinfo.get('given_name'), 
                               "family_name": userinfo.get('family_name'),
                               "picture": userinfo.get('picture')}
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
    sender_name: str
    receiver_name: str

class FriendRequestResponse(BaseModel):
    id: int
    sender_id: str
    sender_name: str
    sender_email: str
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
def accept_friend_request(request_id: UUID, db: Session = Depends(get_db)):
    request_id = str(request_id)  # Convert UUID to string

    db_request = db.query(models.FriendRequest).filter(models.FriendRequest.id == request_id).first()
    
    if not db_request:
        raise HTTPException(status_code=404, detail="Friend request not found")

    db_request.status = "accepted"
    friendship = models.Friendship(user1_id=db_request.sender_id, user2_id=db_request.receiver_id)
    
    db.add(friendship)
    db.commit()

    return {"message": "Friend request accepted"}

@app.post("/friend-requests/{request_id}/reject")
def reject_friend_request(request_id: UUID, db: Session = Depends(get_db)):
    request_id = str(request_id)  # Convert UUID to string

    db_request = db.query(models.FriendRequest).filter(models.FriendRequest.id == request_id).first()
    
    if not db_request:
        raise HTTPException(status_code=404, detail="Friend request not found")

    db_request.status = "rejected"
    db.commit()

    return {"message": "Friend request rejected"}



@app.get("/api/friends/", response_model=List[OnlyuserResponse])
def get_friends_api(db: Session = Depends(get_db), request: Request = None):
    etag = request.session.get('etag')
    user = request.session.get('user_id')
    if not user:
        user = db.query(models.Onlyuser.user_id).filter(models.Onlyuser.global_user == request.session['user']['email']).first()
        user = user[0]
        if not user:
            return {"error": "User not authenticated"}

    user_id = user
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
    # etag = request.session.get('etag')
    user = request.session.get('user_id')
    if not user:
        user = db.query(models.Onlyuser.user_id).filter(models.Onlyuser.global_user == request.session['user']['email']).first()
        user = user[0]
        if not user:
            return {"error": "User not authenticated"}

    user_id = user
    # Get accepted friends
    friends = db.query(Onlyuser).join(
        Friendship, 
        (Friendship.user1_id == Onlyuser.user_id) | (Friendship.user2_id == Onlyuser.user_id)
    ).filter((Friendship.user1_id == user_id) | (Friendship.user2_id == user_id)).all()

    # Get pending friend requests with sender details
    pending_requests = (
        db.query(FriendRequest, Onlyuser.name, Onlyuser.global_user)
        .join(Onlyuser, FriendRequest.sender_id == Onlyuser.user_id)
        .filter(FriendRequest.receiver_id == user_id, FriendRequest.status == "pending")
        .all()
    )

    # Convert to structured data
    pending_requests_data = [
        {
            "id": req.FriendRequest.id,
            "sender_id": req.FriendRequest.sender_id,
            "sender_name": req.name,  # Name from Onlyuser
            "sender_email": req.global_user,  # Email from Onlyuser
            "receiver_id": req.FriendRequest.receiver_id,
            "status": req.FriendRequest.status,
            "created_at": req.FriendRequest.created_at
        }
        for req in pending_requests
    ]

    user = request.session.get('user')

    return templates.TemplateResponse(
        name='friends.html',
        context={'request': request, 'user': user, 'friends': friends, 'pending_requests': pending_requests_data, 'user_id': user_id}
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
    sender = db.query(Onlyuser).filter_by(user_id=request.sender_id).first()
    receiver = db.query(Onlyuser).filter_by(user_id=request.receiver_id).first()

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
    user = request.session.get('user')
    if not user:
        return RedirectResponse('/login')
    
    user_id = user.get("user_id")  # Get UUID from session

    if not user_id:
        return {"error": "User not authenticated"}

    user = request.session.get('user')
    
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
    subscriptions = get_subscriptions(youtube, max_results=50000)

    for item in subscriptions:
        channel_name = item["title"]
        channel_id = item["channelId"]

        db_subscription = db.query(models.Subscriptions).filter(models.Subscriptions.id == channel_id).first()
        if not db_subscription:
            db_subscription = models.Subscriptions(id=channel_id, title=channel_name, description=item["description"])
            db.add(db_subscription)

        # Check if the user is already subscribed to this channel
        existing_user_subscription = db.query(models.User).filter(
            models.User.user_id == user_id,
            models.User.subscription == channel_id
        ).first()

        if not existing_user_subscription:
            db_user = models.User(user_id=user_id, subscription=channel_id)
            db.add(db_user)

    db.commit()
    user = request.session.get('user')
    return RedirectResponse('get_recommendations')


def retrive_summarize_from_doc(request: Request, db: Session = Depends(get_db)):
    # Get user_id from the session
    user = request.session.get('user')
    if not user or "user_id" not in user:
        return {"error": "User not authenticated"}
    
    user_id = user["user_id"]

    # Fetch all subscriptions for the user
    subscriptions = (
        db.query(models.Subscriptions)
        .join(models.User, models.User.subscription == models.Subscriptions.id)
        .filter(models.User.user_id == user_id)
        .all()
    )

    # If no subscriptions are found, return a message
    if not subscriptions:
        return {"summary": "You have no subscriptions listed here, please verify our application to fetch the data."}

    # Convert SQLAlchemy objects to a list of dictionaries
    subscriptions_data = [
        {
            "channelId": sub.id,
            "title": sub.title,
            "description": sub.description,
        }
        for sub in subscriptions
    ]

    try:
        # Call the summarize function with the subscriptions
        summary = summarize(subscriptions_data)
    except Exception as e:
        summary = "There was something wrong with summarization."

    # Store summary in session
    request.session['summary'] = summary

    return summary

def visualize_dictionary(request: Request, db: Session = Depends(get_db)):
    user = request.session.get('user')
    if not user or "user_id" not in user:
        return {"error": "User not authenticated"}
    
    user_id = user["user_id"]
        
    categories_arr = db.query(models.ComputedPreferences.preference, models.ComputedPreferences.weight).filter(models.ComputedPreferences.user_id==user_id)
    categories = dict(categories_arr)

    if len(categories) == 0:    
        # Fetch all subscriptions for the user
        subscriptions = (
            db.query(models.Subscriptions)
            .join(models.User, models.User.subscription == models.Subscriptions.id)
            .filter(models.User.user_id == user_id)
            .all()
        )

        # If no subscriptions are found, return a message
        if not subscriptions:
            return {"summary": "You have no subscriptions listed here, please verify our application to fetch the data."}

        # Convert SQLAlchemy objects to a list of dictionaries
        subscriptions = [
            {
                "channelId": sub.id,
                "title": sub.title,
                "description": sub.description,
            }
            for sub in subscriptions
        ]
        
        categories = get_categories(subscriptions)

        # with open(f'categories_{user_id}.json', 'w') as json_file:
        #     json.dump(categories, json_file, indent=4)
        total_channels = sum(categories.values())
        db.execute(delete(models.ComputedPreferences).where(models.ComputedPreferences.user_id == user_id))
        db.commit()
        for category, num in categories.items():
            db_preference = models.ComputedPreferences(user_id=user_id, preference=category, weight=num/total_channels)
            db.merge(db_preference)
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
    user = request.session.get('user')
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

# from sqlalchemy.orm import Session
# from sqlalchemy.sql import func

def get_random_friend_subscriptions(db: Session, user_id: str, limit: int = 5):
    """
    Retrieves a list of random subscriptions from the user's friends.

    Args:
        db (Session): SQLAlchemy Session object.
        user_id (str): User ID of the user whose friends' subscriptions to retrieve.
        limit (int): Number of subscriptions to retrieve. Defaults to 5.

    Returns:
        List of random subscriptions from the user's friends.
    """
    # Step 1: Get user's own subscriptions
    own_subscriptions_query = (
        db.query(User.subscription)
        .filter(User.user_id == user_id)
    )

    # Step 2: Get user's friends' IDs
    friend_ids_query = (
        db.query(Friendship.user1_id)
        .filter(Friendship.user2_id == user_id)
        .union(
            db.query(Friendship.user2_id)
            .filter(Friendship.user1_id == user_id)
        )
    )

    # Step 3: Get subscriptions of friends
    friend_subscriptions_query = (
        db.query(User.subscription)
        .filter(User.user_id.in_(friend_ids_query))
    )

    # Step 4: Combine both own and friends' subscriptions
    combined_subscriptions_query = (
        db.query(Subscriptions)
        .filter(Subscriptions.id.in_(own_subscriptions_query.union(friend_subscriptions_query)))
        .order_by(func.random())  # Randomize order
        .limit(limit)  # Limit the number of results
    )

    return combined_subscriptions_query.all()



@app.get("/get_recommendations")
async def recommendations(request: Request, db: Session = Depends(get_db)):
    etag = request.session.get('etag')
    user = request.session.get('user')

    # if os.path.exists('recommendations.npy'):
    #     numbered_titles = np.load('recommendations.npy', allow_pickle=True)
    #     return templates.TemplateResponse(
    #         name='recommendation.html',
    #         context={'request': request, 'user': user, 'recommendations': numbered_titles}
    #     )

    if not user:
        user = db.query(models.Onlyuser.user_id).filter(models.Onlyuser.global_user == request.session['user']['email']).first()
        user = user[0]
        if not user:
            return {"error": "User not authenticated"}
    
    random_subscriptions = get_random_friend_subscriptions(db, user['user_id'], limit=5)
    titles = []
    for sub in random_subscriptions:
        info = get_random_videos(sub.id, sub.title, max_results=1)
        titles.extend(info)
    numbered_titles = [(i+1, title, link, channel, thumbnail) for i, (title, link, channel, thumbnail) in enumerate(titles)]

    return templates.TemplateResponse(
        name='recommendation.html',
        context={'request': request, 'user': user, 'recommendations': numbered_titles}
    )

def get_channel_recommendation(request: Request, db: Session = Depends(get_db)):
    user = request.session['user']
    etag = db.query(models.Onlyuser.user_id).filter(models.Onlyuser.global_user == request.session['user']['email']).first()
    etag = etag[0]
    computed_preferences = db.query(models.ComputedPreferences.preference, models.ComputedPreferences.weight).filter(models.ComputedPreferences.user_id == etag).all()
    computed_categories = dict(computed_preferences)


