from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()
client = OpenAI()

categories = [
    "Film & Animation", "Autos & Vehicles", "Music", "Pets & Animals", "Sports", "Short Movies",
    "Travel & Events", "Gaming", "Videoblogging", "People & Blogs", "Comedy", "Entertainment",
    "News & Politics", "Howto & Style", "Education", "Science & Technology", "Movies", "Anime/Animation",
    "Action/Adventure", "Classics", "Comedy", "Documentary", "Drama", "Family", "Foreign", "Horror",
    "Sci-Fi/Fantasy", "Thriller", "Shorts", "Shows", "Trailers", "History & Geography", "Economics & Finance"
]

def get_categories(subscriptions):
  texts = [sub['title'] + ": " + sub['description'] for sub in subscriptions] # + [video['title'] for video in liked_videos]
  categories_dict = dict()

  
  for text in tqdm(texts, desc="Subscriptions classified:"):
    
    prompt = f"""
    Classify the following YouTube channel description into one of the following categories:

    Categories: {', '.join(categories)}

    Description: "{text}"
    Respond only with 2 category names separated by a comma.
    """

    response = client.chat.completions.create(
    # model="gpt-3.5-turbo",
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"{prompt}"},
      ]
    )
    category = response.choices[0].message.content
    category_1 = category.split(",")[0]
    category_2 = category.split(",")[1]
    if category_2 and category_2[0] == " ":
        category_2 = category_2[1:]

    try:
        if category_1 and category_1 not in ["other", "Other"]:
            if category_1 in categories_dict.keys():
                categories_dict[category_1] += 1
            else:
                categories_dict[category_1] = 1
               
        if category_2 and category_2 not in ["other", "Other"]:
            if category_2 in categories_dict.keys():
                categories_dict[category_2] += 1
            else:
                categories_dict[category_2] = 1
               
    except:
        continue
  return categories_dict
