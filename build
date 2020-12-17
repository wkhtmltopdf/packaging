#!/usr/bin/env python
#
# Copyright 2018-2020 wkhtmltopdf authors
#
# This file is part of wkhtmltopdf.
#
# wkhtmltopdf is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# wkhtmltopdf is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with wkhtmltopdf. If not, see <http://www.gnu.org/licenses/#LGPL>.

import argparse, copy, datetime, importlib, json, multiprocessing, os, subprocess, sys, yaml

def message(msg):
    sys.stdout.write(msg+'\n')
    sys.stdout.flush()

def shell(cmd, cwd=None):
    ret = subprocess.call(cmd, shell=True, cwd=cwd)
    if ret:
        message('%s\ncommand failed: exit code %d' % (cmd, ret))
        sys.exit(1)

def output(cmd, **args):
    try:
        text = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, **args).strip()
        return text if isinstance(text, str) else text.decode('utf-8')
    except:
        return None

def docker_images(config, targets, force):
    prefix = config['docker-prefix']
    images = []

    def pull(image, platform):
        if image in images:
            shell('docker rmi -f %s' % image)
        if platform != 'linux/amd64':
            if output('docker version --format "{{.Server.Experimental}}"') != 'true':
                message('Could not detect experimental: true in docker daemon, aborting.')
                sys.exit(1)
        shell('docker pull --platform %s %s' % (platform or 'linux/amd64', image))

    started_qemu = None
    for name in targets:
        if name not in config['docker-targets']:
            message('Unknown target specified: %s' % name)
            sys.exit(1)

        images = (output('docker images --format "{{.Repository}}:{{.Tag}}"') or '').strip().split('\n')
        params = config['docker-targets'][name]
        needed_qemu = params.get('qemu')
        if needed_qemu and started_qemu != needed_qemu:
            pull('aptman/qus:latest', needed_qemu)
            shell('docker run --rm --privileged aptman/qus:latest -- -r')
            shell('docker run --rm --privileged aptman/qus:latest -s -- -p')
            started_qemu = needed_qemu

        image = prefix+name
        args  = ' '.join('--build-arg %s=%s' % a for a in params['args'].items())
        if force or image not in images:
            if 'from' in params.get('args', {}):
                pull(params['args']['from'], params.get('platform') or 'linux/amd64')
            shell('docker build -f %s %s -t %s docker/' % (params['source'], args, image))

def get_version(src_dir, iteration):
    rel_ver = open(os.path.join(src_dir, 'VERSION'), 'r').read().strip()
    if '-' not in rel_ver:
        return (rel_ver, iteration)

    rel_ver, rel_tag = rel_ver.split('-', 1)
    describe = output('git describe --tags --long', cwd=src_dir)
    if not describe:
        today = datetime.datetime.now().strftime('%Y%m%d')
        return (rel_ver, '0.%s.%s' % (today, rel_tag))

    commit_on = output('git log -1 --format=%cd --date=format:%Y%m%d')
    prev_tag, offset, commit = describe.split('-')

    return (rel_ver, '0.%s.%s.%s.%s' % (commit_on, offset, rel_tag, commit[1:]))

def compile_docker(config, target, src_dir, tgt_dir, debug=False):
    if target not in config['docker-targets']:
        message('Unknown target: %s' % target)
        sys.exit(1)

    if not os.path.exists(os.path.join(src_dir, 'wkhtmltopdf.pro')):
        message('Not wkhtmltopdf source directory: %s' % src_dir)
        sys.exit(1)

    if not os.path.exists(os.path.join(src_dir, 'qt', 'configure')):
        message('Qt not present in wkhtmltopdf source: %s' %  src_dir)
        sys.exit(1)

    docker_images(config, [target], False)
    shell('mkdir -p %(tgt)s/app %(tgt)s/qt' % dict(tgt=tgt_dir))

    cross  = config['docker-targets'][target].get('cross_compile')
    dimage = '--user %d:%d %s%s' % (os.getuid(), os.getgid(), config['docker-prefix'], target)
    def dshell(wd, cmd):
        shell('docker run --rm -v%s:/src -v%s:/tgt -v%s:/pkg -w%s %s %s' % (
            os.path.abspath(src_dir), os.path.abspath(tgt_dir), os.getcwd(), wd, dimage, cmd))

    if not os.path.exists(os.path.join(tgt_dir, 'qt_configured')):
        qtconf = config['docker-targets'][target].get('qt_config', 'docker')
        dshell('/tgt/qt', '/src/qt/configure %s %s %s --prefix=/tgt/qt %s' % (
            config['qt-config']['common'].strip(),
            config['qt-config'][qtconf].strip(),
            config['qt-config']['debug'].strip() if debug else '',
            '-device-option CROSS_COMPILE=%s' % cross if cross else ''))
        shell('touch %s/qt_configured' % tgt_dir)

    dshell('/tgt/qt', 'make -j%d' % multiprocessing.cpu_count())

    shell('rm -fr %s/app/bin %s/wkhtmltox' % (tgt_dir, tgt_dir))
    if cross:
        dshell('/tgt/app', '/tgt/qt/bin/qmake -set CROSS_COMPILE %s' % cross)
    dshell('/tgt/app', '/tgt/qt/bin/qmake /src/wkhtmltopdf.pro CONFIG+=silent')
    dshell('/tgt/app', 'make install INSTALL_ROOT=/tgt/wkhtmltox')

    script = 'after_compile/%s.sh' % config['docker-targets'][target].get('after_compile', '')
    if os.path.exists(os.path.abspath(script)):
        dshell('/tgt/app', '/pkg/%s' % script)

