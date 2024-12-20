import requests
import pandas as pd
import os
import re
import json
from datetime import datetime
import openpyxl
import datetime

import K # Make sure you add your keys to a K.py file.


def get_tweet_comments(tweet_id):
    url = "https://api.twitter.com/2/tweets/search/recent"
    headers = {
        "Authorization": f"Bearer {K.BEARER_TOKEN}"
    }
    
    query = f"in_reply_to_tweet_id:{tweet_id}"
    params = {
        "query": query,
        "tweet.fields": "author_id,created_at,text",
        "max_results": 100
    }

    all_replies = []
    while len(all_replies) < 50:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.json()}")
            break

        data = response.json()

        now = datetime.datetime.now()
        with open(f"./twitter_responses/{tweet_id}.{now}", 'w') as f:
            json.dump(data, f, indent=4)

        if "data" in data:
            all_replies.extend(data["data"])

        if "meta" in data and "next_token" in data["meta"]:
            params["next_token"] = data["meta"]["next_token"]
        else:
            break

    return all_replies[:50]


def extract_tickers_and_mentions(text):
    tickers = re.findall(r"\$[A-Za-z]+", text)
    mentions = re.findall(r"@[A-Za-z0-9_]+", text)
    mentions_without_first = mentions[1:] if len(mentions) > 1 else []
    mention_links = [f"https://twitter.com/{mention[1:]}" for mention in mentions_without_first]
    
    return {
        "Tickers": ", ".join(tickers),
        "Mentions": ", ".join(mentions_without_first),
        "Mention Links": ", ".join(mention_links)
    }

def process_comments_with_mentions(comments):
    if comments:
        df = pd.DataFrame(comments)
        
        df[['Tickers', 'Mentions', 'Mention Links']] = df['text'].apply(
            lambda x: pd.Series(extract_tickers_and_mentions(x))
        )
        
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['created_at'] = df['created_at'].dt.strftime('%Y-%m-%d %H:%M:%S') 
        
        return df
    else:
        print("No comments found.")
        return pd.DataFrame()

def adjust_column_widths(file_path):
    workbook = openpyxl.load_workbook(file_path)
    sheet = workbook.active

    for column in sheet.columns:
        max_length = 0
        column_letter = column[0].column_letter 
        for cell in column:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except:
                pass
        adjusted_width = max_length + 2
        sheet.column_dimensions[column_letter].width = adjusted_width

    workbook.save(file_path)


def generate_summary_tab(df):
    ticker_counts = df['Tickers'].str.split(", ").explode().dropna().str.strip()
    mention_counts = df['Mentions'].str.split(", ").explode().dropna().str.strip()

    ticker_counts = ticker_counts[ticker_counts != ""].value_counts()
    mention_counts = mention_counts[mention_counts != ""].value_counts()

    ticker_summary = pd.DataFrame({
        "Entity": ticker_counts.index,
        "Count": ticker_counts.values,
        "Type": "Ticker",
        "Link": None
    })

    mention_summary = pd.DataFrame({
        "Entity": mention_counts.index,
        "Count": mention_counts.values,
        "Type": "Mention",
        "Link": mention_counts.index.map(lambda mention: f"https://twitter.com/{mention[1:]}")
    })

    summary_df = pd.concat([ticker_summary, mention_summary], ignore_index=True)
    return summary_df

def reorder_and_save_with_summary(df, TWEET_ID):
    column_order = [
        "id", 
        "author_id", 
        "created_at", 
        "text", 
        "Tickers", 
        "Mentions", 
        "Mention Links"
    ]
    df = df[column_order]
    
    summary_df = generate_summary_tab(df)
    
    file_path = f"{TWEET_ID}.xlsx"
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Comments", index=False)
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
    
    adjust_column_widths(file_path)
    
    os.system(f'open -a "/Applications/Microsoft Excel.app" {file_path}')


