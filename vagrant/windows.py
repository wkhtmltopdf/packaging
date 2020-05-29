
def _registry_value(key, value=None):
    import winreg
    for mask in [0, winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY]:
        try:
            reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key, 0, winreg.KEY_READ | mask)
            return winreg.QueryValueEx(reg_key, value)[0]
        except WindowsError:
            pass
    return value

def _nsis_version(ver):
    ver = ver.split('-')[0]
    while ver.count('.') < 3:
        ver += '.0'
    return ver

def prepare_build(config, target, build_dir, src_dir):
    import json, os, sys, subprocess

    msvc_ver = config['vagrant-targets'][target]['msvc_version']
    tool_dir = os.environ['VS%sCOMNTOOLS' % msvc_ver.replace('.', '')]
    msvc_dir = os.path.abspath(os.path.join(tool_dir, '..', '..', 'VC'))
    msvc_arg = 'x86'

    if target.endswith('-win64'):
        if os.path.exists(os.path.join(msvc_dir, 'bin', 'amd64', 'cl.exe')):
            msvc_arg = 'amd64'
        else:
            msvc_arg = 'x86_amd64'

    stdout = subprocess.check_output('("%s" %s>nul)&&"%s" -c "import json, os, sys; sys.stdout.write(json.dumps(dict(os.environ)))"' % (
        os.path.join(msvc_dir, 'vcvarsall.bat'), msvc_arg, sys.executable), shell=True)

    os.environ.update(json.loads(stdout if isinstance(stdout, str) else stdout.decode('utf-8')))

    return '-D LIBJPEG_STATIC OPENSSL_LIBS="-llibssl -llibcrypto -lUser32 -lAdvapi32 -lGdi32 -lCrypt32"', ''

def package_build(config, target, build_dir, src_dir, version):
    import os, subprocess
    subprocess.check_call('nmake install INSTALL_ROOT=%s' % os.path.join(build_dir, 'wkhtmltox'), shell=True, cwd=os.path.join(build_dir, 'app'))

    nsis = _registry_value(r'SOFTWARE\NSIS')
    if not nsis or not os.path.exists(os.path.join(nsis, 'makensis.exe')):
        return

    msvc_ver = config['vagrant-targets'][target]['msvc_version']
    msvc_url = config['vagrant-targets'][target]['msvc_redist']
    nsi_loc  = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'wkhtmltox.nsi')
    license  = os.path.join(src_dir, 'LICENSE')

    subprocess.check_call('curl -fsSL -o vcredist.exe "%s"' % msvc_url, cwd=build_dir, shell=True)
    subprocess.check_call('"%s\makensis.exe" /NOCD /DVERSION=%s /DSIMPLE_VERSION=%s /DTARGET=%s /DMSVC=%s /DARCH=%s /DLICENSE=%s "%s"' % (
        nsis, '-'.join(version), _nsis_version(version[0]), target, msvc_ver, target.split('-')[-1], license, nsi_loc), shell=True, cwd=build_dir)
