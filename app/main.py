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
from app.youtube_helper import get_user_info, get_subscriptions, get_most_popular_videos
import json
from app.summarize import summarize
from app.visualize import get_categories


import app.models as models
from app.database import SessionLocal, engine
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from sqlalchemy import delete

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


@app.get("/visualize")
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
    
    categories_arr = db.query(models.ComputedPreferences.preference, models.ComputedPreferences.weight).filter(models.ComputedPreferences.user_id==etag)
    categories = dict(categories_arr)

    # categories = {}
    if len(categories) == 0:    
        with open(f'youtube_subscriptions_{etag}.json', 'r') as f:
            subscriptions = json.load(f)
        categories = get_categories(subscriptions)
        # print(f"categories: {categories}")
        # with open('categories.json', 'w') as json_file:
        #     json.dump(categories, json_file, indent=4)
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
    return templates.TemplateResponse(
        name='visualize.html',
        context={'request': request, 'user': user, 'categories': top_categories}
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
    random_subscriptions = get_random_subscriptions(db, limit=2)
    titles = []
    for sub in random_subscriptions:
        # print(sub.title, sub.id, sub.description)
        # titles.append(sub.title)
        info = get_most_popular_videos(sub.id, sub.title, max_results=1)
        titles.extend(info)
    
    print(f"titles: {titles}")
    
    user = request.session.get('user')

    numbered_titles = [(i+1, title, link, channel, thumbnail) for i, (title, link, channel, thumbnail) in enumerate(titles)]

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


