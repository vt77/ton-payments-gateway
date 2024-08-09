import requests
import logging
from contextlib import contextmanager
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self,token,chat_id):
        self._token = token
        self._chat_id = chat_id

    @contextmanager
    def _method_call(self,method,params=None):
        logger.debug("[TELEGRAMBOT]Send %s => %s",method,params)
        url = f"https://api.telegram.org/bot{self._token}/{method}"
        if params:
            url = '?'.join([url,urlencode(params)])
        data = requests.get(url).json()
        if not data['ok']:
            raise Exception(str(data['description']))
        yield data['result']

    def send_message(self,message):
        with self._method_call('sendMessage',{'chat_id':self._chat_id,'text':message}) as res:
            return res 
    
    def get_updates(self):
        with self._method_call('getUpdates') as res:
            return res 
