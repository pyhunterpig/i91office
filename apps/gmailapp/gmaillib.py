#coding=utf-8
from email.mime.text import MIMEText
from email.MIMEMultipart import MIMEMultipart
#from email.message import Message
from email.header import Header, decode_header, make_header
from email.MIMEBase import MIMEBase
from email import Encoders
from email.utils import getaddresses, parsedate_tz, mktime_tz
import mimetypes
from datetime import datetime
import os
import imaplib
import smtplib
import email
import logging


log = logging.getLogger(__name__)


def decodeheader(headstring, charset='gb18030'):
#    log.debug('decodeheader(%s)', headstring)
    dh = []
    for s, c in decode_header(headstring):
        if c:
            c = c.replace('gb2312', 'gb18030')
        else:
            c = charset
        dh.append((s, c))
    return dh


def decodeaddresses(addresslist, charset='gb18030'):
    alist = []
    for realname, email_address in getaddresses(addresslist):
        dh = decodeheader(realname, charset)
        alist.append((unicode(make_header(dh)), email_address))
    return alist


def displayaddresses(decode_address):
    return ",".join(["%s <%s>" %(r.encode('utf-8'), a)
                           for r, a in decode_address])


class message:

    def __init__(self, fetched_email):
        self._source = fetched_email
        parsed = email.message_from_string(fetched_email)
        self._msg = parsed
        if parsed['Content-Transfer-Encoding'] == '8bit':
            if len(parsed.get_all('Content-Type', [])) > 1:
                try:
                    parsed._headers.remove(
                   ('Content-Type', 'text/plain; charset="us-ascii"'))
                except:
                    pass
            charset = parsed.get_param('charset')
        else:
            charset = 'gb18030'
        self.To = decodeaddresses(parsed.get_all('To', []), charset)
        self.From = decodeaddresses(parsed.get_all('From', []), charset)
        self.Cc = decodeaddresses(parsed.get_all('Cc', []), charset)
        self.timestamp = mktime_tz(parsedate_tz(parsed['date']))
        self.Date = datetime.fromtimestamp(self.timestamp)
        self.Subject = make_header(decodeheader(parsed['subject'], charset))
        self.Subject = unicode(self.Subject)
        self.body = {}
        self.filenames = []
        self._files = {}

    def parsebody(self):
        accepted_types = ['text/plain', 'text/html']
        parsed = self._msg
        if parsed.is_multipart():
            counter = 1
            for part in parsed.walk():
                # multipart/* are just containers
                if part.get_content_maintype() == 'multipart':
                    continue
                filename = part.get_filename()
                if not filename:
                    if part.get_content_type() in accepted_types:
                        if part.get_content_type() not in self.body:
                            self.body[part.get_content_type()] = []
                        self.body[part.get_content_type()].append(
                                  part.get_payload(decode=True))
                    else:
                        ext = mimetypes.guess_extension(
                               part.get_content_type())
                        if not ext:
                            # Use a generic bag-of-bits extension
                            ext = '.bin'
                            filename = 'part-%03d%s' % (counter, ext)
                        counter += 1
                if filename:
                    try:
                        dh = decodeheader(filename)
                        filename = unicode(make_header(dh))
                    except:
                        log.error('filename Error: %s', filename)
                        pass
                    self.filenames.append(filename)
                    self._files[filename] = part

        else:
            if parsed.get_content_type() in accepted_types:
                self.body = parsed.get_payload(decode=True)

    def __repr__(self):
        return "<Msg from: {0}>".format(self.sender_addr)

    def __str__(self):
        return "To: {0}\nFrom: {1}\nDate: {2}\nSubject: {3}\n\n{4}".format(
               displayaddresses(self.To),
               displayaddresses(self.From),
               self.Date,
               self.Subject.encode('utf-8'),
               self.body)


class account:

    def __init__(self, username, password):
        self.username = username
        self.password = password

        self.sendserver = smtplib.SMTP('smtp.gmail.com:587')
