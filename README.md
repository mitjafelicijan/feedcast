# Feedcast - listen to news

## Starting categories

- Featured
  - Good vibes (only positive news from the feeds)
- List
  - World news
  - US news
  - Economy
  - Technology
  - Finance
  - Energy
  - Travel
  - Sports
  - Business
  - Crypto
  - Gaming
  - Politics

## General notes

- Use `vault` S3 on DO since I don't use it really.
- Making of all these episodes should happen on 4$ VM on DO.
- The website could be deployed on Cloudflare since it will be used as a proxy
  etc???

## Steps for a new feedcast cycle/episode

1. Fetch stories from RSS feeds and extract content adn save to database.
2. Choose stories from database and recommend not similar stories while
   returning structured return from OpenAI. Parse response and update database
   by setting `process` to 1.
3. Take all stories for today and that have `process` flag ON and create audio
   version of it and save it locally and on S3 with structure
   `audio:category:hash.mp3`.
4. Create a final mp3 version with structure `episode:YYYY-MM-DD:category.mp3`.
5. Push index.api.json to S3.
6. Send push notifications to users (if possible with time delay).

## Install tooling

```
python3 -m venv .venv
source .venv/bin/activate
pip install requests readability-lxml lxml_html_clean html2text feedparser python-dotenv
```

## Tools

- https://platform.openai.com/docs/guides/text-to-speech
- https://github.com/openai/whisper
- https://platform.openai.com/docs/guides/audio?lang=python
- https://platform.openai.com/docs/guides/batch
- https://github.com/buriy/python-readability
- https://platform.openai.com/docs/guides/prompt-engineering
- https://platform.openai.com/docs/guides/structured-outputs
- https://medium.com/@sachinsiwal/integrating-ios-push-notifications-using-swift-209d99862ec2
- https://developer.apple.com/app-store/subscriptions/
- https://developer.apple.com/documentation/storekit/in-app_purchase/original_api_for_in-app_purchase/subscriptions_and_offers/handling_subscriptions_billing
- https://www.revenuecat.com/blog/engineering/ios-in-app-subscription-tutorial-with-storekit-2-and-swift/

