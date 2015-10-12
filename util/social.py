import twitter
import logging


class Twitter:
    def __init__(self, key, secret, access_key, access_secret):
        self.consumer_key = key
        self.consumer_secret = secret
        self.access_token_key = access_key
        self.access_token_secret = access_secret
        self.api = twitter.Api(consumer_key=self.consumer_key,
                               consumer_secret=self.consumer_secret,
                               access_token_key=self.access_token_key,
                               access_token_secret=self.access_token_secret)
        creds = self.api.VerifyCredentials()
        logging.debug(creds)

    def post(self, message):
        self.api.PostUpdate(message)
