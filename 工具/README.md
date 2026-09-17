# 工具

这些卷子的 PDF 分两种，处理方式不同。

## 1. 文字版 PDF → 直接抽文本

```bash
python3 工具/pdf_text.py "题/2-2010年-2020年/2010年7月/【1】2010年07月N1 真题-版本2.pdf" > /tmp/q.txt
```

只用 Python 标准库（zlib + re），自己解析 PDF 对象、ToUnicode CMap，
**不需要 poppler / pdftotext / PyPDF2**。

## 2. 扫描版 PDF → 渲染成 PNG 再看

```bash
mkdir -p /tmp/pages
osascript -l JavaScript 工具/render_pdf.js "题/.../【2】...答案解析....pdf" /tmp/pages "1,2,3"
```

走 macOS 自带的 PDFKit（JXA），同样不需要装任何东西。
第三个参数是页码列表，逗号分隔。**输出目录必须先存在**，否则会静默失败。

## 怎么判断是哪一种

```bash
python3 -c "
import re,sys
d=open(sys.argv[1],'rb').read()
print('images',len(re.findall(rb'/Subtype\s*/Image',d)),
      'tounicode',len(re.findall(rb'ToUnicode',d)),
      'pages',len(re.findall(rb'/Type\s*/Page[^s]',d)))
" "题/.../某个.pdf"
```

`tounicode` 是 0 或个位数 → 基本是扫描件，走渲染。

## 已知情况

### 「版本1」「版本2」是什么关系

**同一场考试的两个排版，不是两套题。真题只需要做一份。**

已核对 2010年7月：两版的题干、选项、题号完全一致。

- **版本1 = 原卷扫描**，排版接近真实考卷 → **做题以这版为准**
- **版本2 = 重新录入排版**，个别地方有录入手误
  （例：2010-07 第19题干扰项1，版本1「不平」／版本2「不満」，正解不受影响）

### 两份解析是互补的，对答案时都要看

- 版本1（答案解析+听力原文+**译文**）：文字版，有阅读译文、听力原文和逐题「答え」，
  但**答案汇总表那几页是图形文字，抽不出来**
- 版本2（答案解析+听力原文）：扫描件，**第 1 页就是完整答案表**，第 2 页起是逐题解析

对答案的最快路径：**版本2 第 1 页拿答案表（渲染成图看），版本1 抽文本拿解析和听力原文。**
