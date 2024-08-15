
import shortuuid
from .entity import Invoice, BackendErrorException
from contextlib import contextmanager
import mysql.connector as connector
import logging
import json
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)
logging.getLogger("mysql.connector").setLevel(logging.DEBUG)


_INSERT_QUERY = 'INSERT INTO invoices (id,amount,srcpurse,dstpurse,context,expired,last_update) VALUES (%(id)s,%(amount)s,%(srcpurse)s,%(dstpurse)s,%(context)s,%(expired)s,UTC_TIMESTAMP())'
_SELECT_QUERY = 'SELECT * FROM invoices WHERE id=%(id)s'
_SELECT_LIST_QUERY = 'SELECT * FROM invoices WHERE dstpurse=%s ORDER BY last_update DESC LIMIT %s'
_UPDATE_STATUS_QUERY = 'UPDATE invoices SET status=%(status)s, transaction=%(transaction)s, last_update=UTC_TIMESTAMP() WHERE id=%(id)s'
_SELECT_PENDING = "SELECT id FROM invoices WHERE dstpurse=%s AND expired>UTC_TIMESTAMP() AND status='pending'"
_UPDATE_EXPIRED = "UPDATE invoices SET status='expired' WHERE expired<=UTC_TIMESTAMP()"

class MySqlBackend:

    def __init__(self,**config):
        self._conn  = connector.connect(pool_name = "invoicepool",pool_size = 3, autocommit=True,**config)


    @contextmanager
    def connection(self):
        try:
            conn = connector.connect(pool_name = "invoicepool") 
            yield conn
        except (connector.errors.ProgrammingError, connector.errors.DatabaseError) as ex:
            logger.error(str(ex))
            raise BackendErrorException('Database error. See logs') from ex
        finally:
            conn.close()

    def create_invoice(self,**invoice_data):
        invoice_id = shortuuid.uuid()
        logger.info('create invoice %s',invoice_id)
        with self.connection() as conn:
            params = invoice_data
            params['id'] = invoice_id
            if 'expired' not in params:
                params['expired'] = datetime.now(tz=timezone.utc) + timedelta(minutes = 30)
            params['context'] = json.dumps(params.get('context',{}))
            params['amount'] = float(params['amount']) * 1000000000 #Store it in nano TONs
            logger.debug("Create invoice : %s",params)
            conn.cursor().execute(_INSERT_QUERY,params)
        return self.load_invoice(invoice_id)

    def load_invoice(self,invoice_id):
        logger.info('load invoice %s',invoice_id)
        with self.connection() as conn:
            cur = conn.cursor(dictionary=True)
            cur.execute(_SELECT_QUERY,{'id':invoice_id})
            return Invoice(**dict(next(cur)))

    def load_invoices(self,wallet,count=100):
        logger.info('load invoices %s',wallet)
        with self.connection() as conn:
            cur = conn.cursor(dictionary=True)
            cur.execute(_SELECT_LIST_QUERY,(wallet,count))
            return [Invoice(**row) for row in cur]

    def load_pending_invoices_ids(self,wallet):
        """Loads invoices in status pending and not expired """
        with self.connection() as conn:
            cur = conn.cursor(dictionary=True)
            cur.execute(_SELECT_PENDING,(wallet,))
            return [row['id'] for row in cur]


    def update_invoice_status(self,invoice_id,status,transaction=None):
        logger.info('update invoice %s : %s',invoice_id,status)
        with self.connection() as conn:
            conn.cursor().execute(_UPDATE_STATUS_QUERY,{'id':invoice_id,'status':status,'transaction':transaction})
            return self.load_invoice(invoice_id)


    def mark_expired(self):
        with self.connection() as conn:
            conn.cursor().execute(_UPDATE_EXPIRED)
            return None
