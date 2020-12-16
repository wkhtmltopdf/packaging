Packaging wkhtmltopdf releases
==============================

Packaging wkhtmltopdf is a challenge because of the need for using a patched
Qt to provide additional functionality and the cross-platform targets.
Especially for Linux, the approach for packaging has changed multiple times,
so it is best to decouple it from the releases itself.

This will allow creation of packages as per latest best practices, using the
latest dependent libraries in static builds and for targets to be added long
after the release has been made.

All targets are built in a separate container or VM to ensure that nothing
from the build machine leaks into the output package and it can be reproduced
by anyone.


Requirements
============

The software requirements on the build machine are:

* `git` and `p7zip`
* `python` and `PyYAML`
* `docker` >= 17.05 (for linux targets)
  * build-time args in `FROM` were introduced in this version
* Linux kernel >= 4.8 (for linux targets -- foreign archs only)
  * for seamless foreign arch emulation via qemu-user-static
* `vagrant` with `virtualbox` (for non-linux targets)

On Ubuntu 20.04, this can be installed via a single command:

    sudo apt install -y python-yaml docker.io vagrant virtualbox p7zip-full

If you're building for a non-default architecture, you may need to enable
the `experimental: "true"` flag to enable `docker pull --platform`: see
https://docs.docker.com/engine/reference/commandline/pull/#options

By default, the build system assumes the host system runs on x86-64 GNU/Linux
and it will use QEMU to emulate non-x86 platforms within Docker.

You can override this by using the `--no-qemu` to disable QEMU entirely or
`--use-qemu <PLATFORM>` to force the use of a specific build of QEMU for your
host platform. The platform argument follows the format `os/arch(/variant)`.
Both arguments can be useful for building from non-x86 platforms or diagnosing
QEMU bugs.

Examples:

- Building from x86 hosts no arguments are needed:

        $ ./build package-docker buster-amd64 <PATH-TO-WKHTMLTOPDF>

- To build 32-bit ARM packages on a 32-bit ARM host:

        $ ./build --no-qemu package-docker buster-armhf <PATH-TO-WKHTMLTOPDF>

- To build AMD64 packages on a AArch64 host:

        $ ./build --use-qemu linux/arm64/v8 package-docker buster-amd64 <PATH-TO-WKHTMLTOPDF>

Build System
============

Just call `./build` or `python build` from the top-level folder, you will see
all available commands. The `build.yml` file contains the configuration for
all targets -- it includes documentation on the syntax to use.

The source folder which contains wkhtmltopdf (along with Qt) is always
required as an argument; the version number is automatically generated based
on the latest commit in git. In case you are rebuilding a tagged release, you
can optionally specify an `--iteration` which is included in the filename, so
that different filenames are generated if packaging scripts are different.

Please use `build list-targets` to see all available targets.

Docker
------

For building, just use the `./build package-docker` command and it will
generate a package in the `targets` folder. If you don't specify `--clean`,
it will also keep the complete build folder.

Vagrant
-------

The base VM images are pulled and provisioned on-the-fly, so a lot of time
and bandwidth would possibly be required before the build actually starts.
The source code is pushed to the VM via rsync and the target package is
pulled to the `targets` folder.

As the build steps could be varying across targets, for each VM a "plugin"
needs to be defined which has the `prepare_build` and `package_build`
functions defined and do the necessary steps specific to the target.

For building, just use the `./build vagrant` command and it will bring up
the VM, rsync the code into it, build dependent libraries via conan and
compile Qt along with wkhtmltopdf, package it and copy the package into
the output folder.


Porting
=======

It's best if you can get the distribution/OS to support wkhtmltopdf with
patched Qt, as it would enable using the native package management tools.

Failing this, please open an issue for adding support for a different target.
In case your target also requires patches to Qt, make sure to submit and get
them merged before opening a PR for packaging the target.

Linux
-----

You can build a native distro package if [fpm](https://fpm.readthedocs.io/)
supports it directly. If fpm doesn't support your distro format, build a
tarball which can then be used by extracting it manually.

* If you're building for 64-bit linux, find the appropriate docker image
  and provision it with the required tools/libraries in a custom
  Dockerfile present in the `docker/` folder.
* If you're building for other architectures, if there is a docker image
  then you can use emulation via qemu to use it directly -- but please
  note that it will be very slow -- it is not uncommon for builds to take
  8+ hours on a recent machine.
* If you're building for other architectures and cross-compilation toolchain
  is available along with dependent libraries (either built statically or
  extracted from image), then provision everything in a Dockerfile and then
  specify a cross-compilation prefix.

Please look at the existing definitions and use them as a base to making a
working package. In case you get stuck, please discuss it on the related
issue.


Non-Linux
---------

This requires having a base box available on Vagrant Cloud. See the existing
definitions and use them as a base to making a working package. In case you
get stuck, please discuss it on the related issue.
