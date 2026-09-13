from __future__ import annotations

import hashlib
import re
import sys
from collections import Counter

import jieba

# 指纹位数：64 位是 SimHash 的常见选择（比值分辨率 1/64 ≈ 0.0156，够用且好算）
BITS = 64
# 相似判定阈值：海明距离 <= 16 认为「相似」。这只是经验值，写进博客时要说明口径
SIMILAR_THRESHOLD = 16
# 只保留汉字、英文字母、数字，其它（标点/空白/表情）统一换成空格
_CLEAN_PATTERN = re.compile(r"[^\u4e00-\u9fa5A-Za-z0-9]+")

#读文件
def read_text(path:str)->str:
    try:
        with open(path,encoding="utf-8")as file:
            return file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"文件不存在：{path}")from None


#用jieba分词把文本变成词列表
def tokenize(text: str) -> list[str]:
    cleaned=_CLEAN_PATTERN.sub(" ",text)
    words=jieba.lcut(cleaned)
    return [word for word in words if len(word)>1]


#通过md5哈希函数把词变成整数
def word_hash(word:str,bits:int=BITS)->int:
    digest=hashlib.md5(word.encode("utf-8")).hexdigest()
    return int(digest,16)&((1<<bits)-1)


#生成指纹，数频次，出现频次越高，对指纹影响越大
def simhash(text: str,bits: int=BITS)->int:
    words= tokenize(text)
    if not words:
        raise ValueError("文本没有有效词，无法计算 SimHash")

    weights=Counter(words)
    vector=[0] * bits
    for word,weight in weights.items():
        word_h =word_hash(word,bits)
        for i in range(bits):
            if(word_h>>i)&1:
                vector[i]+=weight
            else:
                vector[i]-=weight
    fingerprint=0
    for i in range(bits):
        if vector[i]>0:
            fingerprint|=(1<<i)
    return fingerprint


#海明距离，两指纹有多少位不同
def hamming_distance(h1:int,h2: int)->int:
    return bin(h1^h2).count("1")     #数有几位异或得1


#海明距离->重复率
"""海明距离转换为重复率

完全相同的文本，海明距离为 0，重复率为 1.0；
完全不同的文本，海明距离为 BITS，重复率为 0.0
"""
def similarity(dist: int,bits: int=BITS)->float:
    return round(1-dist/bits,2)


#校验命令行参数
"""
参数个数不是 3 时：打印用法并 sys.exit(1)（退出码 1 表示出错退出）
"""
def parse_args(argv: list[str]) ->tuple[str, str, str]:
    if len(argv) !=3:
        print(
            "用法：python main.py [原文文件] [抄袭版论文的文件] [答案文件]",
            file =sys.stderr
        )
        sys.exit(1)
    return argv[0],argv[1],argv[2]


#写答案
def write_result(path: str,value: float)-> None:
    with open(path,"w",encoding="utf-8")as file:
        file.write(f"{value:.2f}")


#
def main(argv: list[str] | None=None)-> int:
    #允许测试直接穿参数列表
    args =sys.argv[1:] if argv is None else list(argv)

    #参数椒盐
    orig_path, copy_path, ans_path = parse_args(args)

    #读文件
    try:
        orig_text = read_text(orig_path)
        copy_text = read_text(copy_path)
    except FileNotFoundError as err:
        print(f"错误：{err}", file=sys.stderr)
        return 1
    except UnicodeDecodeError:

        print("错误：文件不是 UTF-8 编码,请先另存为 UTF-8 再试", file=sys.stderr)
        return 1

    #计算指纹+重复率
    # 扩展功能：两份文件内容完全相同时复用同一个指纹，省掉第二次分词
    same_text = bool(orig_text.strip()) and orig_text == copy_text
    try:
        orig_hash = simhash(orig_text)
        if same_text:
            copy_hash = orig_hash
            print("提示：两份文件内容完全相同，已跳过第二次计算", file=sys.stderr)
        else:
            copy_hash = simhash(copy_text)

    except ValueError:
        #如果有一方，清洗后没有可用词，就按【完全不重复】处理
        #写入0.00
        print("提示：有一方文本没有有效词，按完全不重复处理", file=sys.stderr)
        rate= 0.0
        orig_hash =copy_hash =None
        distance =BITS #按完全不同处理
    else:
        distance = hamming_distance(orig_hash, copy_hash)
        rate = similarity(distance)

    #写入答案文件
    try:
        write_result(ans_path, rate)
    except OSError as err:
        print(f"错误：写入答案文件失败：{err}", file=sys.stderr)
        return 1

    #在终端输出可读的结果
    if orig_hash is not None:
        print(f"原文指纹:{orig_hash:#018x}")
        print(f"待比对指纹:{copy_hash:#018x}")
    print(f"海明距离:{distance}(共{BITS}位)")
    print(f"重复率:{rate:.2f}")
    verdict = "相似" if distance <= SIMILAR_THRESHOLD else "不相似"
    print(f"判定:{verdict}(阈值:海明距离≤{SIMILAR_THRESHOLD})")
    print(f"已写入答案文件:{ans_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
    #只有【直接运行】才会执行 main()，import 时不会执行