def package_docker(config, target, src_dir, iteration, clean=False):
    tgt_dir = os.path.join('targets', target)
    if clean:
        shell('rm -fr %s' % tgt_dir)

    compile_docker(config, target, src_dir, tgt_dir)

    pkg_ver, pkg_iter = get_version(src_dir, iteration)
    output  = config['docker-targets'][target].get('output', 'tar')
    depend  = config['docker-targets'][target].get('depend', '')

    arch     = config['docker-targets'][target].get('arch')
    dimage   = '-e XZ_OPT=-9 --user %d:%d %s' % (os.getuid(), os.getgid(), config['fpm-image'])
    fversion = '--epoch 1 --version "%s" --iteration "%s.%s"' % (pkg_ver, pkg_iter, target.split('-')[0])
    fparams  = ' '.join('--%s "%s"' % (k, v) for k, v in config['fpm-params'].items())
    fdepend  = ' '.join('--depends "%s"' % p for p in depend.split() if p).strip()
    fpm_args = '%s -a %s -f -s dir -C %s/wkhtmltox %s %s %s' % (
        dimage, arch, target, fversion, fparams, fdepend)
    archive  = 'wkhtmltox-%s-%s.%s' % (pkg_ver, pkg_iter, target)

    if output == 'tar':
        shell('tar -cvf targets/%s.tar -C targets/%s wkhtmltox/' % (archive, target))
        shell('xz -fv9 targets/%s.tar' % archive)
    elif output == '7z':
        shell('rm -f targets/%s.7z' % archive)
        shell('cd targets/%s && 7z a ../%s.7z -mx9 wkhtmltox/' % (target, archive))
    elif output == 'deb':
        fdeb = '-t deb --deb-compression xz --provides wkhtmltopdf --conflicts wkhtmltopdf --replaces wkhtmltopdf --deb-shlibs "libwkhtmltox 0 wkhtmltox (>= 0.12.0)"'
        shell('docker run --rm -v%s:/tgt -w/tgt %s %s' % (os.path.abspath('targets'), fpm_args, fdeb))
    elif output in ('rpm', 'rpm:bzip2'):
        frpm = '-t rpm --rpm-compression %s' % ('xz' if output == 'rpm' else 'bzip2')
        shell('docker run --rm -v%s:/tgt -w/tgt %s %s' % (os.path.abspath('targets'), fpm_args, frpm))
    elif output in ('pacman'):
        fpacman = '-t pacman'
        fpm_args = fpm_args.replace('/usr/local', '/usr')
        shell('docker run --rm -v%s:/tgt -w/tgt %s %s' % (os.path.abspath('targets'), fpm_args, fpacman))
    elif output == 'lambda_zip':
        shell('rm -f targets/%s.zip' % archive)
        shell('cd targets/%s/wkhtmltox && zip -r ../../%s.zip *' % (target, archive))

    if clean:
        shell('rm -fr %s' % tgt_dir)

