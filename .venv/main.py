import sys
from archiver import FileArchiver


def main():
    if len(sys.argv) < 3:
        print("Использование:")
        print("python main.py compress file_name")
        print("python main.py decompress file_name")
        sys.exit(1)

    archiver = FileArchiver()
    command = sys.argv[1]
    input_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None

    if command == 'compress':
        archiver.compress_file(input_file, output_file)
    elif command == 'decompress':
        archiver.decompress_file(input_file, output_file)
    else:
        print("Неизвестная команда. Используйте 'compress' или 'decompress'")


if __name__ == '__main__':
    main()