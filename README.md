# 软件工程个人项目：论文查重（SimHash）

广东工业大学 计算机学院 计科24级78班 ｜ 作业 15702 ｜ 学号 **3124004167**

设计一个论文查重算法：给一个原文文件和一个经过增删改的抄袭版论文文件，在答案文件中输出重复率。

## 运行方式

```bash
python main.py [原文文件] [抄袭版论文的文件] [答案文件]
```

三个参数都是**文件的绝对路径**（路径中不含空格），答案文件输出为**浮点型，精确到小数点后两位**。

```bash
python main.py orig.txt orig_add.txt ans.txt
cat ans.txt     # 例如 0.84
```

## 环境

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r 3124004167/requirements.txt
```

Python 3.8+。

## 目录结构

```
3124004167/
├── main.py           # 程序入口：命令行参数解析、SimHash、海明距离、写答案文件
├── test.py           # 单元测试（unittest，15 个用例，含边界与异常场景）
├── requirements.txt  # 依赖（jieba）
├── PSP.md            # PSP 2.1：预估耗时与实际耗时
├── orig.txt          # 样例：原文
└── orig_add.txt      # 样例：抄袭版论文
```

## 实现要点

- **SimHash**：jieba 分词 → 词哈希（md5，64 位）→ 按位加权降维 → 64 位文本指纹
- **相似度**：海明距离 `d = popcount(h1 ^ h2)`，`重复率 = 1 - d / 64`，保留两位小数
- **异常处理**：命令行参数个数错误、文件不存在、编码错误、空文本（避免除零与假的 100% 相似度）
- **注意**：词哈希使用 `hashlib.md5` 而非内置 `hash()` —— 内置 `hash()` 对字符串按进程随机加盐，会导致指纹不可复现

## 测试

```bash
cd 3124004167
python -m unittest -v                    # 单元测试
coverage run --branch -m unittest && coverage report -m    # 覆盖率
python -m cProfile -s tottime main.py orig.txt orig_add.txt ans.txt   # 性能分析
```

## 约束

不连接网络、不读写除指定输入输出文件以外的文件；单次运行 5 秒内给出结果，内存占用远低于 2048MB。