def build_vagrant(config, target, src_dir, iteration, clean=False, debug=False, version=None):
    if target not in config['vagrant-targets']:
        message('Unknown target: %s' % target)
        sys.exit(1)

    if not os.path.exists(os.path.join(src_dir, 'wkhtmltopdf.pro')):
        message('Not wkhtmltopdf source directory: %s' % src_dir)
        sys.exit(1)

    if not os.path.exists(os.path.join(src_dir, 'qt', 'configure')):
        message('Qt not present in wkhtmltopdf source: %s' %  src_dir)
        sys.exit(1)

    no_version_specified = version is None or version == ['-', '-']
    if version == ['-', '-']:
        version = get_version(src_dir, iteration)

    cfg  = config['vagrant-targets'][target]
    vm   = cfg['vm']
    base = '%s/%s' % (cfg['home_in_rsync'], target)

    src_dir = os.path.abspath(src_dir)
    tgt_dir = os.path.abspath('./targets' if no_version_specified else '../build')
    if not os.path.exists(tgt_dir):
        os.makedirs(tgt_dir)

    def outside_vm():
        cmd_args = '--version "%s" "%s"' % get_version(src_dir, iteration)

        if clean:
            shell('vagrant destroy -f %s' % vm, 'vagrant')
            cmd_args += ' --clean'
        if debug:
            cmd_args += ' --debug'

        shell('vagrant up %s' % vm, 'vagrant')
        shell('vagrant ssh-config %s > .vagrant/%s_config' % (vm, vm), 'vagrant')

        def rsync(flags, src, tgt):
            shell('rsync --info=progress2 -a -e "ssh -F vagrant/.vagrant/%s_config" %s %s/ %s:%s/%s' % (vm, flags, os.path.abspath(src), vm, base, tgt))

        shell('ssh -F vagrant/.vagrant/%s_config %s -- "bash -c \'mkdir -p %s\'"' % (vm, vm, base))
        rsync('--delete --exclude .git',    src_dir, 'src')
        rsync('--delete --exclude targets', '.',     'pkg')
        shell('ssh -F vagrant/.vagrant/%s_config %s -- python %s/pkg/build vagrant %s %s ../src' % (vm, vm, target, cmd_args, target))
        if not debug:
            shell('scp -F vagrant/.vagrant/%s_config %s:%s/wkhtmltox*.* %s' % (vm, vm, target, tgt_dir))
            shell('vagrant %s %s' % ('destroy -f' if clean else 'halt', vm), 'vagrant')

    def _conan_paths(key, cmd_arg):
        with open('conanbuildinfo.json', 'r') as f:
            config = json.load(f)
            paths  = []
            for dependency in config['dependencies']:
                for path in dependency[key]:
                    if path not in paths:
                        paths.append(path)
        return ' '.join('%s %s' % (cmd_arg, str(path)) for path in paths)

    def inside_vm():
        custom = importlib.import_module('vagrant.%s' % cfg.get('custom_build', vm))
        custom_cfg, custom_qmk = custom.prepare_build(config, target, tgt_dir, src_dir)

        os.environ['CONAN_USER_HOME'] = os.path.abspath('.')
        c_build = 'missing' if not clean else '*'
        c_debug = '-s build_type=Debug' if debug else ''
        shell('conan install . --profile %s --build "%s" %s' % (target, c_build, c_debug))

        shell('rm -fr app wkhtmltox ../wkhtmltox*.*', tgt_dir)
        for d in ('qt', 'app', 'wkhtmltox'):
            if not os.path.exists(os.path.join(tgt_dir, d)):
                os.makedirs(os.path.join(tgt_dir, d))
        if not os.path.exists(os.path.join(tgt_dir, 'qt_configured')):
            shell('%s %s %s %s %s %s %s' % (
                os.path.join(src_dir, 'qt', 'configure'),
                config['qt-config']['common'].strip(),
                config['qt-config'][cfg['qt_config']].strip(),
                config['qt-config']['debug'].strip() if debug else '',
                _conan_paths('include_paths', '-I'),
                _conan_paths('lib_paths', '-L'),
                custom_cfg), os.path.join(tgt_dir, 'qt'))
            shell('touch %s/qt_configured' % tgt_dir)

        make  = cfg.get('make', 'make -j%d' % multiprocessing.cpu_count())
        qmake = os.path.join(tgt_dir, 'qt', 'bin', 'qmake')
        shell(make, os.path.join(tgt_dir, 'qt'))
        shell('%s %s/wkhtmltopdf.pro CONFIG+=silent %s' % (qmake, src_dir, custom_qmk), os.path.join(tgt_dir, 'app'))
        shell(make, os.path.join(tgt_dir, 'app'))
        if not debug:
            custom.package_build(config, target, tgt_dir, src_dir, version)

    if version:
        inside_vm()
    else:
        outside_vm()

