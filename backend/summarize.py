from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

def summarize(subscriptions):
    texts = [sub['title'] + ": " + sub['description'] for sub in subscriptions]


    response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"Given a dictionary of my Youtube subscriptions & their descipritions, generate a short summary of my interests. Don't simply list all the genres, be analytic and determine my interests in life. Dictionary: {texts}"},
      ]
    )

    print(response.choices[0].message.content)

    return response.choices[0].message.content
