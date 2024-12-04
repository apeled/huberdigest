#!/usr/bin/env python
# coding: utf-8

"""
Merges podcast RSS feed data with YouTube video transcripts.
The script fetches data using the rss_scraper and 
transcripts_scraper modules, then matches each
podcast entry in the RSS feed with its 
corresponding YouTube video 
transcript based on their index. The most
recent podcast corresponds to the first entry in the RSS feed and the 
first YouTube video in the playlist. It 
saves the merged data as JSON files, each representing a podcast episode 
with its corresponding transcript.

Authors: Mark Daniel, Amit Peled 
Date: 2024-02-28
"""

import os
import json
from tldhuber.utils.rss_scraper import scrape_rss_data
from tldhuber.utils.transcripts_scraper import get_channel_upload_playlist_id_by_channelid, \
      get_playlist_items


#Number of local variables is necessary for testing and implementation purposes
# pylint: disable=R0914
def merge_rss_and_transcripts(api_key, channel_id, rss_feed_url):
    """
    Fetches and merges RSS feed data with
    YouTube video transcripts, saving each
    merged entry as a JSON file.
    
    Parameters:
    - api_key (str): The API key for YouTube Data API access.
    - channel_id (str): The ID of the YouTube channel to fetch video transcripts from.
    - rss_feed_url (str): The URL of the RSS feed to fetch podcast data.
    """
    # Fetch RSS data
    rss_data = scrape_rss_data(rss_feed_url)

    # Fetch YouTube data
    upload_playlist_id = get_channel_upload_playlist_id_by_channelid(api_key, channel_id)
    playlist_items = get_playlist_items(api_key, upload_playlist_id)

    # Ensure directory for merged data exists
    directory = "merged_data"
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Iterate over playlist_items and rss_data simultaneously
    for index, item in enumerate(playlist_items):
        video_id = item["contentDetails"]["videoId"]
        video_title = item["snippet"]["title"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        # Assume fetching transcript function exists
        transcript = "Sample Transcript"  # Placeholder for actual transcript fetching logic

        rss_entry = rss_data.iloc[index] if index < len(rss_data) else None
        if rss_entry is not None:
            title = rss_entry['Title']
            pub_date = rss_entry['Publication Date']
            summary = rss_entry['Summary']
            enclosure_link = rss_entry['Enclosure Link']
        else:
            title = video_title  # Fallback to video title if RSS entry is missing

        merged_entry = {
            "podcast_title": title,
            "publication_date": pub_date,
            "summary": summary,
            "enclosure_link": enclosure_link,
            "video_title": video_title,
            "video_url": video_url,
            "transcript": transcript
        }

        # Save merged data as JSON file
        output_filename = os.path.join(directory, f"merged_entry_{index}.json")
        with open(output_filename, 'w', encoding='utf-8') as file:
            json.dump(merged_entry, file, indent=4)
        print(f"Merged entry saved to {output_filename}")

def main():
    """
    Entry point for the script.

    This function orchestrates the merging of RSS feed data with transcripts
    retrieved using the YouTube Data API. It fetches the channel's upload playlist
    ID using the provided channel ID, then retrieves the playlist items and merges
    them with the RSS feed items. The resulting data is then processed further.

    Parameters:
    - None

    Returns:
    - None
    """
    api_key = "" 
    channel_id="UC2D2CMWXMOVWx7giW1n3LIg"
    rss_feed_url = "https://feeds.megaphone.fm/hubermanlab"
    merge_rss_and_transcripts(api_key, channel_id, rss_feed_url)

if __name__ == "__main__":
    main()
