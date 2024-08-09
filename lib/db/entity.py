import json
from datetime import datetime

DATETIME_FORMAT = '%Y/%m/%d %H:%M:%S'


class BackendErrorException(Exception):
    """
        Backend Excecptions
    """

class Invoice:

    STATUS_COMPLETED = 'completed'
    STATUS_PENDING = 'pending'
    STATUS_TRANSACTION = 'transaction'
    STATUS_ERROR = 'error'

    def __init__(self,id,amount,srcpurse,dstpurse,status,context,created,last_update,expired,transaction):
        self._id = id
        self._amount = amount
        self._srcpurse = srcpurse
        self._dstpurse = dstpurse
        self._status = status
        self._context = context
        self._created = created
        self._last_update = last_update
        self._expired = expired
        self._transaction = transaction


    def __iter__(self):
        yield 'id',self._id
        yield 'amount',self.amount
        yield 'srcpurse',self._srcpurse
        yield 'dstpurse',self._dstpurse
        yield 'status',self._status
        yield 'context',json.loads(self._context if self._context  else {})
        yield 'created',self._created.strftime(DATETIME_FORMAT)
        if self._last_update is not None:
            yield 'last_update',self._last_update.strftime(DATETIME_FORMAT)
        if self._transaction is not None:
            yield 'transaction',self._transaction
        yield 'expired', self._expired.strftime(DATETIME_FORMAT)


    @property
    def amount(self):
        # Because amount stored in nano
        return self._amount / 1000000000

    @property
    def id(self):
        return self._id


    @property
    def transaction(self):
        return self._transaction

    @staticmethod
    def validate(data):
        """ Validate external data before create invoice """
        parsed = {}
        if 'amount' not in data:
            raise Exception('amount field missing')
        #TODO validate amount int
        parsed['amount'] = data['amount']

        if 'srcpurse' not in data:
            raise Exception('srcpurse field missing')
        #TODO validate srcpurse 
        parsed['srcpurse'] = data['srcpurse']

        if 'context' not in data:
            parsed['context'] = {}
        else:    
            #TODO validate context 
            parsed['context'] = data['context']

        return parsed

    def __str__(self):
        return f"Invoice({self._id})"



class Transaction():
    def __init__(self,**data):
        self._id = data.get('id')
        self._hash = data['hash']
        self._utime = data['utime']
        self._srcpurse = data['srcpurse']
        self._dstpurse = data['dstpurse']
        self._value = data['value']
        self._message = data['message']
        self._fee = data['fee']


    @property
    def invoice_id(self):
        return self._message

    @property
    def hash(self):
        return self._hash

    @property
    def amount(self):
        return self._value / 1000000000

    def __iter__(self):
        if self._id:
            yield 'id',self._id
        for p in ['hash','utime','srcpurse','dstpurse','value','message','fee']:
            v = getattr(self,'_'+p)
            if p in ['value','fee']:
                v = int(v) / 1000000000
            if p == 'utime':
                v = datetime.utcfromtimestamp(int(v)).strftime(DATETIME_FORMAT)
            yield p,v

    