#        self.sendserver.set_debuglevel(1)
        self.sendserver.starttls()
        self.sendserver.login(username, password)

        self.recieveserver = imaplib.IMAP4_SSL('imap.gmail.com', 993)
        self.recieveserver.login(username, password)

    def send(self, toaddr, subject='', content='', cc=[], bcc=[]):
        fromaddr = self.username
        msg = MIMEText(content, 'plain', 'utf-8')
        msg['Content-Type'] = 'text/plain; charset="utf-8"'
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = fromaddr
        msg['To'] = toaddr
        if cc:
            msg['CC'] = ",".join(cc)
        toaddrs = toaddr.split(',') + cc + bcc
        self.sendserver.sendmail(fromaddr, toaddrs, msg.as_string())

    def sendwithatt(self, toaddr, subject, content, attfiles, cc=[], bcc=[]):
        fromaddr = self.username
        msg = MIMEMultipart()
        body = MIMEText(content, 'plain', 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = fromaddr
        msg['To'] = toaddr
        if cc:
            msg['CC'] = ",".join(cc)
        toaddrs = toaddr.split(',') + cc + bcc
        msg.attach(body)

        for attfile in list(attfiles):
            msg.attach(self.attachment(attfile))
        self.sendserver.sendmail(fromaddr, toaddrs, msg.as_string())

    def sendHTMLwithatt(self, toaddr, subject, html, attfiles, cc=[], bcc=[]):
        fromaddr = self.username
        msg = MIMEMultipart()
        body = MIMEText(html, 'html', 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = fromaddr
        msg['To'] = toaddr
        if cc:
            msg['CC'] = ",".join(cc)
        toaddrs = toaddr.split(',') + cc + bcc
        msg.attach(body)

        for attfile in list(attfiles):
            msg.attach(self.attachment(attfile))
        self.sendserver.sendmail(fromaddr, toaddrs, msg.as_string())

    def attachment(self, filename):
        fd = file(filename, "rb")
        mimetype, mimeencoding = mimetypes.guess_type(filename)
        if mimeencoding or (mimetype is None):
            mimetype = "application/octet-stream"
        maintype, subtype = mimetype.split("/")

        retval = MIMEBase(maintype, subtype)
        retval.set_payload(fd.read())
        Encoders.encode_base64(retval)
        retval.add_header("Content-Disposition",
                          "attachment",
                          filename=os.path.basename(filename))
        fd.close()
        return retval

    def recieve(self, email_id, mailbox='Inbox'):
        self.recieveserver.select(mailbox)
        #This nasty syntax fetches the email as a string
        typ, fetched_email = self.recieveserver.fetch(email_id, "(RFC822)")
        log.debug("recieve: %s", fetched_email[0][0])
        return fetched_email[0][1]

    def get_all_messages(self, onlyidlist=False, mailbox='Inbox'):
        self.recieveserver.select(mailbox)
        fetch_list = self.recieveserver.search(None, '(UNDELETED)')[1][0]
        fetch_list = fetch_list.split(' ')
        inbox_emails = []
        log.debug("all[%s]", len(fetch_list))
        if onlyidlist:
            return fetch_list
        for each_email in fetch_list:
            inbox_emails.append(self.get_email(each_email, mailbox=mailbox))
        return inbox_emails

    def unread(self, onlyidlist=False, mailbox='Inbox'):
        self.recieveserver.select(mailbox)
        fetch_list = self.recieveserver.search(None, 'UnSeen')[1][0]
        fetch_list = fetch_list.split(' ')
        if fetch_list == ['']:
            return []
        unread_emails = []
        log.debug("unread[%s]", len(fetch_list))
        if onlyidlist:
            return fetch_list
        for each_email in fetch_list:
            unread_emails.append(self.get_email(each_email, mailbox=mailbox))
        return unread_emails

    def get_email(self, email_id, mailbox='Inbox'):
        self.recieveserver.select(mailbox)
        #This nasty syntax fetches the email as a string
        typ, fetched_email = self.recieveserver.fetch(email_id, "(RFC822)")
        parsed_email = message(fetched_email[0][1])
        log.debug("get_email: %s", fetched_email[0][0])
        return parsed_email

    def inbox(self, mailbox='Inbox', start=0, amount=10):
        self.recieveserver.select(mailbox)
        inbox_emails = []
        messages_to_fetch = ','.join(self._get_uids()[start:start+amount])
        fetch_list = self.recieveserver.uid('fetch',
                                            messages_to_fetch,
                                            '(RFC822)')
        for each_email in fetch_list[1]:
            if(len(each_email) == 1):
                continue
            inbox_emails.append(message(each_email[1]))
        return inbox_emails

    def get_inbox_count(self, mailbox='Inbox'):
        return int(self.recieveserver.select(mailbox)[1][0])

    def _get_uids(self, mailbox='Inbox'):
        self.recieveserver.select(mailbox)
        result, data = self.recieveserver.uid('search', None, 'ALL')
        data = data[0].split(' ')
        data.reverse()
        return data
