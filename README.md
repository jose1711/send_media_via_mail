Python helper for sending images/videos from digiKam since the integrated Mail tool did not meet
my expectations (I was looking for a quick way to send attachments from my GMail account without
a need to configure a full-blown e-mail client).

Sends images/videos passed as positional arguments via a configured mailer tool (default: `viagee`)

Images are scaled down and quality is lowered to reduce size of the e-mail. Videos are not processed
(be wary of size limits of your e-mail provider). Sender is hardcoded (see below).

## Installation instructions

Install dependencies:
  - viagee/gnome-gmail (https://github.com/davesteele/viagee)
  - xosd (progress indication)
  - python-pillow (resizing + recompression)
  - python-piexif (rotation tag stored in EXIF)
  - python-filetype (detection of image/video file)


Adjust `sender` variable!

Copy this script `/usr/bin` and make it executable:
```
sudo cp send_media_via_mail.py /usr/bin
sudo chmod 755 /usr/bin/send_media_via_mail.py
```

Copy `send_media_via_mail.desktop` to `~/.local/share/applications/` and re-read
```
cp send_media_via_mail.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications
```

## Usage

In digiKam:
 - mark images/videos to send, right-click to open a context menu
 - choose Open With - Send images/videos via e-mail
 - browser window should open with an e-mail draft containing attachments
 - add recipients, optionally adjust subject and body and hit send

## Bugs

There is a lot of room for improvement and PRs are welcome. Please raise them at
https://github.com/jose1711/send_media_via_mail/pulls
