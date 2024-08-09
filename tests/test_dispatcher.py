import sys
import os
import logging
import unittest
import json
import time
from unittest.mock import MagicMock,patch

sys.path.append("./lib")
logger = logging.getLogger(__name__)
import config
config.db['database'] = 'crypto_payments_test'

setattr(sys.modules['__main__'],'config',config)

from db.entity import Transaction,Invoice
from dispatcher import transactions_check
from dispatcher import db

class TestDispatcher(unittest.IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)

    def setUp(self):
        with db.connection() as conn:
            conn.cursor().execute('DELETE FROM invoices')

    @patch('dispatcher.crypto')
    async def test_transactions_check_ok(self,crypto):

        invoice = db.create_invoice(**{'amount':0.1,'srcpurse':'source_purse','dstpurse':'destination_purse'})
        crypto.wallet = 'destination_purse'

        #Mock crypto loader
        crypto.transactions = [Transaction(
            id=None,
            hash = '3cpLiwfwa0WYYl1f5/B8+a093TbYu5wo07X8iNYNSiQ=',
            utime = 123456789,
            srcpurse = 'srcpurse',
            dstpurse = 'dstpurse',
            value = 100000000, #0.1 TON in nano
            message = invoice.id, 
            fee=2
        )]

        await transactions_check()
        invoice_data = dict(db.load_invoice(invoice.id))
        print(invoice_data) 
        self.assertEqual(invoice_data['status'],Invoice.STATUS_COMPLETED)
        self.assertEqual(invoice_data['transaction'],'3cpLiwfwa0WYYl1f5/B8+a093TbYu5wo07X8iNYNSiQ=')
        self.assertEqual(invoice_data['id'],invoice.id)    

    @patch('dispatcher.crypto')
    async def test_transactions_check_amount_error(self,crypto):

        invoice = db.create_invoice(**{'amount':1,'srcpurse':'source_purse','dstpurse':'destination_purse'})
        crypto.wallet = 'destination_purse'

        #Mock crypto loader
        crypto.transactions = [Transaction(
            id=None,
            hash = '3cpLiwfwa0WYYl1f5/B8+a093TbYu5wo07X8iNYNSiQ=',
            utime = 123456789,
            srcpurse = 'srcpurse',
            dstpurse = 'dstpurse',
            value = 100000000, #0.1 TON in nano
            message = invoice.id, 
            fee=2
        )]

        await transactions_check()
        invoice_data = dict(db.load_invoice(invoice.id))
        self.assertEqual(invoice_data['status'],'error')
        self.assertEqual(invoice_data['id'],invoice.id)

