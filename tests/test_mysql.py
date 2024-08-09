import sys
import os
import logging
import unittest
from unittest.mock import MagicMock,patch

sys.path.append("./lib")
from db.mysql import MySqlBackend
from db.entity import Invoice
import config

logger = logging.getLogger(__name__)

class TestMysql(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)

    def setUp(self):
        self._backend = MySqlBackend(**config.db)

    def test_create_update_invoice(self):
        """ Create invoice test """
        logger.debug("Start create invoice test")
        data = {
            'amount': 10,
            'srcpurse' : 'srspurse-1234',
            'dstpurse' : 'dstpurse-1234',
            'context' : '{}'
        }
        invoice = dict(self._backend.create_invoice(**data))
        self.assertEqual(invoice['amount'],10)
        self.assertEqual(invoice['srcpurse'],'srspurse-1234')
        self.assertEqual(invoice['dstpurse'],'dstpurse-1234')
        self.assertEqual(invoice['status'],Invoice.STATUS_PENDING)


        invoice = dict(self._backend.update_invoice_status(invoice['id'],Invoice.STATUS_COMPLETED))
        self.assertEqual(invoice['status'],Invoice.STATUS_COMPLETED)


