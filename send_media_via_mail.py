#!/usr/bin/env python
'''
send_media_via_mail.py

Python helper for sending images/videos from digiKam since the integrated Mail tool did not meet
my expectations (I was looking for a quick way to send attachments from my GMail account without
a need to configure a full-blown e-mail client).

Sends images/videos passed as positional arguments via a configured mailer tool (default: viagee)

Images are scaled down and quality is lowered to reduce size of the e-mail. Videos are not processed
(be wary of size limits of your e-mail provider). Sender is hardcoded (see below).

== Installation instructions ==

Install dependencies:
  - viagee/gnome-gmail (https://github.com/davesteele/viagee)
  - xosd (progress indication)
  - python-pillow (resizing + recompression)
  - python-piexif (rotation tag stored in EXIF)
  - python-filetype (detection of image/video file)

Adjust sender variable!

Copy this script /usr/bin and make it executable:
  sudo cp send_media_via_mail.py /usr/bin
  sudo chmod 755 /usr/bin/send_media_via_mail.py

Copy send_media_via_mail.desktop to ~/.local/share/applications/ and re-read
  cp send_media_via_mail.desktop ~/.local/share/applications/
  update-desktop-database ~/.local/share/applications

== Usage ==

In digiKam:
 - mark images/videos to send, right-click to open a context menu
 - choose Open With - Send images/videos via e-mail
 - browser window should open with an e-mail draft containing attachments
 - add recipients, optionally adjust subject and body and hit send

== Bugs ==

There is a lot of room for improvement and PRs are welcome. Please raise them at
https://github.com/jose1711/send_media_via_mail

'''
import smtplib
import ssl
import os
import sys
import logging
import subprocess
import shlex
import io
import piexif
import filetype
from PIL import Image
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText 
from email.mime.application import MIMEApplication
from tempfile import mkstemp

image_length = 1280
image_quality = 60

mailer = 'viagee -r'

# change this!
sender = 'USERNAME@gmail.com'


logging.basicConfig(level=logging.INFO)


def get_message():
    message = MIMEMultipart('mixed')
    message['From'] = 'Contact <{sender}>'.format(sender=sender)
    email_body = '<b>Sent from digiKam</b>'

    body = MIMEText(email_body, 'html')
    message.attach(body)
    return message


# if the attachment is an image, resize it
def get_image(filename):
    try:
        with open(filename, "rb") as attachment:
            image_in = Image.open(attachment)
            size = (image_length, int(image_in.size[1]/image_in.size[0]*image_length))
            
            # let's keep exif data if present
            if image_in.info.get('exif'):
                exif_dict = piexif.load(image_in.info["exif"])
                exif_bytes = piexif.dump(exif_dict)
            else:
                exif_bytes = b''
            
            if image_in.size[0] > image_length:
                image_out = image_in.resize(size)
            else:
                image_out = image_in.copy()
            image_out_data = io.BytesIO()
            image_out = image_out.convert('RGB')
            image_out.save(image_out_data, format='jpeg', quality=image_quality, exif=exif_bytes)
            image_out_data.seek(0)
            return MIMEApplication(image_out_data.read(), _subtype="jpg")
    except Exception as e:
        print(str(e))


# attach videos as-is
def get_video(filename):
    try:
        with open(filename, "rb") as attachment:
            return MIMEApplication(attachment.read())
    except Exception as e:
        print(str(e))


if __name__ == "__main__":
    attachments_count = 0
    # size after converting to MIME format, once exceeded a new e-mail
    # will be composed
    size_limit = 12750000
    filenames = sys.argv[1:]
    messages = []
    message = get_message()
    for filename_index, filename in enumerate(filenames, start=1):
        if not os.path.isfile(filename):
            print('No such file: {}, skipping'.format(filename))
            continue

        if filetype.guess(filename).mime.split('/')[0].startswith('video'):
            attachment = get_video(filename)
        else:
            attachment = get_image(filename)
    
        if attachment:
            attachment.add_header('Content-Disposition',
                                  'attachment; filename= {}'.format(os.path.split(filename)[-1]))
            if len(message.as_string()) + len(attachment.as_string()) + 40 > size_limit:
                messages.append(message)
                message = get_message()
                logging.info('E-mail size limit exceeded, creating a new e-mail')
            message.attach(attachment)
            attachments_count += 1
            logging.info('Attached {}'.format(filename))
        else:
            print('Could not attach {}'.format(filename))
        # progress indication
        subprocess.call(shlex.split('osd_cat -A center '
                                             '-b percentage '
                                             '-p middle '
                                             '-P {} -d 1'.format(filename_index*100/len(filenames))))

    messages.append(message)

    if attachments_count == 0:
        logging.info('Nothing to send, terminating')
        sys.exit(1)

    for message_index, message in enumerate(messages, start=1):
        # this will hold an email message as RFC822 file
        _, temp_file = mkstemp()
        with open(temp_file, 'w') as f:
            message['Subject'] = 'Sent from digiKam ({}/{})'.format(message_index, len(messages))
            f.write(message.as_string())
            logging.info('E-mail written to {}'.format(temp_file))
            logging.info('Sending e-mail'.format(temp_file))
            subprocess.call(shlex.split(mailer) + [temp_file])
        os.remove(temp_file)
