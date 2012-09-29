#! /usr/bin/env python
#coding=utf-8

from pymongo import Connection
import hashlib
from crypto import DES
import logging


log = logging.getLogger(__name__)
des = DES()
des.input_key('Px密码!91office')


class MailStorage(object):

    def __init__(self, host='localhosts', port=27017):
        try:
            self.__conn = Connection(host, port)
            self.maildb = self.__conn.maildb
            self.users = self.maildb.users
            self.mails = self.maildb.mails
        except Exception, e:
            log.debug("Open Mongodb: %s", e)

    def checklogin(self, uname, password):
        hmd5 = hashlib.md5()
        hmd5.update(password)
        where = {'uname': uname, 'upasswd': hmd5.hexdigest()}
        if self.users.find(where).count() > 0:
            return True
        else:
            return False

    def adduser(self, uname, password, alias):
        where = {'uname': uname}
        user = self.users.find_one(where)
        if user:
            return False

        hmd5 = hashlib.md5()
        hmd5.update(password)
        dpasswd = des.encode(password)
        user = dict(uname=uname,
                    upasswd=hmd5.hexdigest(),
                    dpasswd=dpasswd,
                    alias=alias)
        self.users.save(user, safe=True)
        return True

    def deluser(self, uname):
        where = {'uname': uname}
        user = self.users.find_one(where)
        if not user:
            return False
        self.users.remove(user, safe=True)
        return True

    def insertmail(self, msgid, from_addr, to_addr, subject, mail_body, \
                   recv_time):
        mail = {}
        mail['msgid'] = msgid
        mail['from'] = from_addr
        mail['to'] = to_addr
        mail['subject'] = subject
        mail['source'] = mail_body
        mail['date'] = recv_time
        mail['size'] = len(mail_body)
        self.mails.save(mail, safe=True)

    def listmail(self, to_addr, listtbl):
        where = {'to': to_addr}
        listtbl[0] = self.mails.find(where, ['size', 'msgid'])

    def listuser(self, uname, listtbl):
        if uname == '':
            where = {}
        else:
            where = {'uname': uname}
        listtbl[0] = self.users.find(where)

    def verifyuser(self, uname):
        where = {'uname': uname}
        user = self.users.find(where).count()
        if user:
            return True
        return False

    def passwd(self, uname, password, listtbl):
        where = {'uname': uname}
        user = self.users.find_one(where)
        if not user:
            return False
        hmd5 = hashlib.md5()
        hmd5.update(password)
        dpasswd = des.encode(password)
        user['upasswd'] = hmd5.hexdigest()
        user['dpasswd'] = dpasswd
        self.users.save(user)
        return True

    def getmailbody(self, mid, mailbody):
        where = {'_id': mid}
        mailbody[0] = self.mails.find_one(where)

    def delmail(self, mid):
        where = {'_id': mid}
        self.mails.remove(where, safe=True)


if __name__ == '__main__':
    ms = MailStorage('192.168.100.15')
    print ms.adduser('steve.zhi@91office.com', 'rskhwzz.', 'users.pyhunterpig')
    print ms.verifyuser('steve.zhi@91office.com')
