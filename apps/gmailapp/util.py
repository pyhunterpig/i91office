#! /usr/bin/env python
#coding=utf-8

from gmaillib import account, message
from mailstorage import MailStorage, des
import logging
import os
import sys
from bson.binary import Binary
import traceback
from datetime import datetime


log = logging.getLogger(__name__)
mailboxdir = '/mnt/workspace/mailbox'
ms = MailStorage('192.168.100.15')


def save2edo(alias, sourcename):
    import easywebdav
    mailbox = easywebdav.connect('edo.91office.com',
               username='edo', password='every91do')
    mailbox.cd('/files/mailbox')
    filepath = sourcename.replace(mailboxdir + '/', '').encode('utf-8')
    for filedir in filepath.split('/')[:-1]:
        try:
            mailbox.mkdir(filedir)
        except:
            errinfo = "".join(traceback.format_exception(*sys.exc_info()))
            if '404' in errinfo:
                log.error(u'save2edo [%s] error: %s', alias, errinfo.decode('utf-8'))
            pass
        mailbox.cd(filedir)

    filename = sourcename.split('/')[-1].encode('utf-8')
    try:
        mailbox.upload(sourcename, filename)
        url = "http://edo.91office.com%s%s/@@@zopen.91email.chmod?alias=%s" \
              %(mailbox.cwd.decode('utf-8'), filename, alias)
        res = mailbox.session.request('GET', url)
        return res.text
    except:
        errinfo = "".join(traceback.format_exception(*sys.exc_info()))
        log.error(u'save2edo [%s] error: %s', alias, errinfo.decode('utf-8'))
        pass


def adduser(uname, password, alias):
    return ms.adduser(uname, password, alias)


def deluser(uname):
    return ms.deluser(uname)


def passwd(uname, password, listtbl):
    return ms.passwd(uname, password, listtbl)


def receiveSources(uname='', mtype='unread', mailbox='Inbox'):

    userlist = [[], ]
    ms.listuser(uname, userlist)
    for user in userlist[0]:
        user_account = account(user['uname'], des.decode(user['dpasswd']))
        if mtype == 'unread':
            mailidlist = user_account.unread(mailbox=mailbox, onlyidlist=True)
        elif mtype == 'all':
            mailidlist = user_account.get_all_messages(mailbox=mailbox,
                                                   onlyidlist=True)
        else:
            mailidlist = []
        ms.maildb.fetchlog.save({'event': 'fetchstart',
                                'uname': user['uname'],
                                'maillist': mailidlist,
                                'datetime': datetime.now()})
        mailbox = mailbox.split('/')[-1].replace('&', '+').decode('utf-7')
        for mailid in mailidlist:
            try:
                filename = "%s.eml" %(mailid)
                filepath = os.path.join(mailboxdir,
                    user['alias'],
                    mailbox)
                if not os.path.exists(filepath):
                    os.makedirs(filepath)
                filename = os.path.join(filepath, filename)
                if os.path.exists(filename):
                    continue
                source = user_account.recieve(mailid)
                log.debug("get source: %s {%s}", mailid, len(source))
                filename = os.path.join(filepath, filename)
                file = open(filename, 'w')
                file.write(source)
                file.close()
                if mailbox == 'Inbox':
                    save2edo(user['alias'], file.name)
                where = {'uname': user['uname'],
                         'mailbox': mailbox,
                         'sourcename': filename}
                if not ms.mails.find(where).count():
                    ms.mails.save({'sourcename': filename,
                              'uname': user['uname'],
                              'mailbox': mailbox,
                              'source': Binary(source, 128)})
                    ms.maildb.fetchlog.save({'event': 'fetchsuccess',
                                             'uname': user['uname'],
                                             'mailbox': mailbox,
                                             'mailid': mailid,
                                             'datetime': datetime.now()})

            except:
                errinfo = "".join(traceback.format_exception(*sys.exc_info()))
                log.error('get_source [%s] error: %s', mailid, errinfo.decode('utf-8'))
                ms.maildb.fetchlog.save({'event': 'fetcherror',
                                        'uname': user['uname'],
                                        'mailbox': mailbox,
                                        'mailid': mailid,
                                        'error': errinfo,
                                        'datetime': datetime.now()})
                continue
    return len(mailidlist)


def parsemails(uname=''):

    userlist = [[], ]
    ms.listuser(uname, userlist)
    for user in userlist[0]:
        where = {'uname': user['uname'],
                 'subject': {'$exists': False}}
        for doc in ms.mails.find(where):
            try:
                log.debug("parsemails: %s ", doc['sourcename'])
                mail = message(doc['source'])
                doc['msgid'] = mail._msg['Message-ID']
                doc['from'] = mail.From[0]
                doc['to'] = mail._msg['Delivered-To']
                doc['subject'] = mail.Subject
                doc['date'] = mail.Date
                doc['size'] = len(doc['source'])
                ms.mails.save(doc, safe=True)
            except:
                log.error('parsemails [%s] error: %s',
                      doc['sourcename'],
                      "".join(traceback.format_exception(*sys.exc_info())))
                continue


def parsebody(uname=''):

    userlist = [[], ]
    ms.listuser(uname, userlist)
    for user in userlist[0]:
        where = {'uname': user['uname'],
                 'body': {'$exists': False}}
        for doc in ms.mails.find(where):
            try:
                log.debug("parsebody: %s ", doc['sourcename'])
                mail = message(doc['source'])
                mail.parsebody()
                if isinstance(mail.body, dict):
                    doc['body'] = dict([(k, Binary("".join(v), 128))
                                       for k, v in mail.body.items()])
                else:
                    doc['body'] = Binary(mail.body, 128)
                doc['filenames'] = mail.filenames
                ms.mails.save(doc, safe=True)
            except:
                log.error('parsebody [%s] error: %s',
                      doc['sourcename'],
                      "".join(traceback.format_exception(*sys.exc_info())))
                continue


def saveatth(uname=''):

    userlist = [[], ]
    ms.listuser(uname, userlist)
    for user in userlist[0]:
        where = {'uname': user['uname'],
                 'filenames': {'$ne': []}}
        for doc in ms.mails.find(where):
            try:
                log.debug("saveatth: %s ", doc['sourcename'])
                mail = message(doc['source'])
                mail.parsebody()
                filepath = os.path.join(mailboxdir,
                                  user['alias'],
                                  doc.get('mailbox', 'Inbox'),
                                  os.path.splitext(
                                      os.path.basename(doc['sourcename']))[0])
                if not os.path.exists(filepath):
                    os.makedirs(filepath)
                for filename in mail.filenames:
                    file = open(os.path.join(filepath, filename), "wb")
                    file.write(mail._files[filename].get_payload(decode=True))
                    file.close()
                    if doc.get('mailbox') == 'Inbox':
                        save2edo(user['alias'], file.name)
            except:
                log.error('saveatth [%s] error: %s',
                      doc['sourcename'],
                      "".join(traceback.format_exception(*sys.exc_info())))
                continue


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(message)s',
                        filename='mailutil.log',
                        filemode='a')
#    alias = 'users.pyhunterpig'
#    sourcename = '/mnt/workspace/mailbox/users.pyhunterpig/Inbox/6734/受访页面_20120729-20120729.zip'
#    save2edo(alias, sourcename)
    receiveSources('steve.zhi@91office.com')
    parsemails()
    parsebody()
    saveatth()
