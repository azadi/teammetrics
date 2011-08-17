#! /usr/bin/env python

"""Removes specified headers from mailbox archives."""

import sys
import mailbox

HEADERS = ('From',
           'Date',
           'Subject',
           'Message-ID',
           'Message-Id',
           'In-Reply-To',
           'References',
           'Content-Type',
           'MIME-Version',
           'Content-Transfer-Encoding',
           'X-Spam-Status',
           'X-Debian-PR-Message',
           'X-Debian-PR-Package',
           'X-Debian-PR-Keywords',
          )

# It might make sense to keep these headers as well.
possible_HEADERS = ('CC',
                    'DKIM-Signature',
                    'DomainKey-Signature',
                    'List-Id',
                    'List-Post',
                    'List-Help',
                    'List-Subscribe',
                    'List-Unsubscribe',
                    'Mail-Followup-To',
                    'To',
                   )


def main(mbox_file):

    out_mbox = mbox_file + '.converted'
    mbox = open(out_mbox, 'w')

    with open(mbox_file) as f:
        # Set the initial markers. Follow the code and the markers will
        # illustrate their respective purpose. 
        stop = False
        start_h = False
        first_add = True
        header = True

        for line in f:

            # If a line starts with a blank space or a '\t', output it provided
            # the line is a header. This excludes lines within the message body.
            if line.startswith((' ', '\t')):
                if start_h:
                    if header:
                        print >>mbox, line, 
            else:
                start_h = False

            # If a line starts with one of the headers specified.
            if line.startswith(HEADERS):
                if header:
                    start_h = True
                    stop = False
                    first_add = True

                    print >>mbox, line,

            # Headers have ended, now start with the message content.
            if stop:
                header = False
                if first_add:
                    print >>mbox
                    first_add = False

                print >>mbox, line,
            
            # Mark the headers to stop and start with the message body.
            if line == '\n':
                stop = True
                header = True
                start_h = False
            
    print 'Headers stripped from mbox'

    # Now open the converted mbox archive to delete messages with the
    # Message-IDs specified in the file messageid. If the file is not
    # found at this point, simply exit. 
    msg_ids = []
    try:
        with open('messageid') as f:
            msg_ids = [line.strip() for line in f.readlines()]
    except IOError:
        sys.exit('Error: messageid file not found in current working directory')

    # Write the changes after matching the respective Message-IDs.
    mbox = mailbox.mbox(out_mbox)

    mbox.lock()
    counter = 0
    for key, msg in mbox.iteritems():
        msg_id = msg['Message-ID']
        if msg_id in msg_ids: 
            mbox.remove(key)
            counter += 1

    print 'Deleted %d messages' % counter
    mbox.flush()
    mbox.close()
    sys.exit('Done')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('Usage: %s <mbox>' % (sys.argv[0]))
    mbox_file = sys.argv[1]
    main(mbox_file)