import sys
import os
from archiver import FileArchiver


def main():
    if '--help' in sys.argv or '-h' in sys.argv:
        print("Архиватор на основе алгоритма Shannon-Fano")
        print("Использовать следующим образом:")
        print("python main.py compress файл_1 файл_2 ... файл_n")
        print("python main.py compress dir")
        print("python main.py decompress архив.sf")
        print("Если сильно хочется, можно добавить:")
        print("  -p ваш_пароль")
        return
    archiver = FileArchiver()
    command = sys.argv[1]
    if command == 'compress':
        password = None
        files = []
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == '-p' and i + 1 < len(sys.argv):
                password = sys.argv[i + 1]
                i += 2
            else:
                files.append(sys.argv[i])
                i += 1
        if not files:
            print("Ошибка: не указаны файлы для архивации")
            return
        archiver.compress_files(files, password)
    elif command == 'decompress':
        if len(sys.argv) < 3:
            print("Ошибка: укажите архив для распаковки")
            return
        input_file = sys.argv[2]
        password = None
        if len(sys.argv) > 4 and sys.argv[3] == '-p':
            password = sys.argv[4]
        else:
            print("Проверка архива...")
        archiver.decompress_file(input_file, password)
    else:
        print("Неизвестная команда. Используйте 'compress' или 'decompress'")


if __name__ == '__main__':
    main()