
def prepare_build(config, target, build_dir, src_dir):
    import os
    qmake = ''
    for var in ('CFLAGS', 'CXXFLAGS', 'OBJECTIVE_CFLAGS'):
        os.environ[var] = '-w -stdlib=libc++ -mmacosx-version-min=10.7'
        qmake += '"QMAKE_%s+=-fvisibility=hidden -fvisibility-inlines-hidden" ' % var
    return '--prefix=%s' % os.path.join(build_dir, 'qt'), qmake

def package_build(config, target, build_dir, src_dir, version):
    import os, subprocess
    subprocess.check_call('make install INSTALL_ROOT=%s' % os.path.join(build_dir, 'wkhtmltox'), shell=True, cwd=os.path.join(build_dir, 'app'))

    # create distribution
    prefix = '/usr/local/share/wkhtmltox-installer'
    subprocess.check_call('rm -fr dist && mkdir dist', shell=True, cwd=build_dir)
    subprocess.check_call('sudo chown -R root:wheel . && tar zcf ../dist/wkhtmltox.tar.gz . && sudo chown -R $USER .', shell=True, cwd=os.path.join(build_dir, 'wkhtmltox'))

    with open(os.path.join(build_dir, 'dist', 'uninstall-wkhtmltox'), 'w') as f:
        f.write("""#!/bin/bash
if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as sudo uninstall-wkhtmltox" 1>&2
   exit 1
fi
cd /usr/local
if which pkgutil >/dev/null; then
    pkgutil --forget org.wkhtmltopdf.wkhtmltox
fi
""")
        for root, dirs, files in os.walk(os.path.join(build_dir, 'wkhtmltox')):
            for file in files:
                f.write('echo REMOVE /usr/local/%(name)s && rm -f %(name)s\n' % { 'name': os.path.relpath(os.path.join(root, file), os.path.join(build_dir, 'wkhtmltox')) })
        f.write('echo REMOVE /usr/local/include/wkhtmltox && rm -df /usr/local/include/wkhtmltox\n')
        f.write('echo REMOVE /usr/local/bin/uninstall-wkhtmltox && rm -f /usr/local/bin/uninstall-wkhtmltox')

    with open(os.path.join(build_dir, 'extract.sh'), 'w') as f:
        f.write("""#!/bin/bash
TGTDIR=/usr/local
BASEDIR=%s
cd $TGTDIR
tar ozxf $BASEDIR/wkhtmltox.tar.gz
mv $BASEDIR/uninstall-wkhtmltox $TGTDIR/bin
rm -fr $BASEDIR
""" % prefix)

    subprocess.check_call('chmod a+x extract.sh dist/uninstall-wkhtmltox', shell=True, cwd=build_dir)

    pkg_ver, pkg_iter = version
    fversion = '--version "%s-%s.%s"' % (pkg_ver, pkg_iter, target)
    fparams  = ' '.join('--%s "%s"' % (k, v) for k, v in config['fpm-params'].items())
    fpm_args = '-t osxpkg --osxpkg-identifier-prefix org.wkhtmltopdf -f -s dir --after-install extract.sh %s %s' % (fversion, fparams)
    subprocess.check_call('fpm %s --prefix %s -C dist . && mv wk*.pkg ..' % (fpm_args, prefix), shell=True, cwd=build_dir)
