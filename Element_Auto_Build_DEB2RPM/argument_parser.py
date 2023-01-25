from argparse import ArgumentParser


class Parser(object):

    def __init__(self, version):
        self._parser = ArgumentParser(prog='element-auto-build-deb2rpm', add_help=True, epilog='Dev-Elektro © 2023')
        self._add_arguments(version)

    def _add_arguments(self, version):
        self._parser.add_argument('-v', '--version', action='version', version=version,
                                  help="Показать версию скрипта")
        self._parser.add_argument('path', help='Путь сохранения rpm пакета')
        self._parser.add_argument('-i', '--img', type=str, default=None, help='Путь к jpg файлу для фона Element')

    def parse(self, argv):
        return self._parser.parse_args()
