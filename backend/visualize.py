from openai import OpenAI
from dotenv import load_dotenv
from categories import categories

load_dotenv()
client = OpenAI()

import json
import ast
from tqdm import tqdm

def get_categories(subscriptions):
  texts = [sub['title'] + ": " + sub['description'] for sub in subscriptions] # + [video['title'] for video in liked_videos]
  categories_dict = dict()

  
  for text in tqdm(texts, desc="Subscriptions classified:"):
    response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"Classify the following text into 5 or less these categories {categories}. Return only the python list of categories. Description: {text}"},
      ]
    )
    # categories.update(response.choices[0].text.strip().split(', '))
    # print(f"content: {response.choices[0].message.content}")
    print(response.choices[0].message.content)
    try:
        arr = ast.literal_eval(response.choices[0].message.content)      
        for category in arr:
            if category in ["Other", "other"]:
                continue
            if category in categories_dict.keys():
                categories_dict[category] += 1
            else:
                categories_dict[category] = 1
        print(categories_dict)

    except:
        continue

  return categories_dict
    
#   print(f"categories: {categories}")

