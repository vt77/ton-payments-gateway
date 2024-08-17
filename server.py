#!/usr/bin/python3
import sys
import os
import logging
import json
from aiohttp import web
from contextlib import contextmanager

sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))
import config
from db.mysql import MySqlBackend
from db.entity import Invoice
from crypto.toncenter import CryptoApiTopCenter,check_address
from telegrambot import TelegramBot
from utils import create_db_backend


logging.basicConfig(stream=sys.stdout,level=logging.DEBUG)
logger = logging.getLogger()

db = create_db_backend(config.db)
routes = web.RouteTableDef()
crypto = CryptoApiTopCenter()
telegrambot = TelegramBot(**config.telegrambot)

class ApiResponse():
    
    def __init__(self):
        self.error = None
        self.response = None

    def __iter__(self):
        if self.error:
            yield 'result','error'
            yield 'msg',self.error
        else:
            yield 'result','ok'
            yield 'data',self.response
              

def make_app():
    app = web.Application()
    app.add_routes(routes)
    return app


@contextmanager
def reponse_context():
    context = ApiResponse()
    try:
        yield context
    except Exception as ex:
        logger.exception(ex)
        context.error  = str(ex)

@routes.get('/')
async def index(request):
    return web.Response(text="Internal API. Access denied")

@routes.post('/invoices/create')
async def create_invoce(request):
    data = await request.json()
    with reponse_context() as ctx:
        invoice_data = Invoice.validate(data) 
        invoice_data['dstpurse'] = crypto.wallet
        invoice = db.create_invoice(**invoice_data)
        telegrambot.send_message(message=f"New invoice created {invoice.id}")
        nanotons = int(invoice.amount * 1000000000)
        ctx.response = {
            'invoice' : dict(invoice),
            'links' : [
                {'text':"Ton Wallet", 'url':f"ton://transfer/{crypto.wallet}?amount={nanotons}&text={invoice.id}"},
                {'text':"Tonkeeper", 'url':f"https://app.tonkeeper.com/transfer/{crypto.wallet}?amount={nanotons}&text={invoice.id}"},
                {'text':"Tonhub", 'url':f"https://tonhub.com/transfer/{crypto.wallet}?amount={nanotons}&text={invoice.id}"}
            ]
        }
    return web.json_response(dict(ctx))

@routes.get('/invoices/{invoice_id}')
async def get_invoice(request):
    invoice_id = request.match_info.get('invoice_id', None)
    logger.debug('Loading invoice %s',invoice_id)
    with reponse_context() as ctx:
        ctx.response = {'invoice':dict(db.load_invoice(invoice_id))}
    return web.json_response(dict(ctx))

@routes.get('/invoices')
async def list_invoces(request):
    with reponse_context() as ctx:
        invoices_list = db.load_invoices(crypto.wallet)
        ctx.response = {'invoices':[dict(i) for i in invoices_list]}
    return web.json_response(dict(ctx))

@routes.get('/transactions')
async def list_transactions(request):
    with reponse_context() as ctx:
        ctx.response = {'transactions':[dict(t) for t in crypto.transactions]}
    return web.json_response(dict(ctx))

@routes.get('/address')
async def address(request):
    with reponse_context() as ctx:
        ctx.response = {'address' : crypto.address}
    return web.json_response(dict(ctx))

@routes.get('/address/{address}')
async def check_user_address(request):
    with reponse_context() as ctx:
        address = request.match_info.get('address', None)
        ctx.response = {'address':check_address(address)}
    return web.json_response(dict(ctx))


@routes.get('/messages')
async def bot_updates(request):
    with reponse_context() as ctx:
        ctx.response = {'updates':telegrambot.get_updates()}
    return web.json_response(dict(ctx))

@routes.post('/messages')
async def bot_message(request):
    data = await request.json()
    with reponse_context() as ctx:
        ctx.response = {'resp':telegrambot.send_message(**data)}
    return web.json_response(dict(ctx))



if __name__ == '__main__':
    web.run_app(make_app())


