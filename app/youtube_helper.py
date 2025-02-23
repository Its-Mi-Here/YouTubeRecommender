import random
import googleapiclient.discovery
import googleapiclient.errors
from .config import API_KEY


def get_liked_videos(youtube, max_results=50):
    liked_videos = []
    next_page_token = None

    while len(liked_videos) < max_results:
        request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId="LL",
            maxResults=min(max_results - len(liked_videos), 50),
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response.get('items', []):
            liked_videos.append({
                'videoId': item['contentDetails']['videoId'],
                'title': item['snippet']['title'],
                'publishedAt': item['snippet']['publishedAt']
            })

        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    return liked_videos

def get_subscriptions(youtube, max_results=50):
    subscriptions = []
    next_page_token = None

    while True:
        request = youtube.subscriptions().list(
            part="snippet",
            mine=True,
            maxResults=max_results,
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response.get('items', []):
            subscriptions.append({
                'channelId': item['snippet']['resourceId']['channelId'],
                'title': item['snippet']['title'],
                'description': item['snippet']['description'],
                'publishedAt': item['snippet']['publishedAt']
            })

        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    return subscriptions

def get_user_info(youtube):
    req = youtube.channels().list(part="snippet,contentDetails", mine=True)
    info = req.execute()

    return info


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
        maxResults=10  # Fetch more to ensure sorting is effective
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

def get_random_videos(channel_id, channel_name, max_results=20):
    youtube = googleapiclient.discovery.build('youtube', 'v3', developerKey=API_KEY)

    # Get video IDs from the uploads playlist
    uploads_playlist_id = get_channel_uploads_playlist(channel_id)

    request = youtube.playlistItems().list(
        part="snippet",
        playlistId=uploads_playlist_id,
        maxResults=max_results * 2  # Fetch more videos to ensure randomness
    )
    response = request.execute()

    video_items = response.get('items', [])
    if not video_items:
        return []

    # Select random videos (avoiding extra API calls)
    random_videos = random.sample(video_items, min(max_results, len(video_items)))

    recommendations = [
        (
            video['snippet']['title'],
            f"https://www.youtube.com/watch?v={video['snippet']['resourceId']['videoId']}",
            channel_name,
            video['snippet']['thumbnails']['medium']['url']
        )
        for video in random_videos
    ]

    return recommendations

def get_super_fast_videos(channel_id, channel_name, max_results=20):
    youtube = googleapiclient.discovery.build('youtube', 'v3', developerKey=API_KEY)

    # Directly fetch max_results videos, avoiding extra requests
    request = youtube.search().list(
        part="snippet",
        channelId=channel_id,
        maxResults=max_results,
        type="video",
        order="date"  # Fetch latest videos for freshness
    )
    response = request.execute()

    video_items = response.get('items', [])
    if not video_items:
        return []

    # Randomly pick videos (without extra API calls)
    selected_videos = random.choices(video_items, k=min(max_results, len(video_items)))

    recommendations = [
        (
            video['snippet']['title'],
            f"https://www.youtube.com/watch?v={video['id']['videoId']}",
            channel_name,
            video['snippet']['thumbnails']['medium']['url']
        )
        for video in selected_videos
    ]

    return recommendations

