import sys
import os
import logging
import unittest
import json
import time
from unittest.mock import MagicMock,patch

from server import make_app

from aiohttp.test_utils import AioHTTPTestCase
from aiohttp import web

sys.path.append("./lib")
logger = logging.getLogger(__name__)


class TestApi(AioHTTPTestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)

    def setUp(self):
        self._backend = MagicMock()
        #DatabaseManager.register_backend(self._backend)

    async def get_application(self):
        return make_app()

    async def test_get_root(self):
        async with self.client.request("GET", "/") as resp:
            self.assertEqual(resp.status, 200)
            text = await resp.text()
        self.assertIn("Internal API. Access denied", text)

    @patch('server.db')
    async def test_post_invoice_create(self,database):
        print(database)
        async with self.client.request("GET", "/invoices/create") as resp:
            self.assertEqual(resp.status, 200)
            text = await resp.text()
        self.assertIn("Internal API. Access denied", text)


