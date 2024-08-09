import requests
import json
import time
from contextlib import contextmanager
from __main__ import config
import logging
from urllib.parse import urlencode
from db.entity import Transaction


api_base_url = {
    'main' : "https://toncenter.com/api/v2/",
    'test' : "https://testnet.toncenter.com/api/v2/"
}

WORK_MODE = config.crypto['mode']
API_BASE = api_base_url[WORK_MODE]
API_TOKEN = config.crypto[WORK_MODE + '_token']
WALLET = config.crypto[WORK_MODE + '_wallet'] 

logger = logging.getLogger(__name__)

class CryptoException(Exception):
    """ Handles crypto errors""" 


@contextmanager
def _send_api_request(address,method,params=None):
    try:
        url = f"{API_BASE}{method}?address={address}&api_key={API_TOKEN}"
        if params:
            url = "&".join([url,urlencode(params)])
        r = requests.get(url)
        response = json.loads(r.text)
        if not response['ok']:
            raise CryptoException(f"Error process request ({response['code']}): {response['error']}")
        yield response['result']
    except CryptoException as ex:
        raise CryptoException(str(ex)) from ex
    except Exception as ex:
        logger.exception(str(ex))
        raise CryptoException('Crypto API error. See logs') from ex

def check_address(address):
    '''
    Detect address
    '''
    with _send_api_request(address,'detectAddress') as resp:
        return {
            'raw_form':resp['raw_form'],
            'bounceable' : resp['bounceable']['b64url'],
            'non_bounceable' : resp['non_bounceable']['b64url'],
            'type' : resp['given_type'],
            'test_only' : resp['test_only']
        }

def get_address_information(address):
    '''
    Get information about address
    '''

    with _send_api_request(address,'getAddressInformation') as resp:
        logger.debug('getAddressInformation %s',resp)
        return {
            'address':address,
            'balance': int(resp['balance']) / 1000000000, #Balance is in nanoTON
            'last_transaction_id' : resp['last_transaction_id']['hash']
        }

def get_wallet_transactions():
    '''
    Get transactions for address
    '''
    with _send_api_request(WALLET,'getTransactions',{'limit':30,'archival':'true'}) as resp:
        return resp

class CryptoApiTopCenter:
    
    def __init__(self,config=None):
        pass

    @property
    def wallet(self):
        return WALLET

    @property
    def address(self):
        return get_address_information(WALLET)

    @property
    def transactions(self):
        for t in get_wallet_transactions():
            yield Transaction(
                hash=t['transaction_id']['hash'],
                utime=t['utime'],
                srcpurse=t['in_msg']['source'],
                dstpurse=t['in_msg']['destination'],
                value=t['in_msg']['value'],
                message=t['in_msg']['message'],
                fee=t['in_msg']['fwd_fee']
                )
