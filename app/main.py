from fastapi import FastAPI, Depends
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
from app.youtube_helper import get_user_info, get_subscriptions
import json
from app.summarize import summarize

import app.models as models
from app.database import SessionLocal, engine
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
import random


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
        'scope': 'email openid profile',
        'redirect_url': 'http://localhost:8000/auth'
    }
)


templates = Jinja2Templates(directory="templates")


@app.get("/")
def index(request: Request):
    user = request.session.get('user')
    if user:
        return RedirectResponse('welcome')

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
    user = token.get('userinfo')
    if user:
        request.session['user'] = dict(user)
    return RedirectResponse('welcome')


@app.get('/logout')
def logout(request: Request):
    request.session.pop('user')
    request.session.clear()
    return RedirectResponse('/')


@app.get('/get_youtube_data')
def get_youtube_data(request: Request,  db: Session = Depends(get_db)):
    # print(request.session)
    # user = request.session.get('user')
    # # print(user)
    # if not user:
    #     return RedirectResponse('/')
    
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
    etag = user_info.get('etag')
    request.session['etag'] = etag

    try:
        name=user_info.get('items')[0].get('snippet').get('title')
    except:
        name = f'Anon_{etag}'

    print(f"ETAG: {etag} & name: {name}")
    print(f"request.session: {request.session}")

    # subscriptions = get_subscriptions(youtube, max_results=50000)
    if db.query(models.Onlyuser).filter(models.Onlyuser.user_id == user_info.get('etag')).first():
        # name=user_info.get('items')[0].get('snippet').get('title')
        print(f"Welcome Back {name}!")
        # return {"message": f"Welcome Back {name}!"}
        user = request.session.get('user')
        return templates.TemplateResponse(
            name='get_data.html',
            context={'request': request, 'user': user}
        )

    else:
        print(f"Welcome {name}!")
        db_onlyuser = models.Onlyuser(user_id=user_info.get('etag'), 
                                    global_user=request.session['user']['email'] , 
                                    name=name)
        db.add(db_onlyuser)
        db.commit()


    subscriptions = get_subscriptions(youtube, max_results=50000)
    # liked_videos = get_liked_videos(youtube, max_results=50000)


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
    # return {"message": f"Hello {name}! Your data was saved to the database."}


    # return {"message": f"Hello {name}! Your data was saved to the database."}

    # return RedirectResponse('welcome_2')
    with open(f"youtube_subscriptions_{user_info.get('etag')}.json", 'w') as json_file:
        json.dump(subscriptions, json_file, indent=4)
    
    user = request.session.get('user')
    print(f"user: {user}")
    print(f"surname: {user['family_name']}")
    # print(f"surname: {user['family_name']}")
    
    return templates.TemplateResponse(
        name='get_data.html',
        context={'request': request, 'user': user}
    )

@app.get("/summarize")
async def retrive_summarize_from_doc(request: Request, db: Session = Depends(get_db)):
    etag = request.session.get('etag')
    print(f"Request: {request.session}, etag: {etag}")

    if not etag:
        # if db.query(models.Onlyuser).filter(models.Onlyuser.global_user == request.session['user']['email']):
            # etag = db.query(models.Onlyuser)
        etag = db.query(models.Onlyuser.user_id).filter(models.Onlyuser.global_user == request.session['user']['email']).first()
        # etag = user_from_db.
        print(f"user_from_db: {type(etag)}")
        if not etag:
            return {"error": "User not authenticated"}

    etag = etag[0]
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
    
    return templates.TemplateResponse(
        name='summary.html',
        context={'request': request, 'user': user, 'summary': summary}
    )



def get_random_subscriptions(db: Session, limit: int = 5):
    return db.query(models.Subscriptions).order_by(func.random()).limit(limit).all()


@app.get("/get_recommendations")
async def retrive_summarize_from_doc(request: Request, db: Session = Depends(get_db)):

    print(f"request: {request.session['user']}")
    etag = request.session.get('etag')
    print(f"Request: {request.session}, etag: {etag}")

    if not etag:
        # if db.query(models.Onlyuser).filter(models.Onlyuser.global_user == request.session['user']['email']):
            # etag = db.query(models.Onlyuser)
        etag = db.query(models.Onlyuser.user_id).filter(models.Onlyuser.global_user == request.session['user']['email']).first()
        # etag = user_from_db.
        print(f"user_from_db: {type(etag)}")
        if not etag:
            return {"error": "User not authenticated"}
    
    etag = etag[0]
    random_subscriptions = get_random_subscriptions(db, limit=5)
    titles = []
    for sub in random_subscriptions:
        # print(sub.title, sub.id, sub.description)
        # titles.append(sub.title)
        info = get_most_popular_videos(sub.id, sub.title, max_results=2)
        titles.extend(info)
    
    print(f"titles: {titles}")
    
    user = request.session.get('user')

    numbered_titles = [(i+1, title, link, channel, thumbnail) for i, (title, link, channel, thumbnail) in enumerate(titles)]

    return templates.TemplateResponse(
        name='recommendation.html',
        context={'request': request, 'user': user, 'recommendations': numbered_titles}
    )


def get_channel_uploads_playlist(channel_id):
    youtube = googleapiclient.discovery.build('youtube', 'v3', developerKey=API_KEY)

    # Get the uploads playlist ID
    request = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    )
    response = request.execute()

    uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    return uploads_playlist_id


def get_most_popular_videos(channel_id, channel_name, max_results=20):
    youtube = googleapiclient.discovery.build('youtube', 'v3', developerKey=API_KEY)

    # Get video IDs from the uploads playlist
    uploads_playlist_id = get_channel_uploads_playlist(channel_id)
    
    request = youtube.playlistItems().list(
        part="snippet",
        playlistId=uploads_playlist_id,
        maxResults=50  # Fetch more to ensure sorting is effective
    )
    response = request.execute()

    video_ids = [item['snippet']['resourceId']['videoId'] for item in response['items']]
    
    # Fetch video statistics
    video_request = youtube.videos().list(
        part="statistics,snippet",
        id=",".join(video_ids)
    )
    video_response = video_request.execute()

    # Sort videos by view count
    videos = sorted(video_response['items'], key=lambda v: int(v['statistics'].get('viewCount', 0)), reverse=True)

    # Print top videos
    recommendations = []
    for i, video in enumerate(videos[:max_results]):
        title = video['snippet']['title']
        views = video['statistics'].get('viewCount', 0)
        video_url = f"https://www.youtube.com/watch?v={video['id']}"
        thumbnail_url = video['snippet']['thumbnails']['medium']['url']
        # print(f"{i+1}. {title} - {views} views\n   {video_url}")
        recommendations.append( (title, video_url, channel_name, thumbnail_url) )

    return recommendations


# @app.get("/summary")
# async def return_summary(request: Request):
#     etag = request.session.get('etag')
#     print(f"Request: {request.session}, etag: {etag}")

#     if not etag:
#         return {"error": "User not authenticated"}
    
#     return templates.TemplateResp
