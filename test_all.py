import os
import tempfile
import unittest
from collections import Counter

from archiver import FileArchiver, FileEntry
from compressor import ShannonFanoCompressor
from decompressor import ShannonFanoDecompressor
from access_control import AccessControl
from nodes import ShannonFanoNode


class TestNodes(unittest.TestCase):
    def test_node_creation_with_symbol(self):
        node = ShannonFanoNode(symbol=65, frequency=10)
        self.assertEqual(node.symbol, 65)
        self.assertEqual(node.frequency, 10)
        self.assertIsNone(node.left)
        self.assertIsNone(node.right)

    def test_node_creation_internal(self):
        node = ShannonFanoNode(frequency=20)
        self.assertIsNone(node.symbol)
        self.assertEqual(node.frequency, 20)

    def test_node_repr_printable_symbol(self):
        node = ShannonFanoNode(symbol=65, frequency=10)
        repr_str = repr(node)
        self.assertIn("A", repr_str)
        self.assertIn("freq=10", repr_str)

    def test_node_repr_internal_node(self):
        node = ShannonFanoNode(frequency=15)
        repr_str = repr(node)
        self.assertIn("internal", repr_str)
        self.assertIn("freq=15", repr_str)

    def test_node_tree_structure(self):
        root = ShannonFanoNode(frequency=10)
        left = ShannonFanoNode(symbol=65, frequency=6)
        right = ShannonFanoNode(symbol=66, frequency=4)
        root.left = left
        root.right = right
        self.assertEqual(root.left, left)
        self.assertEqual(root.right, right)


class TestCompressor(unittest.TestCase):
    def setUp(self):
        self.compressor = ShannonFanoCompressor()

    def test_calculate_frequencies(self):
        test_data = b"hello world"
        frequencies = self.compressor.calculate_frequencies(test_data)
        self.assertEqual(frequencies[ord('l')], 3)
        self.assertEqual(frequencies[ord('o')], 2)
        self.assertEqual(frequencies[ord(' ')], 1)

    def test_build_shannon_fano_tree(self):
        frequencies = {65: 3, 66: 2, 67: 1}
        root = self.compressor.build_shannon_fano_tree(frequencies)
        self.assertIsInstance(root, ShannonFanoNode)
        self.assertEqual(root.frequency, 6)

    def test_generate_codes(self):
        root = ShannonFanoNode(frequency=6)
        root.left = ShannonFanoNode(symbol=65, frequency=3)
        root.right = ShannonFanoNode(frequency=3)
        root.right.left = ShannonFanoNode(symbol=66, frequency=2)
        root.right.right = ShannonFanoNode(symbol=67, frequency=1)
        self.compressor.generate_codes(root)
        self.assertIn(65, self.compressor.codes)
        self.assertIn(66, self.compressor.codes)
        self.assertIn(67, self.compressor.codes)
        for code in self.compressor.codes.values():
            self.assertTrue(all(bit in '01' for bit in code))

    def test_compress_data(self):
        test_data = b"TEST DATA"
        compressed_data, codes, padding = self.compressor.compress_data(test_data)
        self.assertIsInstance(compressed_data, bytes)
        self.assertIsInstance(codes, dict)
        self.assertIsInstance(padding, int)
        self.assertGreaterEqual(padding, 0)
        self.assertLessEqual(padding, 7)

    def test_compress_empty_data(self):
        compressed_data, codes, padding = self.compressor.compress_data(b"")
        self.assertEqual(compressed_data, b"")
        self.assertEqual(codes, {})
        self.assertEqual(padding, 0)

    def test_serialize_deserialize_codes(self):
        test_codes = {65: '101', 66: '1101', 67: '0'}
        serialized = self.compressor._serialize_codes(test_codes)
        self.assertIsInstance(serialized, bytes)
        decompressor = ShannonFanoDecompressor()
        deserialized_codes, _ = decompressor._deserialize_codes(serialized)
        self.assertEqual(deserialized_codes, test_codes)


class TestDecompressor(unittest.TestCase):
    def setUp(self):
        self.decompressor = ShannonFanoDecompressor()

    def test_deserialize_codes(self):
        test_codes = {65: '101', 66: '110'}
        compressor = ShannonFanoCompressor()
        serialized = compressor._serialize_codes(test_codes)
        codes, offset = self.decompressor._deserialize_codes(serialized)
        self.assertEqual(codes, test_codes)

    def test_bytes_to_bits(self):
        test_bytes = b'\xf0'
        bits = self.decompressor._bytes_to_bits(test_bytes, 4)
        self.assertEqual(bits, '1111')
        bits = self.decompressor._bytes_to_bits(test_bytes, 6)
        self.assertEqual(bits, '111100')

    def test_decompress_simple_data(self):
        compressed_data = b'\x58'
        codes = {65: '0', 66: '10', 67: '11'}
        padding_bits = 2
        original_size = 4
        result = self.decompressor.decompress_data(
            compressed_data, codes, padding_bits, original_size
        )
        self.assertEqual(result, b'ABCA')

    def test_decompress_empty_data(self):
        result = self.decompressor.decompress_data(b"", {}, 0, 0)
        self.assertEqual(result, b"")


