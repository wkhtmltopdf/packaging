#!/usr/bin/env bash

libs="libjpeg libpng15 libXrender libfontconfig libfreetype libXext libX11 libxcb libXau"

for lib in $(echo $libs); do
    echo ".*${lib}\.so\.[0-9]{1,2}" | xargs find /usr/lib64 -regextype posix-awk -regex | xargs cp -t /tgt/wkhtmltox/lib/
done

rm -rf /tgt/wkhtmltox/{include,share}

cp -r /usr/share/fonts /tgt/wkhtmltox/
cat >/tgt/wkhtmltox/fonts/font.conf <<EOL
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <dir>/var/task/fonts/</dir>
  <cachedir>/tmp/fonts-cache/</cachedir>
  <config></config>
</fontconfig>
EOL
