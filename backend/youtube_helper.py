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