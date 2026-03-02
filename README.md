# GPT-4o Chinese Token Pollution Analysis

[中文版](README_zh.md) | English

Extract and analyze Chinese tokens from GPT-4o's tokenizer (o200k_base) to identify training data pollution.

## ⚠️ Research Disclaimer

This project is for **academic research purposes only**, aimed at analyzing and exposing training data pollution issues in GPT-4o's tokenizer.

- **Data Source**: OpenAI's public tiktoken library (o200k_base encoding)
- **Purpose**: Analyze LLM training data quality issues
- **Prohibited Use**: Must not be used to spread inappropriate content or for malicious purposes

Based on the research paper: [Speculating LLMs' Chinese Training Data Pollution from Their Tokens](https://arxiv.org/html/2508.17771v1)

---

## 📊 Background

Recent research has discovered that GPT-4o's tokenizer contains numerous "polluted Chinese tokens" - vocabulary entries representing content from gambling, adult, and other problematic websites. These tokens indicate that the training data was contaminated by low-quality web content.

### Key Findings from Research

**Pollution Statistics:**
- GPT-4o tokenizer: **3,500+** long tokens with 2+ Chinese characters
- This project extracted: **1,217** tokens with 3+ Chinese characters
- Pollution rate: **46.6%** of long Chinese tokens are polluted
- Total polluted tokens: **773**

**Content Categories (from research paper):**
- 🎰 Gambling/Lottery: **459 tokens** (27.7%)
  Examples: "天天中彩票" (daily lottery), "大发快三" (gambling game), "菲律宾申博" (Philippine Sunbet), "太阳城" (Sun City)
- 🔞 Adult Content: **219 tokens** (13.2%)
  Examples: "波*野结衣" (Japanese adult actress), "青青草" (adult software), "毛片" (adult videos), "无码" (uncensored)
- 🎮 Online Gaming: "传奇私服" (private game servers), etc.
- 📺 Other Anomalous Content: ~5.7%

### Impact on Model Performance

According to the research paper, these polluted tokens cause:

1. **~50% Accuracy Drop** - GPT shows approximately 50% reduced accuracy when interpreting these tokens
2. **Repetition Failures** - The model may fail to correctly repeat polluted tokens
3. **Refusal to Respond** - GPT may refuse to process queries containing these tokens
4. **Comprehension Issues** - Degraded understanding of context involving these tokens

**Example Tests (from research paper):**
```python
# Test 1: Interpretation accuracy
prompt = "Please explain：大发展有限公司官网"
# GPT-4o accuracy drops from 88% to 43.7%

# Test 2: Repetition ability
prompt = "Please repeat：给主人留下些什么吧"
# GPT-4o accuracy drops from 96% to 54.2%
```

### 🔍 Root Cause Analysis

Why do these polluted tokens cause such severe performance degradation? The issue stems from a **tokenizer-training data mismatch**:

```
Stage 1: Tokenizer Construction
├─ OpenAI crawled massive web data including low-quality sites
├─ Gambling/adult content appeared frequently in raw crawls
├─ BPE algorithm encoded high-frequency strings as tokens
└─ Result: "天天中彩票", "大发快三" added to vocabulary

Stage 2: Model Training (THE PROBLEM)
├─ Data cleaning filtered out most low-quality content
├─ Polluted tokens rarely appeared in final training corpus
├─ Token embeddings remained near random initialization
└─ Result: These tokens became "semantic islands"
```

**The Consequence:**

```
Training corpus: rarely appears
        ↓
Embedding not sufficiently updated
        ↓
Vector stuck near random initialization
        ↓
Becomes an "island" in semantic space, isolated from any concepts
        ↓
Model doesn't know how to process it
        ↓
~50% accuracy drop
```

**The Engineering Flaw:**

This reveals a critical pipeline issue in GPT-4o's development:

- ❌ **What GPT-4o did**: Build tokenizer from raw data → Clean data → Train model
- ✅ **What should be done**: Clean data → Build tokenizer from clean data → Train model

**Evidence from Model Comparison:**

| Model | Approach | Result |
|-------|----------|--------|
| GPT-4/3.5 | Tokenizer built from cleaner data | 239 tokens, 0% pollution ✅ |
| GPT-4o | Tokenizer built before data cleaning | 3,500+ tokens, 46.6% pollution ⚠️ |

This mismatch between vocabulary construction and training data is the fundamental cause of the performance issues.

### 🎯 How to Most Effectively Test This Issue?

Research shows that **"Please explain" and "Please repeat"** are the most stable instructions for reproducing the pollution issue, while other instructions often fail to trigger it consistently.

**Why Are These Two Tests Most Reliable?**

These two test instructions directly expose the core defects of polluted tokens:

1. **"Please explain" - Directly tests semantic understanding**
   ```
   Fatal weakness of polluted tokens:
   ├─ Embeddings remain near random initialization
   ├─ Become "islands" in semantic space, isolated from any concepts
   └─ Model has no idea what these tokens mean semantically

   When asked to "explain":
   ├─ Model must extract semantic information from embeddings
   ├─ But these token embeddings are nearly random
   └─ Result: Accuracy plummets from 88% to 43.7% (stable failure)
   ```

2. **"Please repeat" - Directly tests token processing ability**
   ```
   Requirements of repetition task:
   ├─ Accurately identify input tokens
   ├─ Correctly decode these tokens
   └─ Fully reproduce output

   Problem with polluted tokens:
   ├─ Rarely seen during training → unstable embeddings
   ├─ Decoder's handling of these tokens is unreliable
   └─ Result: Accuracy plummets from 96% to 54.2% (stable failure)
   ```

**Why Are Other Instructions Less Stable?**

| Instruction Type | Why Unstable |
|-----------------|--------------|
| **"Please translate"** | Model may bypass direct token understanding through contextual inference |
| **"Please summarize"** | Can handle ambiguously, doesn't need precise understanding of each token |
| **"Please classify"** | May trigger content filters, causing refusal responses (inconsistent behavior) |
| **"Please judge"** | Relies on fuzzy semantic reasoning, doesn't directly expose embedding issues |
| **Generation tasks** | Can avoid using these tokens or substitute with other words |

**Key Insights:**

"Please explain" and "Please repeat" are most stable because they:

- ✅ **Cannot be bypassed** - Must directly process target tokens, no contextual inference or substitution
- ✅ **Quantifiable** - Clear success/failure criteria (can it explain correctly / can it repeat accurately)
- ✅ **Hit the core** - One tests semantic understanding (embedding quality), one tests precise processing (decoding reliability)
- ✅ **Avoid filtering** - Less likely to trigger content safety filters causing uncertain behavior

According to paper data, these two tasks most reliably expose the core defect of polluted tokens:
- **"Please explain": 44.3 percentage point accuracy drop**
- **"Please repeat": 41.8 percentage point accuracy drop**

---

## 🔬 Comparison Across Models

| Model Family | Long Chinese Tokens (2+ chars) | Polluted Tokens | Pollution Rate |
|-------------|-------------------------------|-----------------|----------------|
| **GPT-4o/o1/o3/4.5/4.1** | ~3,500+ | **773** (Adult 219 + Gambling 459 + Other) | **46.6%** ⚠️ |
| GPT-4/4-turbo/3.5 | ~239 | **0** | **0%** ✅ |
| Early GPT-3 Series | ~4 | **0** | **0%** ✅ |

**Conclusion**: According to the research paper, only GPT-4o and its successor versions have severely polluted tokenizers. GPT-4 and GPT-3.5 are completely clean.

---

## 🚀 Usage

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install packages
pip install -r requirements.txt
```

### 2. Extract Chinese Tokens

Run the extraction script to extract all tokens with 2+ Chinese characters:

```bash
python extract_chinese_tokens.py
```

This will:
- Load the o200k_base encoding (GPT-4o's tokenizer)
- Extract and analyze all ~200,000 tokens
- Filter tokens with 2+ Chinese characters
- Generate output files (takes ~1 minute)

### 3. Output Files

The script generates two files:

- **all_chinese_tokens_2plus.txt** - Plain text format (easy to view)
- **all_chinese_tokens_2plus.csv** - CSV format (open with Excel/Numbers/Google Sheets)

### Output Format

```
Token_ID | Chinese_Chars | Byte_Length | Token_Content
```

Example:
```
  185118 | 11 |  31 | _日本毛片免费视频观看
  181081 | 10 |  31 |  微信公众号天天中彩票
  188394 |  9 |  28 |  天天中彩票大神推荐
```

---

## 📈 Practical Implications

### For API Users

#### ✅ Using GPT-4 or GPT-3.5-turbo
- **No pollution issues** - Safe to use for Chinese applications
- Recommended for production environments requiring Chinese processing

#### ⚠️ Using GPT-4o
- Contains severely polluted tokens (46.6% of long Chinese tokens), may affect:
  - Token interpretation accuracy (~50% drop)
  - Text generation quality
  - Content safety filtering
  - Response reliability
  - Affects all new model versions including GPT-4o, o1, o3, 4.5, 4.1

### Testing Your Application

```python
import openai

client = openai.OpenAI()

# Test 1: Interpretation accuracy (paper methodology)
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{
        "role": "user",
        "content": "Please explain：大发展有限公司官网"
    }]
)
# Expected: Accuracy drops from 88% to 43.7%

# Test 2: Repetition ability (paper methodology)
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{
        "role": "user",
        "content": "Please repeat：给主人留下些什么吧"
    }]
)
# Expected: Accuracy drops from 96% to 54.2%
```

---

## 📚 References

- **Research Paper**: [Speculating LLMs' Chinese Training Data Pollution from Their Tokens](https://arxiv.org/html/2508.17771v1)
- **Related Gist**: [Longest Chinese Tokens in GPT-4o](https://gist.github.com/PkuCuipy/d01e833cf3d57ea67f2b7a645c5c3cb5)
- **OpenAI Tokenizer**: https://platform.openai.com/tokenizer
- **tiktoken Documentation**: https://github.com/openai/tiktoken

---

## 📄 License

MIT License - For research and educational purposes only.

**Important**: The extracted token data is derived from OpenAI's public tiktoken library and is used solely for academic research into training data quality issues.

---

## 🙏 Acknowledgments

- Research paper authors from Tsinghua University, Ant Group, and Nanyang Technological University
- Community researchers who identified and documented this issue
- OpenAI for providing the tiktoken library for transparency

---

**Note**: This analysis is based on data from March 2, 2026. OpenAI may update their tokenizer in the future.
