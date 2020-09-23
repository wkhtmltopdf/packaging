#!/usr/bin/env bash

# We need only binary wkhtmltox files in lambda layer, so we delete all the others
rm -rf /tgt/wkhtmltox/{include,share,lib}

# We need to copy dependencies which are not presented in amazonlinux2 image
libs="libjpeg libpng15 libXrender libfontconfig libfreetype libXext libX11 libxcb libXau libexpat libuuid libbz2"
mkdir -p /tgt/wkhtmltox/lib
for lib in $(echo $libs); do
    echo ".*${lib}\.so\.[0-9]{1,2}" | xargs find /usr/lib64 -regextype posix-awk -regex | xargs cp -t /tgt/wkhtmltox/lib/
done

# To be able to create pdf files we need a font. 
# There is one (dejavu) in the docker image used for compilation.
cp -r /usr/share/fonts /tgt/wkhtmltox/
cat >/tgt/wkhtmltox/fonts/fonts.conf <<EOL
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <dir>/var/task/fonts</dir>
  <dir>/opt/fonts</dir>
  <cachedir>/tmp/fonts-cache</cachedir>
  <config></config>
</fontconfig>
EOL
