Архиватор Shannon-Fano
Назначение: Сжатие и распаковка файлов алгоритмом Шеннона-Фано

Использование:
python main.py compress file_name - для архивации
python main.py decompress filename.sf - для разархивации
python main.py --help - для справки



Структура файлов:

main.py
Обработка аргументов командной строки
Создание FileArchiver
Вызов compress_file() или decompress_file()

nodes.py
Класс ShannonFanoNode:
__init__() - создание узла (символ, частота)
__repr__() - строковое представление

compressor.py
Класс ShannonFanoCompressor:
calculate_frequencies() - подсчет частот байтов
build_shannon_fano_tree() - рекурсивное построение дерева
generate_codes() - обход дерева для генерации кодов
compress_data() - кодирование данных в битовую последовательность
_serialize_codes() - упаковка таблицы кодов в байты
_bits_to_bytes() - преобразование битовой строки в байты

decompressor.py
Класс ShannonFanoDecompressor:
_deserialize_codes() - распаковка таблицы кодов из архива
_bytes_to_bits() - преобразование байтов в битовую строку
decompress_data() - декодирование битовой последовательности

file_archiver.py
Класс FileArchiver:
compress_file() - чтение файла, сжатие, запись архива
decompress_file() - чтение архива, проверка сигнатуры, распаковка

Формат архива: сигнатура SFv1 + имя файла + размер + таблица кодов + сжатые данные