class TestAccessControl(unittest.TestCase):
    def setUp(self):
        self.access_control = AccessControl()

    def test_set_and_verify_password(self):
        password = "test_password_123"
        password_hash = self.access_control.set_password(password)
        self.assertIsInstance(password_hash, bytes)
        self.assertEqual(len(password_hash), 48)
        result = self.access_control.verify_password(password, password_hash)
        self.assertTrue(result)

    def test_verify_wrong_password(self):
        password = "correct_password"
        stored_hash = self.access_control.set_password(password)
        result = self.access_control.verify_password("wrong_password", stored_hash)
        self.assertFalse(result)

    def test_verify_invalid_hash(self):
        result = self.access_control.verify_password("password", b"short")
        self.assertFalse(result)
        result = self.access_control.verify_password("password", None)
        self.assertFalse(result)

    def test_is_protected(self):
        result = self.access_control.is_protected(None)
        self.assertFalse(result)
        password_hash = self.access_control.set_password("test")
        result = self.access_control.is_protected(password_hash)
        self.assertTrue(result)


class TestArchiver(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.archiver = FileArchiver()
        self.file1 = os.path.join(self.test_dir, "test1.txt")
        self.file2 = os.path.join(self.test_dir, "test2.txt")
        with open(self.file1, 'w', encoding='utf-8') as f:
            f.write("Hello World! This is test file 1.")
        with open(self.file2, 'w', encoding='utf-8') as f:
            f.write("Test content for file number 2.")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)
        for file in [self.file1, self.file2]:
            archive_path = file + '.sf'
            if os.path.exists(archive_path):
                os.remove(archive_path)
        if os.path.exists("archive.sf"):
            os.remove("archive.sf")
        for filename in ["test1.txt", "test2.txt"]:
            if os.path.exists(filename):
                os.remove(filename)

    def test_file_entry_creation(self):
        entry = FileEntry(
            filename="test.txt",
            size=100,
            compressed_size=50,
            metadata={'size': 100, 'mtime': 123456789},
            codes={65: '101', 66: '110'},
            padding=2
        )
        self.assertEqual(entry.filename, "test.txt")
        self.assertEqual(entry.size, 100)
        self.assertEqual(entry.compressed_size, 50)
        self.assertEqual(entry.padding, 2)

    def test_get_file_metadata(self):
        metadata = self.archiver._get_file_metadata(self.file1)
        self.assertIn('size', metadata)
        self.assertIn('mtime', metadata)
        self.assertIn('atime', metadata)
        self.assertIn('mode', metadata)
        self.assertGreater(metadata['size'], 0)

    def test_compress_single_file(self):
        result = self.archiver.compress_files([self.file1])
        self.assertTrue(result)
        archive_path = self.file1 + '.sf'
        self.assertTrue(os.path.exists(archive_path))

    def test_compress_multiple_files(self):
        result = self.archiver.compress_files([self.file1, self.file2])
        self.assertTrue(result)
        self.assertTrue(os.path.exists("archive.sf"))

    def test_compress_with_password(self):
        result = self.archiver.compress_files([self.file1], "testpassword")
        self.assertTrue(result)
        archive_path = self.file1 + '.sf'
        self.assertTrue(os.path.exists(archive_path))

    def test_decompress_single_file(self):
        self.archiver.compress_files([self.file1])
        archive_path = self.file1 + '.sf'
        result = self.archiver.decompress_file(archive_path)
        self.assertTrue(result)
        self.assertTrue(os.path.exists("test1.txt"))

    def test_decompress_with_password(self):
        self.archiver.compress_files([self.file1], "mypassword")
        archive_path = self.file1 + '.sf'
        result = self.archiver.decompress_file(archive_path, "mypassword")
        self.assertTrue(result)
        self.assertTrue(os.path.exists("test1.txt"))


def run_all_tests():
    print("ЗАПУСК ВСЕХ ТЕСТОВ АРХИВАТОРА SHANNON-FANO")
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(loader.loadTestsFromTestCase(TestNodes))
    test_suite.addTests(loader.loadTestsFromTestCase(TestCompressor))
    test_suite.addTests(loader.loadTestsFromTestCase(TestDecompressor))
    test_suite.addTests(loader.loadTestsFromTestCase(TestAccessControl))
    test_suite.addTests(loader.loadTestsFromTestCase(TestArchiver))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    print(f"ТЕСТЫ ЗАВЕРШЕНЫ: {result.testsRun} тестов выполнено")
    print(f"УСПЕШНО: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"ПРОВАЛЕНО: {len(result.failures)}")
    print(f"ОШИБОК: {len(result.errors)}")
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)