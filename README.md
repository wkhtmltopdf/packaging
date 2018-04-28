Packaging wkhtmltopdf releases
------------------------------

Packaging wkhtmltopdf is a challenge because of the need for using a patched
Qt to provide additional functionality and the cross-platform targets.
Especially for Linux, the approach for packaging has changed multiple times,
so it is best to decouple it from the releases itself.

This will allow creation of packages as per latest best practices, using the
latest dependent libraries in static builds and for targets to be added long
after the release has been made.
