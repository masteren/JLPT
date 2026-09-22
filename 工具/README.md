# 工具

`题/` 里的 PDF 分两种，处理方式不同。两条路径都只用 Windows 自带环境，无需第三方库。

## 1. 文字版 PDF → 抽文本

```bash
PYTHONIOENCODING=utf-8 python 工具/pdf_text.py "题/2012年7月/【2】2012年07月N1答案解析+听力原文+译文-版本1.pdf" > out.txt
```

只用 Python 标准库（zlib + re），自己解析 PDF 对象和 ToUnicode CMap。

> Windows 上必须带 `PYTHONIOENCODING=utf-8`，否则 stdout 走 GBK 会在日文字符上
> 报 `UnicodeEncodeError`。读回这个 txt 时同样要显式 `encoding='utf-8'`。

## 2. 扫描版 PDF → 渲染成 PNG

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File 工具/render_pdf.ps1 `
  -Pdf "题/2012年7月/【1】2012年07月N1 真题-版本1.pdf" -OutDir "<输出目录>" -Pages "1,2,3"
```

走 WinRT `Windows.Data.Pdf`。输出到 `<输出目录>/page-001.png`，目录不存在会自动创建。
`-Width` 默认 1700 px，日文小字和答案表都看得清。

## 怎么判断是哪一种

```bash
python -c "
import re,sys
d=open(sys.argv[1],'rb').read()
print('images',len(re.findall(rb'/Subtype\s*/Image',d)),'tounicode',len(re.findall(rb'ToUnicode',d)))
" "题/.../某个.pdf"
```

`tounicode` 是 0 或个位数 → 扫描件，走渲染。

## 「版本1」「版本2」是什么关系

**同一场考试的两个排版，不是两套题。做题只做版本1。**

- **版本1 ＝ 原卷扫描**，排版接近真实考卷 → 做题、对答案都以这版为准
- 版本2 ＝ 重新录入排版，个别地方有录入手误
  （例：2010-07 第19题干扰项1，版本1「不平」／版本2「不満」，正解不受影响）

**版本1 的解析（带译文那份）一份就够**：第 1 页是全卷参考答案表（渲染成图看），
后面是逐题解析、阅读译文和听力原文（抽文本看）。2012 年起的解析直接标「正解：X」。
