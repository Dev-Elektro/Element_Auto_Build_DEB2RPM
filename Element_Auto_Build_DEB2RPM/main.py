import os
import subprocess
import re
import sys

import requests
from tqdm import tqdm
from bs4 import BeautifulSoup

from .argument_parser import Parser


def check_version(cmd: str):
    v = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    stdout = v.stdout.decode()
    return v.returncode, stdout


def get_link_for_latest_version():
    url = 'https://packages-old.element.io/debian/pool/main/e/element-desktop/'
    params = {'C': 'M', 'O': 'D'}
    r = requests.get(url, params=params)
    if r.status_code != 200:
        return 0
    soup = BeautifulSoup(r.text, 'lxml')
    table = soup.find('table', {'id': 'list'})
    link_list = table.find_all('a')
    if len(link_list) > 7:
        link_list = link_list[7:]
        href = url + link_list[0].get('href')
        version = re.findall(r"\d+.\d+.\d+", href)[0]
        return version, href


def download_file(url: str, path: str):
    local_filename = url.split('/')[-1]
    path_full = os.path.join(path, local_filename)
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        progress_bar = tqdm(total=int(r.headers.get('content-length', 0)), unit='iB', unit_scale=True)
        with open(path_full, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                progress_bar.update(len(chunk))
                f.write(chunk)
            progress_bar.clear()
            progress_bar.close()
    return path_full


def create_tree_dirs():
    home = os.getenv("HOME")
    dirs = ['rpmbuild', 'rpmbuild/SOURCES', 'rpmbuild/BUILD', 'rpmbuild/BUILDROOT', 'rpmbuild/RPMS', 'rpmbuild/SPECS']
    for i in dirs:
        path = os.path.join(home, i)
        if not os.path.exists(path):
            os.mkdir(path)


def create_spec_file(path: str, name: str, version: str, source: str, img: str = None):
    buf = f"Name:           {name}\n"
    buf += f"Version:        {version}\n"
    buf += """\
    Release:        1%{?dist}
    Summary:        Element   

    License:        Apache-2.0       
    URL:            https://element.io/
    
    AutoReqProv:    no

    %description
    Клиент Element для рабочего стола by EFKO
    
    %prep
    """
    buf += "ar -x %{_sourcedir}/" + source + " data.tar.xz\n"
    buf += """\
    tar -xJf data.tar.xz
    rm -f data.tar.xz
    snap run asar e opt/Element/resources/webapp.asar _temp
    sed -i "s/matrix-client.matrix.org/matrix.efko.ru/" _temp/config.json
    sed -i "s/matrix.org/matrix.efko.ru/" _temp/config.json
    """
    if img and os.path.exists(img):
        buf += f"cp {img} _temp/themes/element/img/backgrounds/lake.jpg\n"
    buf += """snap run asar p _temp opt/Element/resources/webapp.asar
    rm -rf _temp
    
    %install
    cp -r opt %{buildroot}
    cp -r usr %{buildroot}
    rm -rf %{_builddir}/*

    %files
    /opt/Element/*
    %{_datadir}/applications/element-desktop.desktop
    %{_datadir}/doc/element-desktop/changelog.gz
    %{_datadir}/icons/*

    %post
    ln -sf '/opt/Element/element-desktop' '/usr/bin/element-desktop'
    chmod 4755 '/opt/Element/chrome-sandbox' || true
    update-mime-database /usr/share/mime || true
    update-desktop-database /usr/share/applications || true
    """
    buf = re.sub(r'^ {4}', r'', buf, flags=re.M)
    path = os.path.join(path, name + '.spec')
    with open(path, 'w') as fp:
        fp.write(buf)
    return path


def main():
    parser = Parser('Version: 0.0.1')
    known_args = parser.parse(sys.argv)

    list_command = ['rpmbuild', 'snap', 'snap run asar']
    for i in list_command:
        res, out = check_version(i + ' --version')
        if res != 0:
            print(f'Not found: {i}', file=sys.stderr)
            sys.exit(1)

    print("Получаем ссылку на последнюю версию Element: ")
    version, href = get_link_for_latest_version()
    print(version)
    if os.path.exists(os.path.join(known_args.path, f'element-desktop-{version}-1.el7.x86_64.rpm')):
        print('Текущая версия уже собрана.')
        sys.exit(0)
    home = os.getenv("HOME")
    print("Создание каталогов для сборки")
    create_tree_dirs()
    print("Загрузка deb пакета")
    download_file(href, os.path.join(home, 'rpmbuild/SOURCES'))
    print("Создание spec файла")
    spec = create_spec_file(os.path.join(home, 'rpmbuild/SPECS'), 'element-desktop', version, href.split('/')[-1],
                            known_args.img)
    print("Сборка rpm пакета")
    v = subprocess.run(f"rpmbuild -bb {spec}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if v.returncode != 0:
        print(v.stderr.decode(), file=sys.stderr)
        print('Ошибка сборки rpm пакета.', file=sys.stderr)
        subprocess.run('rm -rf ~/rpmbuild', shell=True)
        sys.exit(1)
    print(f"Копирование rpm пакета > {known_args.path}element-desktop-{version}-1.el7.x86_64.rpm")
    v = subprocess.run(f'cp ~/rpmbuild/RPMS/x86_64/element-desktop-{version}-1.el7.x86_64.rpm {known_args.path}',
                   shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    print("Очистка")
    subprocess.run('rm -rf ~/rpmbuild', shell=True)
    if v.returncode != 0:
        print(v.stderr.decode(), file=sys.stderr)
        print('Ошибка копирования rpm пакета.', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
