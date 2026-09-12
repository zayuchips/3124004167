"""main.py 的单元测试。

要求：至少 10 个用例（作业原文），先跑测试看它失败（RED），再实现 main.py 里的 TODO（GREEN）。
运行：python -m unittest -v
覆盖率：coverage run -m unittest && coverage report -m && coverage html  # 打开 htmlcov/index.html 截图
"""

import os
import tempfile
import unittest

from main import (
    hamming_distance,
    parse_args,
    read_text,
    similarity,
    simhash,
    tokenize,
    write_result,
)

TEXT_A = "软件工程是一门研究用工程化方法构建和维护有效的、实用的和高质量的软件的学科。"
TEXT_A_PARA = "软件工程是一门利用工程化手段开发并维护高效、可用、高质量软件的学科。"
TEXT_A_NEAR = "软件工程是一门研究用工程化方法构建和维护有效的实用的和高质量的软件的学科。"
TEXT_B = "今天天气很好，适合出门散步。"
TEXT_LONG = TEXT_A * 500


class TestTokenizer(unittest.TestCase):
    def test_drops_punctuation_and_single_chars(self):
        """分词要去标点、过滤单字（“的/了/是”缺乏区分度）。"""
        words = tokenize("今天，天气很好！！！")
        self.assertNotIn("，", words)
        self.assertNotIn("！", words)
        self.assertTrue(all(len(w) > 1 for w in words))

    def test_blank_text_has_no_words(self):
        self.assertEqual(tokenize("   \n\t "), [])


class TestSimHashCore(unittest.TestCase):
    def test_identical_text_distance_zero(self):
        """完全相同文本 → 距离 0、相似度 1.00。"""
        d = hamming_distance(simhash(TEXT_A), simhash(TEXT_A))
        self.assertEqual(d, 0)
        self.assertEqual(similarity(d), 1.0)

    def test_family_friendly_text_small_distance(self):
        """只改标点/虚词的版本，距离应该很小（这是查重能用的前提）。"""
        d = hamming_distance(simhash(TEXT_A), simhash(TEXT_A_NEAR))
        self.assertLessEqual(d, 16, "近乎相同的文本不应被判为不相似")

    def test_rewritten_text_between(self):
        """改写过的文本：比无关文本更相似，但不等于 1.0。"""
        d_rewritten = hamming_distance(simhash(TEXT_A), simhash(TEXT_A_PARA))
        d_unrelated = hamming_distance(simhash(TEXT_A), simhash(TEXT_B))
        self.assertLess(d_rewritten, d_unrelated)

    def test_unrelated_text_large_distance(self):
        """完全无关文本 → 距离明显大于阈值、相似度偏低。"""
        d = hamming_distance(simhash(TEXT_A), simhash(TEXT_B))
        self.assertGreater(d, 16)
        self.assertLess(similarity(d), 0.8)

    def test_deterministic_across_calls(self):
        """同一文本的指纹必须可复现 —— 这条例行抓“用了内置 hash()”的坑。"""
        self.assertEqual(simhash(TEXT_A), simhash(TEXT_A))
        self.assertEqual(simhash(TEXT_LONG), simhash(TEXT_LONG))

    def test_similarity_is_two_decimals(self):
        """答案要求精确到小数点后两位。"""
        for d in range(0, 65):
            self.assertEqual(similarity(d), round(similarity(d), 2))
        self.assertEqual(similarity(0), 1.0)
        self.assertEqual(similarity(64), 0.0)

    def test_long_text_performance_budget(self):
        """长文本也不能慢（评测要求 5 秒内出结果）。"""
        import time

        start = time.time()
        simhash(TEXT_LONG)
        self.assertLess(time.time() - start, 3.0)


class TestBoundary(unittest.TestCase):
    def test_empty_text_raises(self):
        """空文本/纯空白必须报错，不能返回 0（否则会得到假的 100%）。"""
        with self.assertRaises(ValueError):
            simhash("   ")

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            read_text("not_exist_不存在的文件.txt")

    def test_bad_encoding_raises(self):
        """非 UTF-8 文件要给出可读异常，而不是崩栈。"""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write("这是一个 GBK 文件".encode("gbk"))
            path = f.name
        try:
            with self.assertRaises(UnicodeDecodeError):
                read_text(path)
        finally:
            os.unlink(path)

    def test_parse_args_rejects_wrong_count(self):
        """参数个数不对要以“用法提示 + 退出码 1”结束，不能抛 Traceback。"""
        with self.assertRaises(SystemExit) as ctx:
            parse_args(["only_one_arg.txt"])
        self.assertEqual(ctx.exception.code, 1)

    def test_parse_args_ok(self):
        self.assertEqual(
            parse_args(["a.txt", "b.txt", "c.txt"]), ("a.txt", "b.txt", "c.txt")
        )


class TestOutput(unittest.TestCase):
    def test_write_result_two_decimals(self):
        """答案文件里必须是保留两位小数的浮点。"""
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "ans.txt")
            write_result(path, 0.8421)
            with open(path, encoding="utf-8") as f:
                self.assertEqual(f.read().strip(), "0.84")


if __name__ == "__main__":
    unittest.main(verbosity=2)
