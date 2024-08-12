# List of categories
categories = [
    "Film & Animation",
    "Autos & Vehicles",
    "Music",
    "Pets & Animals",
    "Sports",
    "Short Movies",
    "Travel & Events",
    "Gaming",
    "Videoblogging",
    "People & Blogs",
    "Comedy",
    "Entertainment",
    "News & Politics",
    "Howto & Style",
    "Education",
    "Science & Technology",
    "Movies",
    "Anime/Animation",
    "Action/Adventure",
    "Classics",
    "Comedy",
    "Documentary",
    "Drama",
    "Family",
    "Foreign",
    "Horror",
    "Sci-Fi/Fantasy",
    "Thriller",
    "Shorts",
    "Shows",
    "Trailers",
    "History & Geography",
    "Economics & Finance"
]

"""
This categories are retrieved from the YouTube data API.

import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors


# Define the scopes required for accessing watch history
scopes = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]


# Disable OAuthlib's HTTPS verification when running locally.
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

api_service_name = "youtube"
api_version = "v3"
client_secrets_file = "client_secret.json"

# Get credentials and create an API client
flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
    client_secrets_file, scopes, redirect_uri='http://localhost:8080/')

# Run the local server and authenticate
credentials = flow.run_local_server(port=8080)

youtube = googleapiclient.discovery.build(
    api_service_name, api_version, credentials=credentials)

request = youtube.videoCategories().list(
            part='snippet',
            regionCode='US'
        )
response = request.execute()
categories = response.get('items', [])

for cat in categories:
    print(f"{cat['snippet']['title']}")

"""