## Reginald use the youtube search API to search for videos in a channel with youtube API

import os
import requests
import urllib.parse
from html import escape

# Set your API key and channel ID
with open(os.path.join(os.getcwd(), 'key_googleapi.txt'), 'r') as file:
    api_key = file.read().strip()

channel_id = 'UCEwkL7_F9fob_wOIRBuRL6Q'

def generate_youtube_url(video_id):
    return f"https://www.youtube.com/watch?v={video_id}"

# Function to escape HTML special characters in text
def escape_html(text):
    return escape(text)

# Function to generate HTML for video items
def generate_video_item_html(video_id, title, description, thumbnail_url):
    video_url = generate_youtube_url(video_id)
    title = escape_html(title)
    description = escape_html(description)
    return f'''<div class="video-item" onclick="window.open('{video_url}', '_blank')">
    <img src="{thumbnail_url}" alt="Thumbnail for video titled {escape_html(title)}">
    <div class="video-details">
       <strong>{title}</strong>
           <p>{description}</p>
       </div>
    </div>'''
    
query = 'créer une facture'
encoded_query = urllib.parse.quote(query)
url = f'https://www.googleapis.com/youtube/v3/search?key={api_key}&channelId={channel_id}&part=snippet&type=video&q={encoded_query}'

response = requests.get(url)
data = response.json()

# Initialize a list to hold the HTML for each video item
video_items_html = []

#print(data)

# Processing the response
for item in data['items']:
    video_id = item['id']['videoId']
    video_url = generate_youtube_url(video_id)
    title = item['snippet']['title']
    published_at = item['snippet']['publishedAt']
    description = item['snippet']['description']
    thumbnail_url = item['snippet']['thumbnails']['default']['url']
    thumbnail_width = item['snippet']['thumbnails']['default']['width']
    thumbnail_height = item['snippet']['thumbnails']['default']['height']
    video_item_html = generate_video_item_html(video_id, title, description, thumbnail_url)
    video_items_html.append(video_item_html)

# Combine all video item HTML into one string
full_html = '\n'.join(video_items_html)
print(full_html)

    # print(f"Title: {title}")
    # print(f"Video ID: {video_id}")
    # print(f"Published At: {published_at}")
    # print(f"Video URL: {video_url}")
    # print(f"Thumbnail URL: {thumbnail_url}")
    # print(f"Thumbnail width; height: {thumbnail_width}, {thumbnail_height}")
    # print(f"Description: {description}")
    # print("------")
