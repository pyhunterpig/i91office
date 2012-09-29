#coding=utf-8
from uliweb import expose, request
from util import *
from json import loads
import sys
import traceback


class ExtResponse(object):
    success, data, message, errors, tid, trace, total = (False, [], '', '',
                                                     0, '', None)

    def __init__(self, **kw):
        self.success = getattr(kw, 'success', False)
        self.message = getattr(kw, 'message', '')
        self.data = getattr(kw, 'data', [])

    def to_Dict(self):
        return self.__dict__


@expose('/')
def index():
    return '<h1>Hello, Uliweb</h1>'

@expose('/fetch/<string:uname>', defaults={'mailbox': 'Inbox'})
@expose('/fetch/<string:uname>/<string:mailbox>')
def fetch(uname, mailbox):
    if mailbox != 'Inbox':
        mailbox = '[Gmail]/%s' %mailbox.encode('utf-7').replace('+','&')
    try:
        if receiveSources(uname, mailbox=mailbox):
            parsemails(uname)
            parsebody(uname)
            saveatth(uname)
        return json({'success': True})
    except:
        errinfo = "".join(traceback.format_exception(*sys.exc_info()))
        return json({'success': False, 'error': errinfo})


@expose()
class compose(object):

    def add(self):
        pass
    
    def edit(self):
        pass
    
    def upload(self):
        pass
    
    def post(self):
        pass



@expose()
class mailbox(object):

    Collection = ms.mails

    @expose('inbox/<string:uname>')
    def inbox(self, uname):
        res = ExtResponse()
        values = []
        total = 0
        where = {'uname': uname, 'mailbox': 'Inbox'}
        fields = ['uname', 'from', 'date', 'subject', 'filenames', 'size']
        sort = [('date', -1)]
        try:
            values, total = self._query(where, fields, sort=sort)
            res.success = True
            res.message = uname
        except Exception, msg:
            res.success = False
            res.errors = str(msg)
            if settings.GLOBAL.DEBUG:
                raise
        res.data = values
        res.total = total

        return dict(res=res)

    @expose('sent/<string:uname>')
    def sent(self, uname):
        res = ExtResponse()
        values = []
        total = 0
        where = {'uname': uname, 'mailbox': '已发邮件'.decode('utf-8')}
        fields = ['uname', 'from', 'date', 'subject', 'filenames', 'size']
        sort = [('date', -1)]
        try:
            values, total = self._query(where, fields, sort=sort)
            res.success = True
            res.message = uname
        except Exception, msg:
            res.success = False
            res.errors = str(msg)
            if settings.GLOBAL.DEBUG:
                raise
        res.data = values
        res.total = total

        return dict(res=res)

    @expose('spam/<string:uname>')
    def spam(self, uname):
        res = ExtResponse()
        values = []
        total = 0
        where = {'uname': uname, 'mailbox': '垃圾邮件'.decode('utf-8')}
        fields = ['uname', 'from', 'date', 'subject', 'filenames', 'size']
        sort = [('date', -1)]
        try:
            values, total = self._query(where, fields, sort=sort)
            res.success = True
            res.message = uname
        except Exception, msg:
            res.success = False
            res.errors = str(msg)
            if settings.GLOBAL.DEBUG:
                raise
        res.data = values
        res.total = total

        return dict(res=res)

    def _query(self, where={}, fields={}, limit=25, start=0, sort=[]):
        """ 查询数据

        """
        where = loads(request.args.get('where', "{}")) or where
        fields = loads(request.args.get('fields', "{}")) or fields
        limit = loads(request.args.get('limit', "{}")) or limit
        start = loads(request.args.get('start', "{}")) or start
        sort = loads(request.args.get('sort', "{}")) or sort
        if sort:
            for i in range(len(sort)):
                if isinstance(sort[i], (dict, )):
                    sort[i] = (sort[i]["property"],
                               sort[i]["direction"] == "ASC" and 1 or -1)

        if fields:
            result = self.Collection.find(where, fields)
        else:
            result = self.Collection.find(where)

        if sort:
            result = result.sort(sort)
        log.debug('query', extra=dict(where=where,
                                      fields=fields,
                                      limit=limit,
                                      start=start,
                                      sort=sort))
        total = result.count()
        values = []
        for row in result.limit(limit):
            row['_id'] = str(row['_id'])
            values.append(row)
        return values, total


@expose()
class admin(object):

    def adduser(self):
        uname = request.args.get('uname')
        password = request.args.get('password')
        alias = request.args.get('alias')
        result = adduser(uname, password, alias)
        return json({'success': result})

    def deluser(self):
        uname = request.args.get('uname')
        result = deluser(uname)
        return json({'success': result})
