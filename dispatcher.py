#!/usr/bin/python3
import sys
import os
import asyncio
import logging
import aiohttp
import json
import hashlib

sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))

import config
from utils import get_my_ip,create_db_backend
from crypto.toncenter import CryptoApiTopCenter as CryptoApi
from db.entity import Invoice
from telegrambot import TelegramBot

db =  create_db_backend(**config.db)
crypto = CryptoApi()
telegrambot = TelegramBot(**config.telegrambot)

webhook_queue = asyncio.Queue()
message_queue = asyncio.Queue()

logging.basicConfig(
    format="[TONDISPATCHER]%(asctime)-15s %(process)d %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)
logger = logging.getLogger()

IP = get_my_ip()
SIGN_KEY = config.api['sign_key']
logger.debug('Using external IP %s',IP)

def accepted_statuses(status_code):
    return status_code in [200,204]


def create_webhook_data(invoice):
    return {
        'attempt':0,
        'invoice':dict(invoice),
        'sign': hashlib.md5(f"{invoice.id}:{invoice.amount}:{IP}:{SIGN_KEY}".encode('utf-8')).hexdigest(),
    }

async def bot_message_queue_processor():
    while(1):
        message = await message_queue.get()
        telegrambot.send_message(message)
        await asyncio.sleep(1)

async def webhook_queue_processor():
    while(1):
        webhook_data = await webhook_queue.get()
        logger.debug('Sending webhook %s attempt %s',webhook_data['invoice']['id'],webhook_data['attempt'])
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(config.api['webhook_url'],json=webhook_data) as resp:
                    if not accepted_statuses(resp.status):
                        logger.warning(f'webhook bad status code : %s %s',resp.status,webhook_data)
                        if webhook_data['attempt'] < 3:
                            # Wait and retray after delay
                            webhook_data['attempt'] = webhook_data['attempt'] + 1
                            webhook_queue.put_nowait(webhook_data)
                            await asyncio.sleep(3)
                        else:
                            logger.error('Webhook for %s failed with code %s',webhook_data['invoice']['id'], resp.status)
                            message_queue.put_nowait(f"webhook faild for {webhook_data['invoice']['id']}")
            except aiohttp.ClientConnectorError as e:
                logger.error("Error connect to webhook server :%s",str(e))
                webhook_queue.put_nowait(webhook_data)
                await asyncio.sleep(5)
        await asyncio.sleep(1)

def update_invoice_from_transaction(transaction):
    logger.info('update_invoice_from_transaction %s => %s',transaction.invoice_id, transaction.hash)
    invoice = db.load_invoice(transaction.invoice_id)

    if invoice.amount != transaction.amount:
        logger.warning('Bad invoice amount : invoice(%s) %s transaction(%s) %s',invoice.id,invoice.amount,transaction.hash,transaction.amount)
        db.update_invoice_status(invoice.id, Invoice.STATUS_ERROR)
        raise Exception(f"bad amount invoice({invoice.id}) {invoice.amount} of transaction({transaction.hash}) {transaction.amount}")

    #TODO check  testnet or mainnet

    db.update_invoice_status(invoice.id, Invoice.STATUS_COMPLETED,transaction.hash)
    return db.load_invoice(transaction.invoice_id)


async def transactions_check():
    db.mark_expired()
    pending_invoices = db.load_pending_invoices_ids(crypto.wallet)
    if len(pending_invoices) > 0:
        logger.debug("Pending invoices count %s",len(pending_invoices))
        for t in crypto.transactions:
            if t.invoice_id in pending_invoices:
                try:
                    invoice = update_invoice_from_transaction(t)
                    webhook_data = create_webhook_data(invoice)
                    logger.debug("Append webhook queue %s",webhook_data)
                    webhook_queue.put_nowait(create_webhook_data(invoice))
                    message_queue.put_nowait(f"#invoice_paid\nId: <code>{t.invoice_id}</code>\nAmount: {invoice.amount}\nFrom: {t._srcpurse}\nTo: {t._dstpurse} Transaction: {t.hash}")
                except Exception as ex:
                    logger.exception(str(ex))
                    message_queue.put_nowait(f"#where_is_my_fuckn_money Invoice {t.invoice_id} process error : {str(ex)}")

async def transactions_check_processor():

    while(1):
        await transactions_check()
        await asyncio.sleep(2)

async def main():
    logger.debug('Starting tasks')
    tasks = [transactions_check_processor(), webhook_queue_processor(),bot_message_queue_processor()]
    res = await asyncio.gather(*tasks, return_exceptions=True)
    return res    
     
if __name__ == '__main__':
    logger.debug('Start payment dispatcher')
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
