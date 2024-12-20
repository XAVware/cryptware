
# https://docs.dexscreener.com/api/reference

import requests

""" 
Fetch the latest token profiles
Limit: 60 requests per minute

- SAMPLE RESPONSE -

{
  "url": "https://example.com",
  "chainId": "text",
  "tokenAddress": "text",
  "icon": "https://example.com",
  "header": "https://example.com",
  "description": "text",
  "links": [
    {
      "type": "text",
      "label": "text",
      "url": "https://example.com"
    }
  ]
}

"""

def fetch_new():
    url = "https://api.dexscreener.com/token-profiles/latest/v1"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        # Filter for Solana coins only
        solana_coins = [token for token in data if token.get('chainId') == 'solana']
        return solana_coins
    
    except Exception as e:
        print(f"Error fetching new tokens: {e}")
        return None, []
    

""" 
Get one or multiple pairs by token address
Limit: 300 requests per minute

- SAMPLE RESPONSE -

{
  "schemaVersion": "text",
  "pairs": [
    {
      "chainId": "text",
      "dexId": "text",
      "url": "https://example.com",
      "pairAddress": "text",
      "labels": [
        "text"
      ],
      "baseToken": {
        "address": "text",
        "name": "text",
        "symbol": "text"
      },
      "quoteToken": {
        "address": "text",
        "name": "text",
        "symbol": "text"
      },
      "priceNative": "text",
      "priceUsd": "text",
      "liquidity": {
        "usd": 0,
        "base": 0,
        "quote": 0
      },
      "fdv": 0,
      "marketCap": 0,
      "info": {
        "imageUrl": "https://example.com",
        "websites": [
          {
            "url": "https://example.com"
          }
        ],
        "socials": [
          {
            "platform": "text",
            "handle": "text"
          }
        ]
      },
      "boosts": {}
    }
  ]
}
"""
def fetch_pairs(token_address):
    url = f'https://api.dexscreener.com/latest/dex/tokens/{token_address}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get('pairs', [])
    except Exception as e:
        print(f"Error fetching pairs for token {token_address}: {e}")
        return []
    
