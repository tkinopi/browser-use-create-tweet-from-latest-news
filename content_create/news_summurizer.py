from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from browser_use.agent.service import Agent
from browser_use.controller.service import Controller

import asyncio
from typing import List, Optional

from tweepy import Client
from tweepy.errors import TweepyException, Unauthorized

import json
from pathlib import Path

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Twitter API credentials
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

# Initialize controller first
controller = Controller()

class Model(BaseModel):
	content: str
	url: str


class Models(BaseModel):
	models: List[Model]


@controller.action('Save models', param_model=Models)
def save_models(params: Models):
    file_path = Path('news.json')
    existing_data = []
    
    # Add new models to list
    for model in params.models:
        model_data = {
            'content': model.content,
            'url': model.url
        }
        existing_data.append(model_data)
    
    # Save updated list
    with open(file_path, 'w') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)

set_llm = ChatOpenAI(model='gpt-4o')


async def main():
    # Delete existing news.json if it exists
    file_path = Path('news.json')
    if file_path.exists():
        file_path.unlink()
    # Initialize Twitter client
    client = Client(
        bearer_token=TWITTER_BEARER_TOKEN,
        consumer_key=TWITTER_API_KEY,
        consumer_secret=TWITTER_API_SECRET,
        access_token=TWITTER_ACCESS_TOKEN,
        access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
    )

    # Get content using Agent
    task = f"Find the latest news about generative AI and summarize the most important story characters and return it with a URL in 200 characters,  save top 5 to file."
		
    agent = Agent(
        task=task,
        llm=set_llm,
        controller=controller
    )
    await agent.run()

    file_path = Path('news.json')
    combined_entries = []

    with open(file_path, 'r') as f:
        news_data = json.load(f)
        for entry in news_data:
            # Combine content and URL with spacing
            combined_text = f"{entry['content']} \n{entry['url']}"
            combined_entries.append(combined_text)

    # Post tweet
    for combined_text in combined_entries:
        try:
            response = client.create_tweet(text=combined_text)
            print(f"Tweet posted: {combined_text}")
        except Unauthorized as e:
            print(f"Unauthorized: {e}")
        except TweepyException as e:
            print(f"Error posting tweet: {e}")

    return response

if __name__ == "__main__":
    asyncio.run(main())