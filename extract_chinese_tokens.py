#!/usr/bin/env python3
"""
GPT-4o 中文 Token 提取工具
从 tiktoken 的 o200k_base encoding 提取并分析所有包含中文字符的 tokens
输出包含 2+ 中文字的长词，供人工审查
"""

import tiktoken
import csv
import re
from tqdm import tqdm


def count_chinese_chars(text):
    """计算文本中的中文字符数量（包括繁简体）"""
    chinese_pattern = re.compile(
        r'[\u4e00-\u9fff\u3400-\u4dbf\u20000-\u2a6df\u2a700-\u2b73f'
        r'\u2b740-\u2b81f\u2b820-\u2ceaf\uf900-\ufaff\u3300-\u33ff]'
    )
    return len(chinese_pattern.findall(text))


def has_chinese(text):
    """检查文本是否包含中文字符"""
    return any(0x4e00 <= ord(c) <= 0x9fff for c in text)


def extract_chinese_tokens(min_chinese_chars=2):
    """
    提取并分析包含中文的 tokens

    Args:
        min_chinese_chars: 最小中文字符数，默认为 2

    Returns:
        包含 token 信息的列表
    """
    print("正在加载 tiktoken o200k_base encoding...")
    enc = tiktoken.get_encoding("o200k_base")
    vocab_size = enc.n_vocab

    print(f"词汇表大小: {vocab_size:,} tokens")
    print(f"\n开始提取包含 {min_chinese_chars}+ 中文字的 tokens...\n")

    # 第一步：提取所有 tokens 并计算字节长度
    length_dict = {}
    for i in tqdm(range(vocab_size), desc="计算 token 长度"):
        try:
            token_bytes = enc.decode_single_token_bytes(i)
            length_dict[i] = len(token_bytes)
        except:
            pass

    # 按字节长度排序（从长到短）
    sorted_tokens = sorted(length_dict.items(), key=lambda t: -t[1])

    # 第二步：筛选中文 tokens
    chinese_tokens = []
    chinese_count_distribution = {}

    for token_id, byte_length in tqdm(sorted_tokens, desc="筛选中文 tokens"):
        try:
            token_str = enc.decode([token_id])

            # 检查是否包含中文
            if has_chinese(token_str):
                chinese_count = count_chinese_chars(token_str)

                # 只保留符合最小中文字数要求的 tokens
                if chinese_count >= min_chinese_chars:
                    token_info = {
                        'id': token_id,
                        'token': token_str,
                        'chinese_count': chinese_count,
                        'total_length': len(token_str),
                        'byte_length': byte_length
                    }
                    chinese_tokens.append(token_info)

                    # 统计分布
                    chinese_count_distribution[chinese_count] = \
                        chinese_count_distribution.get(chinese_count, 0) + 1
        except:
            pass

    # 按中文字数排序（从多到少），中文字数相同则按 token 内容排序
    chinese_tokens.sort(key=lambda x: (-x['chinese_count'], x['token']))

    return chinese_tokens, chinese_count_distribution


def save_results(tokens, min_chinese_chars=2):
    """保存结果到 txt 和 csv 文件"""

    # 输出为纯文本
    txt_filename = f'all_chinese_tokens_{min_chinese_chars}plus.txt'
    with open(txt_filename, 'w', encoding='utf-8') as f:
        f.write(f"# GPT-4o (o200k_base) - 所有 {min_chinese_chars}+ 中文字的 Tokens\n")
        f.write(f"# 总计: {len(tokens)} 个\n")
        f.write(f"# 格式: Token ID | 中文字数 | 字节长度 | Token 内容\n")
        f.write("-" * 80 + "\n\n")

        for item in tokens:
            line = f"{item['id']:8d} | {item['chinese_count']:2d} | {item['byte_length']:3d} | {item['token']}\n"
            f.write(line)

    print(f"✓ 已输出至: {txt_filename}")

    # 输出为 CSV
    csv_filename = f'all_chinese_tokens_{min_chinese_chars}plus.csv'
    with open(csv_filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Token_ID', '中文字数', '总长度', '字节长度', 'Token内容', '备注'])

        for item in tokens:
            writer.writerow([
                item['id'],
                item['chinese_count'],
                item['total_length'],
                item['byte_length'],
                item['token'],
                ''  # 空白备注栏
            ])

    print(f"✓ 已输出 CSV: {csv_filename}")


def print_statistics(tokens, distribution):
    """打印统计信息"""
    print("\n" + "=" * 80)
    print("统计信息:")
    print("=" * 80)
    print(f"符合条件的 tokens 总数: {len(tokens):,}")

    print("\n中文字符数分布:")
    for count in sorted(distribution.keys()):
        print(f"  {count:2d} 个中文字: {distribution[count]:,} tokens")

    print(f"\n中文字数最多的前 20 个 tokens:")
    for i, token in enumerate(tokens[:20], 1):
        print(f"  {i:2d}. [ID:{token['id']:6d}] {token['chinese_count']:2d}字 | "
              f"{token['byte_length']:3d}字节 | {token['token']}")


def main():
    # 设置最小中文字符数
    MIN_CHINESE_CHARS = 2

    # 提取中文 tokens
    chinese_tokens, distribution = extract_chinese_tokens(MIN_CHINESE_CHARS)

    # 保存结果
    print(f"\n正在保存结果...")
    save_results(chinese_tokens, MIN_CHINESE_CHARS)

    # 打印统计信息
    print_statistics(chinese_tokens, distribution)

    print("\n" + "=" * 80)
    print(f"✓ 完成！共找到 {len(chinese_tokens):,} 个包含 {MIN_CHINESE_CHARS}+ 中文字的 tokens")
    print("=" * 80)


if __name__ == "__main__":
    main()