def list_targets(config):
    for target in sorted(config['docker-targets']):
        message('docker\t%s' % target)

    for target in sorted(config['vagrant-targets']):
        message('vagrant\t%s' % target)

def main():
    parser = argparse.ArgumentParser(prog='build')
    sub    = parser.add_subparsers(title='TARGETS', metavar='<target>')

    qemu = parser.add_mutually_exclusive_group()
    qemu.add_argument('--no-qemu', action='store_true', default=False, help='don\'t use QEMU')
    qemu.add_argument('--use-qemu', metavar='PLATFORM', help='use a specific QEMU platform on the host. The platform must be a "os/architecture(/variant)" value')

    docker = sub.add_parser('docker-images', help='build docker images')
    docker.add_argument('--force', action='store_true', default=False, help='force rebuild for all specified targets')
    docker.add_argument('targets', nargs='+', metavar='TARGET', help='targets for which to build images')

    docker.set_defaults(func=docker_images)

    compile = sub.add_parser('compile-docker', help='compile source via Docker image')
    compile.add_argument('target',  help='target to use for compilation')
    compile.add_argument('src_dir', help='directory which has wkhtmltopdf source code')
    compile.add_argument('tgt_dir', help='output directory')
    compile.add_argument('--debug', action='store_true', default=False, help='compile in debug mode')
    compile.set_defaults(func=compile_docker)

    package = sub.add_parser('package-docker', help='compile and package via Docker image')
    package.add_argument('target',  help='target to use for compilation')
    package.add_argument('src_dir', help='directory which has wkhtmltopdf source code')
    package.add_argument('--clean', action='store_true', default=False, help='perform clean build')
    package.add_argument('--iteration', default='1', help='iteration for release builds')
    package.set_defaults(func=package_docker)

    targets = sub.add_parser('list-targets', help='list all available targets')
    targets.set_defaults(func=list_targets)

    vagrant = sub.add_parser('vagrant', help='compile/package source via Vagrant VM')
    vagrant.add_argument('target',  help='target to use for compilation')
    vagrant.add_argument('src_dir', help='directory which has wkhtmltopdf source code')
    vagrant.add_argument('--clean', action='store_true', default=False, help='perform clean build')
    vagrant.add_argument('--debug', action='store_true', default=False, help='compile in debug mode')
    vagrant.add_argument('--version', nargs=2, metavar=('VER', 'ITER'), help='version to use when packaging inside VM')
    vagrant.add_argument('--iteration', metavar='RELITER', default='1', help='iteration for release builds')
    vagrant.set_defaults(func=build_vagrant)

    cli  = sys.argv[1:] if len(sys.argv) > 1 else ['-h']
    args = vars(parser.parse_args(cli))
    use_qemu = args.pop('use_qemu', None)
    no_qemu = args.pop('no_qemu')
    func = args.pop('func', None)
    bdir = os.path.dirname(os.path.abspath(__file__))

    if func is None:
        parser.print_help()
        exit(1)

    with open(os.path.join(bdir, 'build.yml'), 'r') as f:
        os.chdir(bdir)
        config = yaml.safe_load(f.read())
        # expand matrix into separate per-arch targets
        for name, target in list(config['docker-targets'].items()):
            if 'qemu' in target and no_qemu:
                del target['qemu']
            if use_qemu is not None:
                target['qemu'] = use_qemu
            distro_arch = target.get('matrix')
            if not distro_arch:
                continue
            for arch in distro_arch:
                new_target = copy.deepcopy(target)
                del new_target['matrix']
                new_target['arch'] = arch
                new_target['platform'] = config['matrix-platforms'][arch]
                if use_qemu is not None:
                    new_target['qemu'] = use_qemu
                elif not no_qemu:
                    # keep the old behavior for convienience
                    # workaround https://bugs.launchpad.net/qemu/+bug/1805913 for 32-bit targets
                    new_target['qemu'] = 'linux/amd64' if new_target['platform'] not in ('linux/arm/v5', 'linux/arm/v7') else 'linux/386'
                config['docker-targets']['%s-%s' % (name, arch)] = new_target
            del config['docker-targets'][name]
        func(config, **args)

if __name__ == '__main__':
    main()
