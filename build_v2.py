# -*- coding: utf-8 -*-
"""
Combined deck v2 — preserves ALL original text & images of the four source
PPTs, styled after Part 4.pptx (navy / teal / gold card design).
"""
import os, re
from copy import deepcopy
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from PIL import Image

# --------------------------------------------------------------- palette ----
NAVY  = RGBColor(0x1B, 0x2A, 0x4A)
TEAL  = RGBColor(0x00, 0x96, 0xC7)
CYAN  = RGBColor(0x48, 0xCA, 0xE4)
GOLD  = RGBColor(0xF4, 0xA2, 0x5F)
RED   = RGBColor(0xC0, 0x50, 0x50)
GREEN = RGBColor(0x2E, 0x7D, 0x5B)
BG    = RGBColor(0xF2, 0xF4, 0xF7)
DARK  = RGBColor(0x2D, 0x2D, 0x2D)
GRAY  = RGBColor(0x5A, 0x5A, 0x5A)
LIGHT = RGBColor(0xBB, 0xCC, 0xDD)
BORDER= RGBColor(0xD8, 0xDE, 0xE6)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

FONT = "Calibri"
EA   = "Microsoft YaHei"
MEDIA = r"e:\Tech_English\_media"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
TOTAL = 63
PAGE = 0

# --------------------------------------------------------------- helpers ----
def slide():
    return prs.slides.add_slide(BLANK)

def _noline(sh, color=None):
    if color is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = color; sh.line.width = Pt(0.75)
    sh.shadow.inherit = False

def rect(s, x, y, w, h, color, line=None, rounded=False):
    kind = MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE
    sh = s.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb = color
    _noline(sh, line)
    if rounded:
        try: sh.adjustments[0] = 0.06
        except Exception: pass
    return sh

def oval(s, x, y, d, color, num=None, fs=13):
    sh = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y),
                            Inches(d), Inches(d))
    sh.fill.solid(); sh.fill.fore_color.rgb = color
    _noline(sh)
    if num is not None:
        tf = sh.text_frame; tf.word_wrap = True
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = str(num)
        _st(r, fs, True, WHITE)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    return sh

def chevron(s, x, y, w, h, color):
    sh = s.shapes.add_shape(MSO_SHAPE.CHEVRON, Inches(x), Inches(y),
                            Inches(w), Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb = color
    _noline(sh)
    return sh

def _st(run, size, bold, color, italic=False):
    f = run.font
    f.size = Pt(size); f.bold = bold; f.italic = italic
    f.name = FONT; f.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        ea = rPr.makeelement(qn('a:ea'), {}); rPr.append(ea)
    ea.set('typeface', EA)

def text(s, x, y, w, h, paras, anchor=MSO_ANCHOR.TOP, wrap=True):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    for m in ('margin_left','margin_right','margin_top','margin_bottom'):
        setattr(tf, m, Pt(2))
    for i, sp in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = sp.get('align', PP_ALIGN.LEFT)
        p.space_after = Pt(sp.get('after', 2))
        p.space_before = Pt(sp.get('before', 0))
        p.line_spacing = sp.get('ls', 1.05)
        if 'runs' in sp:
            for (t, b, c, *rest) in sp['runs']:
                r = p.add_run(); r.text = t
                _st(r, sp.get('sz', 13), b, c, sp.get('it', False) or bool(rest))
        else:
            r = p.add_run(); r.text = sp['t']
            _st(r, sp.get('sz', 13), sp.get('b', False),
                 sp.get('color', DARK), sp.get('it', False))
    return tb

def P(t, sz=13, b=False, color=DARK, **kw):
    d = {'t': t, 'sz': sz, 'b': b, 'color': color}; d.update(kw); return d

def card(s, x, y, w, h, accent='top', ac=TEAL, fill=BG, line=None):
    rect(s, x, y, w, h, fill, line=line)
    if accent == 'top':
        rect(s, x, y, w, 0.07, ac)
    elif accent == 'left':
        rect(s, x, y, 0.12, h, ac)
    elif accent == 'tag':
        oval(s, x + 0.18, y + 0.16, 0.16, ac)
    return

def pic_fit(s, path, x, y, w, h, pad=0.1, border=True,
            cl=0, cr=0, ct=0, cb=0):
    """Place image contained in box (x,y,w,h), white card + optional border."""
    cardw, cardh = w, h
    if border:
        rect(s, x, y, w, h, WHITE, line=BORDER)
    iw, ih = Image.open(path).size
    vis_w, vis_h = iw * (1 - cl - cr), ih * (1 - ct - cb)
    ar = vis_w / vis_h
    iw_in = (w - 2 * pad)
    ih_in = iw_in / ar
    if ih_in > h - 2 * pad:
        ih_in = h - 2 * pad
        iw_in = ih_in * ar
    px = x + (w - iw_in) / 2
    py = y + (h - ih_in) / 2
    p = s.shapes.add_picture(path, Inches(px), Inches(py),
                             Inches(iw_in), Inches(ih_in))
    if cl or cr or ct or cb:
        p.crop_left = cl; p.crop_right = cr
        p.crop_top = ct; p.crop_bottom = cb
    return p

def title_bar(s, title, subtitle):
    rect(s, 0, 0, 13.333, 7.5, WHITE)
    rect(s, 0, 0, 13.333, 1.12, NAVY)
    rect(s, 0, 1.12, 13.333, 0.06, TEAL)
    text(s, 0.55, 0.15, 12.25, 0.62, [P(title, 25, True, WHITE)])
    if subtitle:
        text(s, 0.55, 0.76, 12.25, 0.3, [P(subtitle, 12.5, False, CYAN)])

def footer(s, source):
    text(s, 0.4, 7.05, 3.0, 0.3, [P(f"{PAGE} / {TOTAL}", 9, False, GRAY)])
    if source:
        text(s, 5.3, 7.05, 7.63, 0.3,
             [P(source, 9, False, GRAY, align=PP_ALIGN.RIGHT)])

def content(title, subtitle, source):
    global PAGE
    PAGE += 1
    s = slide(); title_bar(s, title, subtitle); footer(s, source)
    return s

def divider(num, en, cn, topics):
    global PAGE
    PAGE += 1
    s = slide()
    rect(s, 0, 0, 13.333, 7.5, NAVY)
    rect(s, 0, 2.55, 13.333, 0.06, TEAL)
    rect(s, 0, 4.45, 13.333, 0.03, CYAN)
    text(s, 0.8, 1.42, 11.73, 0.5,
         [P(f"PART 0{num}", 20, True, CYAN, align=PP_ALIGN.CENTER)])
    text(s, 0.8, 2.72, 11.73, 0.9,
         [P(en, 36, True, WHITE, align=PP_ALIGN.CENTER)])
    text(s, 0.8, 3.6, 11.73, 0.5,
         [P(cn, 21, True, GOLD, align=PP_ALIGN.CENTER)])
    text(s, 1.3, 4.65, 10.73, 1.6,
         [P(topics, 14, False, LIGHT, align=PP_ALIGN.CENTER, ls=1.45)])
    text(s, 0.4, 7.05, 3.0, 0.3, [P(f"{PAGE} / {TOTAL}", 9, False, GRAY)])
    return s

def chip(s, x, y, w, h, head, body, hc=NAVY, hs=12.5, bs=11,
         accent='top', fill=BG):
    card(s, x, y, w, h, accent=accent, ac=hc, fill=fill)
    paras = [P(head, hs, True, hc)]
    if body:
        if isinstance(body, str):
            paras.append(P(body, bs, False, DARK, before=2, ls=1.12))
        else:
            paras += body
    text(s, x + 0.2, y + 0.13, w - 0.38, h - 0.25, paras)

def quote_card(s, x, y, w, h, paras, src=None, ac=TEAL):
    card(s, x, y, w, h, accent='left', ac=ac, fill=BG)
    qparas = []
    for t in paras:
        qparas.append(P(t, 10.5, False, RGBColor(0x40, 0x40, 0x40),
                        it=True, ls=1.14, after=3))
    if src:
        qparas.append(P(src, 9.5, True, TEAL, before=2, align=PP_ALIGN.RIGHT))
    text(s, x + 0.28, y + 0.14, w - 0.5, h - 0.26, qparas)

def fcap(s, x, y, w, txt):
    """Italic grey figure caption (auto height, up to ~3 lines)."""
    text(s, x, y, w, 0.85, [P(txt, 9.3, False, GRAY, it=True,
                              align=PP_ALIGN.CENTER, ls=1.08)])

def fig_note(s, x, y, w, h, head, body, ac=TEAL):
    """Small explanatory card used on literature-figure pages."""
    card(s, x, y, w, h, accent='left', ac=ac, fill=BG)
    paras = [P(head, 11.5, True, ac)]
    if isinstance(body, str):
        paras.append(P(body, 9.8, False, DARK, before=2, ls=1.12))
    else:
        paras += body
    text(s, x + 0.22, y + 0.12, w - 0.4, h - 0.22, paras)

SRC1 = "Garini et al., 2006 · Prasad et al., 2024"
SRC2 = "[1] Mukhtar et al., 2025 · [2] Lu & Fei, 2014"
SRC3 = "Roussel et al., 2017 · Gautam et al., 2015 · Yamamoto et al., 2022"

# ======================================================== 1. TITLE ========
s = slide(); PAGE += 1
rect(s, 0, 0, 13.333, 7.5, NAVY)
rect(s, 0, 2.62, 13.333, 0.08, TEAL)
rect(s, 0, 4.62, 13.333, 0.04, CYAN)
text(s, 0.8, 1.15, 11.73, 1.0,
     [P("Spectroscopy and Spectral Imaging", 38, True, WHITE,
        align=PP_ALIGN.CENTER)])
text(s, 0.8, 2.0, 11.73, 0.55,
     [P("光谱与光谱成像", 26, True, GOLD, align=PP_ALIGN.CENTER)])
text(s, 0.8, 2.85, 11.73, 0.5,
     [P("From Fundamental Spectroscopy to Spectral Imaging Applications",
        17, False, CYAN, align=PP_ALIGN.CENTER)])
text(s, 0.8, 3.72, 11.73, 0.8,
     [P("Fundamentals of Spectroscopy  •  Principles of Spectral Imaging",
        14, False, LIGHT, align=PP_ALIGN.CENTER, after=4),
      P("Data Processing & Analysis  •  Applications & Future Trends",
        14, False, LIGHT, align=PP_ALIGN.CENTER)])
text(s, 0.8, 5.25, 11.73, 0.5,
     [P("Technical English Group Presentation", 18, False, WHITE,
        align=PP_ALIGN.CENTER)])
text(s, 0.8, 5.85, 11.73, 0.4,
     [P("Based on research papers (2003–2025)", 13, False, CYAN,
        align=PP_ALIGN.CENTER)])

# ======================================================== 2. CONTENTS =====
s = slide(); PAGE += 1
title_bar(s, "Contents", "Presentation Structure · 目录")
toc = [
    ("01", "Fundamentals of Spectroscopy", "光谱学基础",
     "Electromagnetic waves · Spectra · Atomic & molecular energy levels"),
    ("02", "Principles of Spectral Imaging", "光谱成像原理",
     "Data cube · Whiskbroom / Pushbroom / Staring · MSI vs. HSI"),
    ("03", "Data Processing & Analysis", "光谱数据处理与分析",
     "Calibration · PCA / MNF · Spectral classification & validation"),
    ("04", "Applications & Future Trends", "应用案例与未来趋势",
     "Remote sensing · Agriculture · Biomedicine · Miniaturization & AI"),
]
for i, (num, en, cn, sub) in enumerate(toc):
    x = 0.6 + (i % 2) * 6.27
    y = 1.7 + (i // 2) * 2.5
    rect(s, x, y, 6.0, 2.2, BG); rect(s, x, y, 0.13, 2.2, TEAL)
    oval(s, x + 0.35, y + 0.35, 0.78, TEAL, num)
    text(s, x + 1.35, y + 0.3, 4.5, 0.7, [P(en, 17, True, NAVY, ls=1.0)])
    text(s, x + 1.35, y + 0.92, 4.5, 0.35, [P(cn, 12.5, True, GOLD)])
    text(s, x + 1.35, y + 1.3, 4.45, 0.7, [P(sub, 11, False, GRAY, ls=1.1)])
footer(s, None)

# ########################################################## PART 1 #########
divider(1, "Fundamentals of Spectroscopy", "光谱学基础",
        "Light as electromagnetic waves · Spectroscopy\n"
        "Atomic & molecular energy levels · Historical development\n"
        "Key parameters · Beer–Lambert law · Eight technique families")

# --- 1.1 Light as electromagnetic waves -----------------------------------
s = content("1 · Light as Electromagnetic Waves",
            "Part 1 · Fundamentals of Spectroscopy", SRC1)
EN = ("Wave can be defined as any disturbance made in the medium that "
      "propagates through space. Most of the waves require some of the "
      "supporting media for propagation. The time dependence of displacement "
      "at any single point in the space often oscillates about some "
      "equilibrium position. For example, sound waves travel through the "
      "medium of air, and disturbance is the small collective displacement "
      "of air molecules. Therefore, it has properties of waves such as ocean "
      "waves, and light waves have crests and troughs. The distance between "
      "two successive crests or troughs is known as wavelength. Frequency "
      "can be defined as the number of waves passing from a point in one "
      "second. The velocity of light is the product of the wavelength of "
      "light and frequency of light. The different colors of light have "
      "different frequencies and wavelengths.")
CN = ("波可以定义为在空间传播的介质中产生的任何扰动。大多数波需要一些支持介质才能传播。"
      "空间中任何单点位移的时间依赖性常常围绕某个平衡位置振荡。例如，声波通过空气介质传播，"
      "扰动是空气分子的微小集体位移。因此，它具有海浪等波的性质，光波也有波峰和波谷。"
      "两个连续波峰或波谷之间的距离称为波长。频率可以定义为一秒钟内从一点经过的波数。"
      "光速是光的波长和光的频率的乘积。不同颜色的光有不同的频率和波长。"
      "光可以直线穿过某些物体，但不是所有物体。")
chip(s, 0.5, 1.45, 6.13, 3.5, "English", EN, hc=NAVY, hs=14, bs=10.5)
chip(s, 6.85, 1.45, 5.98, 3.5, "中文", CN, hc=GOLD, hs=14, bs=10.5)
for i, (h, b, c) in enumerate([
    ("Crest & Trough", "波峰与波谷：振荡的最高点和最低点", NAVY),
    ("Wavelength  λ", "波长：相邻波峰/波谷间距，nm、µm", TEAL),
    ("Frequency  ν", "频率：每秒经过一点的波数，单位 Hz", GOLD),
    ("c = λ · ν", "光速 = 波长 × 频率", RED),
]):
    x = 0.5 + i * 3.11
    rect(s, x, 5.2, 2.94, 1.6, BG); rect(s, x, 5.2, 2.94, 0.07, c)
    text(s, x + 0.15, 5.4, 2.64, 0.5, [P(h, 14, True, c, align=PP_ALIGN.CENTER)])
    text(s, x + 0.15, 5.92, 2.64, 0.8,
         [P(b, 10.5, False, GRAY, align=PP_ALIGN.CENTER, ls=1.12)])

# --- 1.2 Spectroscopy -------------------------------------------------------
s = content("2 · Spectroscopy", "Part 1 · Fundamentals of Spectroscopy", SRC1)
EN2 = ("Spectroscopy is a term that is used to describe different phenomena, "
       "and we limit our discussion to optical spectroscopy, mainly in the "
       "visible light range. A spectrum is a collection of light intensities "
       "at different wavelengths. Spectroscopy, the science of acquiring and "
       "explaining the spectral characteristics of matter, is a broad, well "
       "established and old science.")
CN2 = ("光谱学是一个用于描述不同现象的术语，我们将讨论限制在光学光谱学上，"
       "主要是在可见光范围内。光谱是不同波长的光强度的集合。"
       "光谱学是一门获取和解释物质光谱特征的科学，是一门广泛、完善的古老科学。")
chip(s, 0.5, 1.45, 7.4, 2.75, "English", EN2, hc=NAVY, hs=14, bs=11.5)
chip(s, 8.1, 1.45, 4.73, 2.75, "中文", CN2, hc=GOLD, hs=14, bs=10.5)
text(s, 0.5, 4.42, 12.3, 0.35,
     [P("Historical chain  —  Newton (1666) → Balmer (1885) → Bohr (1913) → Schrödinger (1926)",
        13, True, TEAL)])
chain = [
    ("1666", "Newton", "dispersion of white light into its constituent colours"),
    ("1900", "Spectrograph", "a system for measuring a spectrum, widely used"),
    ("1885", "Balmer", "explained the spectrum of hydrogen"),
    ("1913", "Bohr", "the Bohr model of the atom"),
    ("1926", "Schrödinger", "development of quantum mechanics"),
]
for i, (yr, name, desc) in enumerate(chain):
    x = 0.5 + i * 2.51
    c = [NAVY, TEAL, GOLD, TEAL, NAVY][i]
    chevron(s, x, 4.9, 2.42, 1.85, c)
    text(s, x + 0.22, 5.05, 2.0, 0.4, [P(yr, 17, True, WHITE)])
    text(s, x + 0.22, 5.5, 2.0, 0.35, [P(name, 13, True, WHITE)])
    text(s, x + 0.22, 5.88, 1.95, 0.85,
         [P(desc, 9, False, WHITE if i % 2 == 0 else WHITE, ls=1.05)])

# --- 1.3 Basic principle + FIG.1 -------------------------------------------
s = content("3 · The Basic Principle of Spectroscopy",
            "Part 1 · Fundamentals of Spectroscopy", SRC1)
EN3 = ("The structure of atoms and molecules is directly related to "
       "spectroscopy. The spectrum is a direct measurement of the energy "
       "levels of the detected structure (Fig. 1). Molecules (and atoms) "
       "have a specific energy-band structure. In an absorption process "
       "(which occurs in both brightfield and fluorescence microscopy), an "
       "electron is excited from the ground state to an excited energy band "
       "(1 in Fig. 1). In fluorescence, the electron rapidly decays to a "
       "meta-stable energy level (2 in Fig. 1). Then, light is emitted when "
       "the electron decays back to the ground state (3 in Fig. 1). The "
       "energy levels are intrinsic properties of the molecule, and the "
       "spectrum, therefore, provides a precise fingerprint of the molecule.")
CN3 = ("原子和分子的结构与光谱学直接相关。光谱是对所检测结构能级的直接测量（图 1）。"
       "分子（和原子）具有特定的能带结构。在吸收过程（明场显微镜和荧光显微镜中都会发生）中，"
       "电子从基态激发到激发能带（图 1 中的 1）。在荧光中，电子迅速衰减到亚稳态能级"
       "（图 1 中的 2）。然后，当电子衰变回到基态时就会发射光（图 1 中的 3）。"
       "能级是分子的固有属性，因此光谱提供了分子的精确指纹。")
chip(s, 0.5, 1.45, 7.25, 3.15, "English", EN3, hc=NAVY, hs=14, bs=10.5)
chip(s, 0.5, 4.75, 7.25, 2.1, "中文", CN3, hc=GOLD, hs=13, bs=10)
# right figure card
rect(s, 7.95, 1.45, 4.88, 5.35, WHITE, line=BORDER)
pic_fit(s, os.path.join(MEDIA, "p1_s4_3.png"), 8.25, 1.6, 4.28, 3.0,
        border=False, pad=0.02)
steps = [("1", "Absorption — the electron is excited from the ground state to the excited energy band by absorbing a photon."),
         ("2", "The electron decays rapidly to a meta-stable energy level."),
         ("3", "The electron falls back to the ground state, emitting a photon of lower energy (fluorescence).")]
yy = 4.55
for n, t in steps:
    oval(s, 8.2, yy + 0.03, 0.32, TEAL, n, fs=11)
    text(s, 8.65, yy, 3.95, 0.7, [P(t, 9.8, False, DARK, ls=1.05)])
    yy += 0.72
text(s, 8.2, 6.52, 4.4, 0.25,
     [P("FIG. 1. Energy-level diagram of a fluorescent molecule (Garini et al., 2006)",
        8.5, False, GRAY)])

# --- 1.4 Main parameter -----------------------------------------------------
s = content("4 · Main Parameters of a Spectrum",
            "Part 1 · Fundamentals of Spectroscopy", SRC1)
chip(s, 0.5, 1.45, 6.65, 5.35, "English", [
    P("Some of the important characteristics of a spectrum include:", 12, True, NAVY, after=6),
    P("1.  The spectral resolution determines the closest wavelengths that can be distinguished.",
      11, after=6, ls=1.15),
    P("2.  The spectral range in which spectra can be measured.", 11, after=6, ls=1.15),
    P("3.  The lowest detectable signal and dynamic range, which defines the smallest measurable "
      "signal and the number of distinguishable levels in a given measurement. These parameters "
      "also depend on the shape of the measured spectrum. A sharp laser line has a better "
      "detectable signal because the energy is concentrated at a single wavelength when compared "
      "to a broad spectrum with equal energy which is distributed over a large spectral range.",
      11, ls=1.15)], hc=NAVY, hs=14)
chip(s, 7.35, 1.45, 5.48, 3.0, "中文", [
    P("光谱的一些重要特征包括：", 11, True, GOLD, after=4),
    P("1. 光谱分辨率决定了可以区分的最接近的波长。", 10.5, after=3, ls=1.15),
    P("2. 可测量光谱的光谱范围。", 10.5, after=3, ls=1.15),
    P("3. 最低可检测信号和动态范围，定义了给定测量中的最小可测量信号和可区分级别的数量。"
      "这些参数还取决于测量光谱的形状——尖锐的激光线能量集中在单个波长处，"
      "比等能量宽光谱具有更好的可检测信号。", 10.5, ls=1.15)], hc=GOLD, hs=13)
for i, (h, b, c) in enumerate([
    ("Spectral Resolution", "closest distinguishable wavelengths", TEAL),
    ("Spectral Range", "wavelength interval that can be measured", NAVY),
    ("Detectable Signal & Dynamic Range", "smallest signal · number of distinguishable levels", GOLD),
]):
    y = 4.65 + i * 0.75
    rect(s, 7.35, y, 5.48, 0.65, BG); rect(s, 7.35, y, 0.1, 0.65, c)
    text(s, 7.55, y + 0.06, 5.2, 0.3, [P(h, 11.5, True, c)])
    text(s, 7.55, y + 0.34, 5.2, 0.3, [P(b, 9.5, False, GRAY)])

# --- 1.5 History 17-19 ------------------------------------------------------
s = content("5 · Historical Developments (17th–19th Century)",
            "Part 1 · Fundamentals of Spectroscopy", SRC1)
chip(s, 0.5, 1.45, 12.33, 1.95,
     "Prism spectroscopy  (17–18th century)",
     "The earliest observations of spectroscopic phenomena can be traced back to experiments "
     "conducted by Isaac Newton in the late 17th century. He demonstrated that white light could "
     "be separated into its component colors using a prism, revealing the spectrum of visible light.",
     hc=NAVY, hs=14, bs=11.5)
# two figures band
pic_fit(s, os.path.join(MEDIA, "p1_s6_5.png"), 0.5, 5.3, 4.25, 1.55)
pic_fit(s, os.path.join(MEDIA, "p1_s6_8.png"), 5.0, 5.42, 7.83, 1.4)
# spectral analysis card overlays middle band
rect(s, 0.5, 3.62, 12.33, 1.5, BG); rect(s, 0.5, 3.62, 0.12, 1.5, GOLD)
text(s, 0.82, 3.72, 11.9, 1.35, [
    P("Spectral analysis  (19th century)", 14, True, GOLD),
    P("In the early 19th century, Joseph von Fraunhofer systematically studied the absorption "
      "lines in the solar spectrum; he discovered hundreds of dark lines — Fraunhofer lines — "
      "caused by absorption of specific wavelengths by elements in the Sun's atmosphere. Gustav "
      "Kirchhoff and Robert Bunsen further advanced the field in the mid-19th century, developing "
      "flame emission spectroscopy and laying the foundation for quantitative analysis of chemical "
      "elements based on their spectral signatures.", 10.5, before=2, ls=1.12)])

# --- 1.6 History 20-21 ------------------------------------------------------
s = content("5 · Historical Developments (20th–21st Century)",
            "Part 1 · Fundamentals of Spectroscopy", SRC1)
chip(s, 0.5, 1.45, 6.05, 4.1,
     "Quantum mechanics and atomic spectra  (Early 20th century)",
     "The development of quantum mechanics in the early 20th century revolutionized our "
     "understanding of atomic structure and spectral lines. Scientists such as Niels Bohr, Max "
     "Planck, and Werner Heisenberg formulated theories to explain the discrete energy levels of "
     "atoms and the quantized nature of electromagnetic radiation. The Bohr model of the atom, "
     "proposed by Niels Bohr in 1913, provided a theoretical framework for understanding atomic "
     "spectra and the transitions of electrons between energy levels.",
     hc=NAVY, hs=13.5, bs=10.5)
chip(s, 6.78, 1.45, 6.05, 4.1,
     "Modern spectroscopic techniques  (20th–21st century)",
     "Throughout the 20th and 21st centuries, spectroscopic techniques have continued to evolve "
     "with technological advancements and instrumentation. Developing techniques such as infrared "
     "(IR) spectroscopy, Raman spectroscopy, nuclear magnetic resonance spectroscopy, and X-ray "
     "spectroscopy has expanded the range of applications in fields such as chemistry, physics, "
     "biology, materials science, and medicine. Innovations in detectors, lasers, optics, and "
     "computational methods have enabled higher sensitivity, resolution, and versatility.",
     hc=GOLD, hs=13.5, bs=10.5)
chip(s, 0.5, 5.75, 6.05, 1.05, "Key People",
     "Niels Bohr · Max Planck · Werner Heisenberg  —  discrete energy levels & quantized radiation",
     hc=NAVY, hs=12.5, bs=10.5)
chip(s, 6.78, 5.75, 6.05, 1.05, "Key Techniques",
     "IR · Raman · NMR · X-ray spectroscopy  —  higher sensitivity, resolution and versatility",
     hc=GOLD, hs=12.5, bs=10.5)

# --- 1.7 Instrumentation ----------------------------------------------------
s = content("6 · Classification and Types of Major Spectroscopic Techniques",
            "Part 1 · Absorption & Emission Instrumentation", SRC1)
chip(s, 0.5, 1.45, 6.05, 2.0,
     "a)  Absorption instrumentation",
     "The radiation from a white source is directed by some guiding device onto the sample, from "
     "which it passes through an analyzer, which selects the frequency that reaches the detector at "
     "any given time. The signal from the analyzer passes to a recorder synchronized with the "
     "analyzer to produce a trace of absorbance as the frequency varies. A modulator is often "
     "placed between the sample and the analyzer to manipulate the properties of light and extract "
     "specific information from a sample.",
     hc=NAVY, hs=13, bs=9.8)
pic_fit(s, os.path.join(MEDIA, "p1_s8_5.png"), 0.5, 3.62, 6.05, 3.18)
chip(s, 6.78, 1.45, 6.05, 2.0,
     "b)  Emission instrument",
     "Emission instrumentation refers to the devices and systems used to measure the emission "
     "spectra of atoms, molecules, or ions. Many instruments are developed based on the emission "
     "mechanism, such as atomic emission spectroscopy, optical emission spectroscopy, inductively "
     "coupled plasma emission spectroscopy, laser-induced breakdown spectroscopy, and fluorescence "
     "spectroscopy.",
     hc=GOLD, hs=13, bs=9.8)
pic_fit(s, os.path.join(MEDIA, "p1_s8_8.png"), 6.78, 3.62, 6.05, 3.18)

# --- 1.7F Literature figure: UV-Vis instrument layout -----------------------
s = content("Figures from the Literature · Inside a UV-Vis Spectrometer",
            "Part 1 · Absorption Spectroscopy Instrumentation",
            "Prasad et al., 2024")
pic_fit(s, os.path.join(MEDIA, "fig_uvvis_schematic.png"),
        1.1, 1.5, 11.13, 4.45)
fcap(s, 1.1, 6.0, 11.13,
     "Fig. 1. A pictorial representation of UV-Vis spectroscopy: the measured "
     "sample absorbs selected wavelengths from the selector, and the detector "
     "converts transmitted light into an electric signal. (Prasad et al., 2024)")
rect(s, 1.1, 6.62, 11.13, 0.36, BG)
text(s, 1.3, 6.66, 10.7, 0.3,
     [P("Common chain of every absorption instrument:  light source  →  "
        "wavelength selector  →  sample  →  detector  →  readout / computer",
        10.5, True, NAVY, align=PP_ALIGN.CENTER)],
     anchor=MSO_ANCHOR.MIDDLE)

# --- 1.8 Beer-Lambert & emission --------------------------------------------
s = content("7 · Measurement Principles of Absorption and Emission Spectra",
            "Part 1 · Fundamentals of Spectroscopy", SRC1)
rect(s, 0.5, 1.45, 6.9, 2.95, BG); rect(s, 0.5, 1.45, 0.12, 2.95, NAVY)
text(s, 0.82, 1.6, 6.5, 2.75, [
    P("Absorption spectra — Beer–Lambert's law", 13.5, True, NAVY),
    P("In optical spectroscopy, the absorption of light by a sample is typically described by "
      "Beer-Lambert's law: the absorbance of light is proportional to the concentration of the "
      "absorbing species, the path length of the light through the sample, and the molar "
      "absorptivity of the species at a given wavelength. By measuring absorbance at different "
      "wavelengths, one obtains an absorption spectrum revealing the characteristic absorption "
      "bands or peaks associated with specific molecular or electronic transitions.",
      10.3, before=3, ls=1.12),
    P("A = ε · c · l", 16, True, TEAL, before=5, align=PP_ALIGN.CENTER)])
rect(s, 0.5, 4.6, 6.9, 2.2, BG); rect(s, 0.5, 4.6, 0.12, 2.2, GOLD)
text(s, 0.82, 4.74, 6.5, 2.0, [
    P("Emission spectra — fluorescence & phosphorescence", 13.5, True, GOLD),
    P("In emission spectroscopy, the intensity of light emitted is measured. This light, which may "
      "occur instantaneously or with a delay, contains information about the energy levels, "
      "electronic states, and chemical environment of the emitting species. The two main types are "
      "fluorescence and phosphorescence spectroscopy, distinguished by their respective mechanisms "
      "of excited-state relaxation and lifetime.", 10.3, before=3, ls=1.12)])
pic_fit(s, os.path.join(MEDIA, "p1_s9_1026.png"), 7.62, 1.45, 5.21, 3.75)
text(s, 7.62, 5.25, 5.21, 0.25,
     [P("Absorbance and fluorescence vs. wavelength", 9.5, False, GRAY,
        align=PP_ALIGN.CENTER)])
rect(s, 7.62, 5.6, 5.21, 1.2, BG); rect(s, 7.62, 5.6, 0.12, 1.2, TEAL)
text(s, 7.9, 5.72, 4.85, 1.0, [
    P("Emission may be instantaneous or delayed", 11.5, True, TEAL),
    P("fluorescence (fast relaxation) vs. phosphorescence (longer lifetime)",
      10.5, before=2, ls=1.1)])

# --- 1.9 Eight technique families -------------------------------------------
s = content("8 · Major Spectroscopic Techniques",
            "Part 1 · Eight Families of Modern Spectroscopic Methods", SRC1)
techs = [
    ("1", "光学光谱  Optical Spectroscopy",
     "UV-Vis 紫外-可见 ｜ UPS 紫外光电子能谱 ｜ 荧光光谱 Fluorescence", NAVY),
    ("2", "振动光谱  Vibrational Spectroscopy",
     "FT-IR 傅里叶变换红外 ｜ Raman 拉曼 ｜ SERS 表面增强拉曼", TEAL),
    ("3", "电子光谱  Electron Spectroscopy",
     "XPS X射线光电子能谱 ｜ AES 俄歇电子能谱 ｜ EELS 电子能量损失谱", GOLD),
    ("4", "磁共振光谱  Magnetic Resonance",
     "NMR 核磁共振 ｜ FMR 铁磁共振", NAVY),
    ("5", "质谱  Mass Spectrometry",
     "TOF-MS 飞行时间质谱 ｜ MALDI-MS 基质辅助激光解吸电离质谱", TEAL),
    ("6", "热光谱  Thermal Analysis",
     "TGA 热重分析", GOLD),
    ("7", "光发射光谱  Optical Emission",
     "OES 光发射光谱 ｜ ICP-OES 电感耦合等离子体光发射光谱", NAVY),
    ("8", "其它  Miscellaneous",
     "XAS X 射线吸收光谱（含 XANES / EXAFS）｜ AAS 原子吸收光谱", TEAL),
]
for i, (n, head, body, c) in enumerate(techs):
    x = 0.5 + (i % 2) * 6.28
    y = 1.45 + (i // 2) * 1.33
    rect(s, x, y, 6.05, 1.2, BG); rect(s, x, y, 0.1, 1.2, c)
    oval(s, x + 0.18, y + 0.33, 0.52, c, n, fs=15)
    text(s, x + 0.88, y + 0.15, 5.0, 0.4, [P(head, 12.5, True, NAVY)])
    text(s, x + 0.88, y + 0.55, 5.05, 0.6, [P(body, 10.3, False, DARK, ls=1.08)])

# --- 1.9F Literature figure: spectral unmixing of tissue --------------------
s = content("Figures from the Literature · Spectral Unmixing of Tissue",
            "Part 1 · Spectral Imaging in the Life Sciences",
            "Garini et al., 2006")
pic_fit(s, os.path.join(MEDIA, "fig_garini_unmixing.png"),
        0.5, 1.5, 7.55, 5.3)
fcap(s, 0.5, 6.42, 7.55,
     "Fig. 9. Spectral unmixing applied to a pathological prostate tissue "
     "section stained with hematoxylin and eosin. (Garini et al., 2006)")
card(s, 8.3, 1.5, 4.53, 5.3, accent='top', ac=NAVY)
text(s, 8.55, 1.7, 4.05, 5.0, [
    P("How to read this figure", 12.5, True, NAVY),
    P("(A)  Colour image created from the spectral image — similar to the "
      "visual image seen through the microscope.", 9.8, before=4, ls=1.13),
    P("(B)  Optical-density spectra of two reference stains: eosin and "
      "hematoxylin, measured on reference slides.", 9.8, before=4, ls=1.13),
    P("(C, D)  Unmixing results: how the tissue would look if stained with "
      "only hematoxylin (C) or only eosin (D).", 9.8, before=4, ls=1.13),
    P("Linear unmixing: the measured spectrum at each pixel is decomposed "
      "into a weighted sum of pure reference spectra.",
      10, True, TEAL, before=8, ls=1.15)])

# ########################################################## PART 2 #########
divider(2, "Principles of Spectral Imaging", "光谱成像原理",
        "From single-point spectroscopy to the spectral data cube I(x, y, λ)\n"
        "Whiskbroom · Pushbroom · Staring acquisition modes\n"
        "Spatial–spectral resolution trade-off · Multispectral vs. hyperspectral")

# --- 2.0 Overview -----------------------------------------------------------
s = content("Overview · Three Topics of Spectral Imaging",
            "Part 2 · Principles of Spectral Imaging", SRC2)
ovw = [
    ("单点光谱扩展到光谱成像", "From Single-Point Spectroscopy to Spectral Imaging", NAVY),
    ("光谱成像的主要模式", "Three Primary Spectral-Imaging Acquisition Modes", TEAL),
    ("光谱分辨率与空间分辨率及其权衡",
     "Trade-off Between Spatial Resolution and Spectral Resolution", GOLD),
    ("多光谱与高光谱", "Multispectral and Hyperspectral", RED),
]
for i, (cn, en, c) in enumerate(ovw):
    y = 1.6 + i * 1.32
    rect(s, 1.0, y, 11.33, 1.12, BG); rect(s, 1.0, y, 0.12, 1.12, c)
    oval(s, 1.35, y + 0.24, 0.62, c, str(i + 1), fs=18)
    text(s, 2.25, y + 0.17, 9.8, 0.45, [P(cn, 18, True, NAVY)])
    text(s, 2.25, y + 0.62, 9.8, 0.4, [P(en, 12.5, False, GRAY, it=True)])

# --- 2.1 Single point -> data cube + FIGURE 1 ------------------------------
s = content("From Single-Point Spectroscopy to Spectral Imaging",
            "Part 2 · Principles of Spectral Imaging", SRC2)
bullets = [
    ("Conventional single-point spectroscopy only obtains spectral information at one fixed "
     "spatial location: it answers “what” material the target is."),
    ("Traditional 2-D imaging only records spatial information: it answers “where” the object is "
     "located."),
    ("Spectral imaging combines spectroscopy and imaging, generating a 3-D spectral data cube "
     "I(x,y,λ). It answers: where is what."),
    ("The data cube contains two spatial dimensions (x,y) and one spectral dimension (λ)."),
]
rect(s, 0.5, 1.45, 7.2, 5.35, BG); rect(s, 0.5, 1.45, 0.12, 5.35, NAVY)
yy = 1.72
for i, b in enumerate(bullets):
    oval(s, 0.8, yy + 0.02, 0.34, [NAVY, TEAL, GOLD, RED][i], str(i + 1), fs=11)
    text(s, 1.3, yy, 6.2, 1.2, [P(b, 12.5 if i < 2 else 13, ls=1.18)])
    yy += 1.25
rect(s, 7.9, 1.45, 4.93, 5.35, WHITE, line=BORDER)
pic_fit(s, os.path.join(MEDIA, "p2_s3_5.png"), 8.1, 1.7, 4.53, 3.55,
        border=False)
text(s, 8.1, 5.35, 4.53, 0.6,
     [P("FIGURE 1. 3-D data cube [1]", 11, True, NAVY,
        align=PP_ALIGN.CENTER, ls=1.1),
      P("two spatial dimensions (x, y) + one spectral dimension (λ)",
        9.5, False, GRAY, align=PP_ALIGN.CENTER)])
text(s, 8.1, 6.25, 4.53, 0.4,
     [P("where is what  —  WHAT + WHERE together", 10.5, True, TEAL,
        align=PP_ALIGN.CENTER)])

# --- 2.1F Literature figure: hyperspectral data cube ------------------------
s = content("Figures from the Literature · Anatomy of a Hyperspectral Cube",
            "Part 2 · Principles of Spectral Imaging",
            "Shaw & Burke, 2003")
pic_fit(s, os.path.join(MEDIA, "fig_hsi_cube.png"),
        0.5, 1.45, 5.7, 5.4)
fcap(s, 0.5, 6.55, 5.7,
     "FIGURE 4. Concept of the hyperspectral data cube: spatial scanning "
     "builds a stack of co-registered wavelength bands. (Shaw & Burke, 2003)")
card(s, 6.4, 1.45, 6.43, 5.4, accent='top', ac=TEAL)
text(s, 6.65, 1.62, 5.95, 5.15, [
    P("How to read the cube", 12.5, True, TEAL),
    P("(a)  A push-broom platform collects one scan line at a time as the "
      "platform moves.", 9.8, before=4, ls=1.13),
    P("(b)  Each line carries all wavelengths; successive lines are stacked "
      "into the 3-D cube I(x, y, λ).", 9.8, before=4, ls=1.13),
    P("(c)  Cutting across wavelengths gives a stack of monochrome band "
      "images — one image per λ.", 9.8, before=4, ls=1.13),
    P("(d)  Cutting across space at one pixel gives a continuous spectrum; "
      "tree, fabric, paint and grass each show a distinct, diagnostic "
      "spectral curve.", 9.8, before=4, ls=1.13),
    P("Material identification = matching measured curves against known "
      "spectral signatures.", 10, True, NAVY, before=8, ls=1.15)])

# --- 2.2 Whiskbroom & Pushbroom + FIGURE 2 ---------------------------------
s = content("Acquisition Modes: Whiskbroom & Pushbroom",
            "Part 2 · Scanning Imagers", SRC2)
chip(s, 0.5, 1.45, 6.95, 2.55,
     "Whiskbroom Mode  (Point-Scanning，扫帚式 / 点扫描)", [
    P("Optical path: a scanning mirror moves across the scene, one spatial point at a time. "
      "Each single point acquires its complete full spectrum; the cube is built by scanning "
      "every pixel point-by-point.", 10.8, ls=1.15),
    P("✅  Pros: high spectral quality for each sampled point; good SNR.", 10.8, True, GREEN, before=5),
    P("❌  Cons: two-axis mechanical scanning; long acquisition time; moving-part artifacts.",
      10.8, True, RED, before=2)], hc=NAVY, hs=12.5)
chip(s, 0.5, 4.18, 6.95, 2.62,
     "Pushbroom Mode  (Line-Scanning，推扫式 / 线扫描)", [
    P("Optical path: simultaneously captures an entire line of spatial information plus the "
      "full spectrum for each pixel on that line. The complete 2-D area is obtained via relative "
      "platform motion (aircraft / satellite / translation stage).", 10.8, ls=1.15),
    P("✅  Pros: much faster than whiskbroom; widely used in remote sensing.",
      10.8, True, GREEN, before=5),
    P("❌  Cons: depends on steady relative movement between sensor and target.",
      10.8, True, RED, before=2)], hc=GOLD, hs=12.5)
rect(s, 7.65, 1.45, 5.18, 5.35, WHITE, line=BORDER)
pic_fit(s, os.path.join(MEDIA, "p2_s4_5.png"), 7.85, 1.6, 4.78, 4.55,
        border=False, cr=0.5, cb=0.09)
text(s, 7.85, 6.22, 4.78, 0.5,
     [P("FIGURE 2. (a) Point scanning or whiskbroom, (b) Line scanning or pushbroom [1]",
        9.5, True, NAVY, align=PP_ALIGN.CENTER, ls=1.05)])

# --- 2.3 Staring + FIGURE 3 -------------------------------------------------
s = content("Acquisition Mode: Staring",
            "Part 2 · Spectral Scanning (SC)", SRC2)
chip(s, 0.5, 1.45, 7.55, 5.35,
     "Staring Mode  (Spectral Scanning，凝视式 / 光谱扫描)", [
    P("Optical path: keep the whole scene stationary on the detector; use tunable optical "
      "filters (AOTF, LCTF, FPI, LVF) to sequentially select one wavelength band. Stack a series "
      "of 2-D images to reconstruct the full 3-D data cube.", 12.5, ls=1.2, after=10),
    P("✅  Pros", 13, True, GREEN, after=2),
    P("Captures the full-field scene for each wavelength; no spatial mechanical scanning.",
      12.5, ls=1.18, after=10),
    P("❌  Cons", 13, True, RED, after=2),
    P("Wavelength scanning takes time; poor performance for dynamic moving scenes.",
      12.5, ls=1.18)], hc=NAVY, hs=14)
rect(s, 8.25, 1.45, 4.58, 5.35, WHITE, line=BORDER)
pic_fit(s, os.path.join(MEDIA, "p2_s5_5.png"), 8.7, 1.6, 3.68, 4.55,
        border=False, cl=0.28, cr=0.27, cb=0.09)
text(s, 8.4, 6.22, 4.3, 0.5,
     [P("FIGURE 3. (c) Spectral scanning (SC) or staring [1]", 10, True, NAVY,
        align=PP_ALIGN.CENTER)])

# --- 2.4 Trade-off -----------------------------------------------------------
s = content("Trade-off Between Spatial Resolution and Spectral Resolution",
            "Part 2 · Principles of Spectral Imaging", SRC2)
trade = [
    ("Intrinsic trade-off",
     "In conventional spectral-imaging optical systems, there exists an intrinsic trade-off "
     "between spatial resolution and spectral resolution [1].", NAVY),
    ("Higher spectral resolution",
     "Requires more, narrower spectral bands. Under limited photon budget and detector "
     "constraints, this often sacrifices spatial sampling performance.", TEAL),
    ("Higher spatial resolution",
     "If you pursue fine spatial details, the number of available spectral channels will be "
     "limited.", GOLD),
    ("Advanced approaches",
     "Snapshot imaging and compressive computational imaging can mitigate this conflict, but "
     "cannot completely eliminate the fundamental physical limits from photon availability.", RED),
]
for i, (h, b, c) in enumerate(trade):
    x = 0.5 + (i % 2) * 6.28
    y = 1.7 + (i // 2) * 2.5
    card(s, x, y, 6.05, 2.3, accent='left', ac=c)
    oval(s, x + 0.22, y + 0.22, 0.5, c, str(i + 1), fs=14)
    text(s, x + 0.9, y + 0.24, 5.0, 0.4, [P(h, 14.5, True, c)])
    text(s, x + 0.25, y + 0.85, 5.6, 1.3, [P(b, 11.8, ls=1.22)])

# --- 2.5 MSI -----------------------------------------------------------------
s = content("MULTISPECTRAL IMAGING  多光谱成像",
            "Part 2 · Multispectral Imaging (MSI)", SRC2)
card(s, 0.8, 1.75, 11.73, 2.5, accent='left', ac=NAVY)
text(s, 1.15, 1.95, 11.1, 2.2, [
    P("English  [1]", 11, True, GRAY),
    P("By capturing and analyzing how objects reflect, absorb, or emit light across different "
      "spectral bands, MSI uncovers information about the composition, structure, and properties "
      "of a scene or object. [1]", 15, before=4, ls=1.3)])
card(s, 0.8, 4.5, 11.73, 2.1, accent='left', ac=GOLD)
text(s, 1.15, 4.7, 11.1, 1.8, [
    P("中文", 11, True, GRAY),
    P("通过捕捉和分析物体在不同光谱带中反射、吸收或发射光的方式，多光谱成像（MSI）"
      "能够揭示场景或物体的组成、结构和特性信息。", 15, before=4, ls=1.3)])

# --- 2.5F Literature figure: MSI platforms ----------------------------------
s = content("Figures from the Literature · Real Multispectral Imaging Platforms",
            "Part 2 · Multispectral Imaging (MSI)",
            "Mukhtar et al., 2025 (IEEE Access)")
pic_fit(s, os.path.join(MEDIA, "fig_msi_platforms.png"),
        1.0, 1.4, 11.33, 3.6)
fcap(s, 1.0, 5.02, 11.33,
     "FIGURE 8. Representative MSI systems: tunable-LED underwater imager, "
     "portable LED-based field imager, and a snapshot pixel-wise "
     "polarization camera. (Mukhtar et al., 2025, IEEE Access)")
for i, (h, b, c) in enumerate([
    ("(a)  TuLUMIS — underwater MSI",
     "Tunable LED-based underwater multispectral system: LEDs, camera and "
     "control electronics, here mounted on the PELAGIOS frame during a "
     "deployment cruise.", NAVY),
    ("(b)  Portable LED MSI imager",
     "Low-cost multispectral imager with a multi-spectral LED board and a "
     "tablet for real-time visualisation — compact for field applications.",
     TEAL),
    ("(c)  Snapshot P-DACC camera",
     "Pixel-wise polarization sensor with colour wheel and imaging lens: a "
     "single exposure captures a multispectral / polarisation data cube.",
     GOLD),
]):
    x = 0.5 + i * 4.16
    card(s, x, 5.55, 3.98, 1.32, accent='top', ac=c)
    text(s, x + 0.18, 5.66, 3.62, 0.3, [P(h, 10.8, True, c)])
    text(s, x + 0.18, 5.97, 3.62, 0.85, [P(b, 9.2, ls=1.1)])

# --- 2.6 HSI ------------------------------------------------------------------
s = content("HYPERSPECTRAL IMAGING  高光谱成像",
            "Part 2 · Hyperspectral Imaging (HSI)", SRC2)
card(s, 0.8, 1.75, 11.73, 2.5, accent='left', ac=NAVY)
text(s, 1.15, 1.95, 11.1, 2.2, [
    P("English  [1]", 11, True, GRAY),
    P("While MSI systems have long provided a balance between spectral information and ease of "
      "implementation, the HSI systems have pushed the boundaries in terms of providing deep "
      "spectral insight. [1]", 15, before=4, ls=1.3)])
card(s, 0.8, 4.5, 11.73, 2.1, accent='left', ac=GOLD)
text(s, 1.15, 4.7, 11.1, 1.8, [
    P("中文", 11, True, GRAY),
    P("虽然多光谱成像（MSI）系统长期以来一直在光谱信息与实施便捷性之间寻求平衡，"
      "但高光谱成像（HSI）系统在提供深入的光谱洞察方面则突破了界限。", 15, before=4, ls=1.3)])

# --- 2.7 HSI pros -------------------------------------------------------------
s = content("HSI · Advantages in Agriculture & Food Quality Estimation",
            "Part 2 · Hyperspectral Imaging (HSI)", "[2] Lu & Fei, 2014")
text(s, 0.5, 1.4, 12.3, 0.5,
     [P("The pros of using Hyperspectral Imaging in different applications such as agriculture, "
        "and food quality estimation are as follows [2]:", 13, True, NAVY)])
pros = [
    ("(i)", "It is a non-invasive, non-contact, non-destructive technology that ensures the "
     "quality and safety of food goods."),
    ("(ii)", "The experiments use no chemicals, therefore environmentally safe."),
    ("(iii)", "The time required to process for quality evaluation and food control/storage is "
     "low compared to chemical and traditional approaches."),
    ("(iv)", "It gives an improved understanding of the chemical elements of food products and is "
     "generally known as chemical imaging."),
    ("(v)", "It provides appropriate area selection for critical analysis of the image."),
    ("(vi)", "It gains spatial and spectral information together to provide more appropriate and "
     "accurate data concerning chemical samples from interested platforms and enhance a chance "
     "to data refine and achieve further experiments."),
]
for i, (n, b) in enumerate(pros):
    x = 0.5 + (i % 3) * 4.16
    y = 2.05 + (i // 3) * 2.35
    card(s, x, y, 3.98, 2.15, accent='top', ac=GREEN)
    text(s, x + 0.2, y + 0.18, 3.6, 0.35, [P(n, 15, True, GREEN)])
    text(s, x + 0.2, y + 0.6, 3.6, 1.45, [P(b, 10.8, ls=1.18)])

# --- 2.8 HSI cons -------------------------------------------------------------
s = content("HSI · Limitations",
            "Part 2 · Hyperspectral Imaging (HSI)", "[2] Lu & Fei, 2014")
text(s, 0.5, 1.45, 12.3, 0.4,
     [P("Despite its pros, Hyperspectral Imaging also has some cons [2].", 14, True, NAVY)])
cons = [
    ("(i)  High cost",
     "A hyperspectral imaging system is highly costly compared to other image processing "
     "techniques.", RED),
    ("(ii)  Large data size",
     "Since the data size of hyperspectral imaging is large, there is a demand for high-speed "
     "computers for the processing of data and extensive capacity drives for the storage of data.",
     GOLD),
    ("(iii)  Ambient interference",
     "While acquiring the images, the signal could be impacted by ambient surroundings such as "
     "scattering, illumination, etc., therefore producing a destitute signal-to-noise ratio.", TEAL),
    ("(iv)  Difficult discrimination",
     "Detection and identification of different items within the equivalent image using spectral "
     "data is mostly difficult except the diverse objects have distinct absorption features.", NAVY),
]
for i, (h, b, c) in enumerate(cons):
    x = 0.5 + (i % 2) * 6.28
    y = 2.0 + (i // 2) * 2.4
    card(s, x, y, 6.05, 2.2, accent='left', ac=c)
    text(s, x + 0.28, y + 0.2, 5.6, 0.4, [P(h, 13.5, True, c)])
    text(s, x + 0.28, y + 0.72, 5.55, 1.35, [P(b, 11.5, ls=1.22)])

# --- 2.9 MSI vs HSI bilingual table + spectra -------------------------------
s = content("Multispectral Imaging VS Hyperspectral Imaging",
            "Part 2 · Multispectral vs. Hyperspectral", SRC2)
rows_n = 5
gf = s.shapes.add_table(rows_n, 3, Inches(0.5), Inches(1.4),
                        Inches(12.33), Inches(3.65))
tbl = gf.table; tbl.first_row = False; tbl.horz_banding = False
tbl.columns[0].width = Inches(2.75)
tbl.columns[1].width = Inches(4.79)
tbl.columns[2].width = Inches(4.79)
tdata = [
    ("", "Multispectral Imaging  多光谱成像", "Hyperspectral Imaging  高光谱成像"),
    ("Spectral bands\n光谱波段",
     "Discrete widely-spaced bands (typically 3–25 bands)",
     "Hundreds of contiguous narrow spectral bands"),
    ("Spectral signature\n光谱特征",
     "Coarse spectral sampling",
     "Dense continuous spectral fingerprint per pixel"),
    ("Data volume\n数据量",
     "Small, easy to process",
     "Large 3-D data cube, heavy computation load"),
    ("Typical strength\n优势",
     "Higher spatial / temporal resolution; low cost",
     "Fine material discrimination by continuous spectrum"),
]
for ri, row in enumerate(tdata):
    tbl.rows[ri].height = Inches(0.6 if ri == 0 else 0.76)
    for ci, val in enumerate(row):
        cell = tbl.cell(ri, ci)
        cell.margin_left = Inches(0.1); cell.margin_right = Inches(0.08)
        cell.margin_top = Inches(0.03); cell.margin_bottom = Inches(0.03)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        if ri == 0:
            cell.fill.solid(); cell.fill.fore_color.rgb = NAVY
            col, bold, sz = WHITE, True, 13.5
        elif ci == 0:
            cell.fill.solid(); cell.fill.fore_color.rgb = BG
            col, bold, sz = NAVY, True, 11.5
        else:
            cell.fill.solid(); cell.fill.fore_color.rgb = WHITE
            col, bold, sz = DARK, False, 11.5
        lines = val.split("\n")
        p0 = cell.text_frame.paragraphs[0]
        r = p0.add_run(); r.text = lines[0]; _st(r, sz, bold, col)
        if len(lines) > 1:
            p1 = cell.text_frame.add_paragraph()
            r1 = p1.add_run(); r1.text = lines[1]; _st(r1, sz - 1.5, bold, GOLD)
rect(s, 0.5, 5.25, 12.33, 1.55, WHITE, line=BORDER)
pic_fit(s, os.path.join(MEDIA, "p2_s11_13.png"), 0.7, 5.33, 11.93, 1.4,
        border=False)

# ########################################################## PART 3 #########
divider(3, "Data Processing & Analysis", "光谱数据处理与分析",
        "Preprocessing: radiometric & atmospheric correction\n"
        "Dimensionality reduction: PCA vs. MNF\n"
        "Spectral classification (SAM) · Statistical validation · Paper excerpts")

# --- 3.1 terminology table --------------------------------------------------
s = content("Basic Terminology  基本术语",
            "Part 3 · Data Processing & Analysis", SRC3)
terms = [
    ("辐射定标", "Radiometric Calibration", "将传感器原始 DN 值转换为辐射亮度 / 反射率的过程"),
    ("大气校正", "Atmospheric Correction", "消除大气散射、吸收对地表反射率的影响"),
    ("光谱响应函数", "Spectral Response Function (SRF)", "传感器对不同波长的响应曲线"),
    ("半高宽", "Full Width at Half Maximum (FWHM)", "光谱响应峰半高处的宽度，表征光谱分辨率"),
    ("光谱微笑效应", "Spectral Smile", "推扫式传感器跨轨方向中心波长偏移现象"),
    ("基线校正", "Baseline Correction", "去除荧光 / 散射造成的低频背景漂移"),
    ("噪声等效辐亮度", "Noise Equivalent Radiance (NER)", "表征传感器噪声水平"),
    ("几何校正", "Geometric Correction", "将图像像素与地理坐标配准"),
]
g = s.shapes.add_table(9, 3, Inches(0.5), Inches(1.45),
                       Inches(12.33), Inches(5.4))
tb = g.table; tb.first_row = False; tb.horz_banding = False
tb.columns[0].width = Inches(2.55); tb.columns[1].width = Inches(4.55)
tb.columns[2].width = Inches(5.23)
head = ("中文", "English", "含义")
allrows = [head] + terms
for ri, row in enumerate(allrows):
    tb.rows[ri].height = Inches(0.55 if ri == 0 else 0.6)
    for ci, val in enumerate(row):
        cell = tb.cell(ri, ci)
        cell.margin_left = Inches(0.12); cell.margin_right = Inches(0.08)
        cell.margin_top = Inches(0.02); cell.margin_bottom = Inches(0.02)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        if ri == 0:
            cell.fill.solid(); cell.fill.fore_color.rgb = NAVY
            col, bold, sz = WHITE, True, 12.5
        elif ci == 0:
            cell.fill.solid(); cell.fill.fore_color.rgb = BG
            col, bold, sz = NAVY, True, 11.5
        elif ci == 1:
            cell.fill.solid(); cell.fill.fore_color.rgb = WHITE
            col, bold, sz = TEAL, True, 11
        else:
            cell.fill.solid(); cell.fill.fore_color.rgb = WHITE
            col, bold, sz = DARK, False, 11
        r = cell.text_frame.paragraphs[0].add_run(); r.text = val
        _st(r, sz, bold, col)

# --- 3.2 pipeline -----------------------------------------------------------
s = content("Processing Pipeline  流程总览",
            "Part 3 · Data Processing & Analysis", SRC3)
text(s, 0.5, 1.5, 12.3, 0.4,
     [P("先看这张流程图，三步：", 15, True, NAVY)])
steps3 = [
    ("STEP 1", "Preprocessing", "预处理",
     "Calibration & correction: DN → radiance / reflectance", NAVY),
    ("STEP 2", "Dimensionality Reduction", "降维",
     "Compress hundreds of correlated bands (PCA / MNF)", TEAL),
    ("STEP 3", "Classification & Recognition", "分类与识别",
     "Identify materials with spectral classifiers (SAM, SVM…)", GOLD),
]
for i, (tag, en, cn, desc, c) in enumerate(steps3):
    x = 0.5 + i * 4.16
    rect(s, x, 2.25, 3.98, 3.6, BG); rect(s, x, 2.25, 3.98, 0.75, c)
    text(s, x, 2.38, 3.98, 0.5, [P(tag, 17, True, WHITE,
                                    align=PP_ALIGN.CENTER)],
         anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.2, 3.2, 3.6, 0.7, [P(en, 15.5, True, c,
                                        align=PP_ALIGN.CENTER, ls=1.0)])
    text(s, x + 0.2, 3.92, 3.6, 0.4, [P(cn, 17, True, NAVY,
                                         align=PP_ALIGN.CENTER)])
    text(s, x + 0.25, 4.6, 3.5, 1.1,
         [P(desc, 11.5, False, GRAY, align=PP_ALIGN.CENTER, ls=1.2)])
    if i < 2:
        text(s, x + 3.86, 3.4, 0.45, 0.8,
             [P("→", 26, True, GRAY, align=PP_ALIGN.CENTER)])
rect(s, 0.5, 6.15, 12.33, 0.65, NAVY)
text(s, 0.8, 6.27, 11.8, 0.45,
     [P("Preprocessing  →  Dimensionality Reduction  →  Classification & Recognition",
        14, True, WHITE, align=PP_ALIGN.CENTER)])

# --- 3.3 calibration --------------------------------------------------------
s = content("Preprocessing (I) · Calibration  预处理 · 定标类",
            "Part 3 · Step 1 — Preprocessing",
            "Yamamoto et al., 2022")
text(s, 0.5, 1.4, 12.3, 0.35,
     [P("这一页有四个高频词：", 13, True, NAVY)])
cals = [
    ("1  Radiometric Calibration（辐射定标）",
     "把仪器记到的数字 DN（digital number）换算成真实的辐射亮度或反射率。"
     "没有这一步，数据只是一堆数字。", NAVY),
    ("2  Spectral Response Function（SRF，光谱响应函数）",
     "传感器对每个波长“有多敏感”，是一条随波长变化的曲线。", TEAL),
    ("3  FWHM（Full Width at Half Maximum，半高宽）",
     "峰高一半处的宽度。它越小，光谱分辨率越高。", GOLD),
    ("4  Spectral Smile（光谱微笑效应）",
     "中间和两边的波长对不齐，曲线像一张微笑的嘴。", RED),
]
for i, (h, b, c) in enumerate(cals):
    x = 0.5 + (i % 2) * 6.28
    y = 1.85 + (i // 2) * 1.62
    card(s, x, y, 6.05, 1.45, accent='left', ac=c)
    text(s, x + 0.28, y + 0.12, 5.6, 0.4, [P(h, 12, True, c)])
    text(s, x + 0.28, y + 0.55, 5.6, 0.85, [P(b, 11, ls=1.18)])
quote_card(s, 0.5, 5.2, 12.33, 1.6, [
    "“The path of the light from the lamps is slightly different from the path of light "
    "through the full optical system… the smile correction table determined based on the "
    "former does not enable sufficient spectral smile correction for actual observation images.”",
    "“…absorption bands centered at λ = 765 nm … CO₂ … 2010 nm … 2060 nm.”"],
    src="— Yamamoto et al., 2022 (HISUI spectral-smile calibration)")

# --- 3.4 atmospheric correction --------------------------------------------
s = content("Preprocessing (II) · Atmospheric Correction  大气校正",
            "Part 3 · Step 1 — Preprocessing", "Roussel et al., 2017")
atms = [
    ("1  Atmospheric Correction（大气校正）",
     "光从太空到地面会被大气散射和吸收，这一步把干扰减掉，还原地表真实反射率。", NAVY),
    ("2  MODTRAN",
     "常用的大气辐射传输模型，物理法大气校正靠它算大气参数。", TEAL),
    ("3  COCHISE vs. 经验阴影校正法",
     "物理模型法（COCHISE）准，但假设地面是平的；经验阴影校正法能识别阴影，"
     "但把像素当成“要么全亮、要么全暗”。", GOLD),
    ("4  Spatial Resolution（空间分辨率）",
     "决定哪种方法更好：空间分辨率越低，COCHISE 相对经验法的优势越大。", RED),
]
for i, (h, b, c) in enumerate(atms):
    y = 1.55 + i * 1.06
    card(s, 0.5, y, 12.33, 0.95, accent='left', ac=c)
    text(s, 0.85, y + 0.1, 4.5, 0.75, [P(h, 12.5, True, c)],
         anchor=MSO_ANCHOR.MIDDLE)
    text(s, 5.45, y + 0.1, 7.2, 0.78, [P(b, 11.3, ls=1.12)],
         anchor=MSO_ANCHOR.MIDDLE)
quote_card(s, 0.5, 5.85, 12.33, 0.95, [
    "“…the choice depends on the spatial resolution of the processed data set… with the lower "
    "spatial resolution where COCHISE can be 10% more accurate than the empirical method.”"],
    src="— Roussel et al., 2017")

# --- 3.4F Literature figures: spectral smile + atmosphere -------------------
s = content("Figures from the Literature · Spectral Smile & Atmospheric Paths",
            "Part 3 · Calibration & Atmospheric Correction",
            "Yamamoto et al., 2022 · Shaw & Burke, 2003")
pic_fit(s, os.path.join(MEDIA, "fig_smile_curves.png"),
        0.45, 1.45, 7.55, 4.55)
fcap(s, 0.45, 6.02, 7.55,
     "Fig. 9–10. SWIR colour composites (left) and measured centre-wavelength "
     "shift δλ of the spectral smile along across-track samples for SWIR "
     "bands S1–S3 of HISUI (right). (Yamamoto et al., 2022)")
pic_fit(s, os.path.join(MEDIA, "fig_atmosphere.png"),
        8.2, 1.45, 4.68, 4.55)
fcap(s, 8.2, 6.02, 4.68,
     "FIGURE 5. Solar illumination, atmospheric absorption and scattering, "
     "upwelling radiance and the ground pixel viewed by the sensor. "
     "(Shaw & Burke, 2003)")

# --- 3.5 Raman vs FTIR -------------------------------------------------------
s = content("Preprocessing (III) · Raman vs. FTIR  拉曼 vs 红外",
            "Part 3 · Step 1 — Scatter & Baseline Correction",
            "Gautam et al., 2015")
rect(s, 0.5, 1.45, 12.33, 3.05, BG); rect(s, 0.5, 1.45, 0.12, 3.05, NAVY)
raman = [
    ("Fluorescence Baseline（荧光基线）",
     "拉曼信号弱，被荧光背景盖住，要先做 Baseline Correction（基线校正）。"),
    ("Cosmic Ray Spike（宇宙射线尖峰）", "CCD 上突然冒出的假亮点，要先去掉。"),
    ("ALS（Asymmetric Least Squares）", "非对称最小二乘法，常用的拟合基线算法。"),
    ("Mie Scattering（米氏散射）", "细胞大小和红外波长差不多，会把光谱形状扭歪。"),
    ("EMSC（Extended Multiplicative Scatter Correction，扩展乘性散射校正）",
     "红外里最常用的预处理。"),
]
yy = 1.62
for h, b in raman:
    text(s, 0.85, yy, 5.4, 0.55, [P(h, 11.5, True, TEAL)],
         anchor=MSO_ANCHOR.MIDDLE)
    text(s, 6.3, yy, 6.35, 0.55, [P(b, 11, ls=1.1)],
         anchor=MSO_ANCHOR.MIDDLE)
    yy += 0.57
text(s, 0.85, yy + 0.02, 11.8, 0.3,
     [P("【文献出处】Gautam 2015：拉曼的荧光基线、宇宙射线尖峰、ALS、SG 平滑、SNV；"
        "FTIR 的 Mie 散射、MSC / EMSC。", 10, True, GOLD)])
quote_card(s, 0.5, 4.7, 12.33, 2.1, [
    "“…the strong intrinsic fluorescence from many biomolecules. The fluorescence background is "
    "often many times more intense than the weak Raman signals.”",
    "“…mid-infrared spectrum… is hampered by Mie scattering… Extended Multiplicative Scatter "
    "Correction (EMSC) can be employed for this purpose.”"],
    src="— Gautam et al., 2015")

# --- 3.6 PCA ------------------------------------------------------------------
s = content("Dimensionality Reduction · PCA  降维：主成分分析",
            "Part 3 · Step 2 — Dimensionality Reduction", "Gautam et al., 2015")
pca_items = [
    ("Hyperspectral Cube（高光谱数据立方体）",
     "两个空间维度 + 一个光谱维度，一景图有几百个波段。"),
    ("为什么降维？",
     "因为波段之间高度相关。"),
    ("PCA（Principal Component Analysis，主成分分析）",
     "把几百个波段“拧成”几个 PC（主成分）。"),
    ("Eigenvalue / Eigenvector（特征值 / 特征向量）",
     "PCA 的数学基础，由协方差矩阵分解得到。"),
    ("Score Plot（得分图） / Loading Plot（载荷图）",
     "Score Plot 看样本分成几堆（分组与离群点）；Loading Plot 看哪些波长在起作用；"
     "Scree Plot（碎石图）用于选择保留的 PC 数。"),
    ("【文献出处】Gautam 2015",
     "PCA 原理、协方差矩阵特征分解、Score / Loading plot、碎石图选 PC 数。"),
]
rect(s, 0.5, 1.45, 12.33, 3.85, BG); rect(s, 0.5, 1.45, 0.12, 3.85, TEAL)
text(s, 0.85, 1.55, 11.8, 0.35, [P("二、降维：PCA", 14, True, NAVY)])
yy = 1.98
for i, (h, b) in enumerate(pca_items):
    oval(s, 0.82, yy + 0.02, 0.3, [TEAL, NAVY, GOLD, TEAL, NAVY, GOLD][i],
         str(i + 1), fs=10)
    text(s, 1.3, yy, 4.3, 0.52, [P(h, 11.3, True, NAVY)],
         anchor=MSO_ANCHOR.MIDDLE)
    text(s, 5.65, yy, 7.0, 0.52, [P(b, 10.8, ls=1.08)],
         anchor=MSO_ANCHOR.MIDDLE)
    yy += 0.55
quote_card(s, 0.5, 5.5, 12.33, 1.3, [
    "“Eigenvectors of the covariance matrix of the data…”  — Fig. 1: “Scatter Plots of score "
    "values of different Principal Components (PCs)…” used to inspect groups and outliers."],
    src="— Gautam et al., 2015")

# --- 3.7 PCA vs MNF -----------------------------------------------------------
s = content("PCA vs. MNF  主成分分析 vs. 最小噪声分离",
            "Part 3 · Step 2 — Dimensionality Reduction", "Gautam et al., 2015")
text(s, 0.5, 1.45, 12.3, 0.35, [P("重点对比两个词：", 13, True, NAVY)])
card(s, 0.5, 1.9, 6.05, 2.75, accent='top', ac=NAVY)
text(s, 0.75, 2.08, 5.6, 2.5, [
    P("PCA", 20, True, NAVY),
    P("按 Variance（方差）大小排序。", 12.5, before=4, ls=1.2),
    P("PCA 最大化方差，但不区分信号与噪声——高方差成分也可能只是噪声。",
      11.5, before=4, ls=1.2)])
card(s, 6.78, 1.9, 6.05, 2.75, accent='top', ac=GOLD)
text(s, 7.03, 2.08, 5.6, 2.5, [
    P("MNF（Minimum Noise Fraction，最小噪声分离）", 16, True, GOLD),
    P("先把噪声“白化”（noise whitening），再做 PCA，按 Signal-to-Noise Ratio "
      "（SNR，信噪比）排序。", 12.5, before=4, ls=1.2),
    P("高信噪比成分排在前面，噪声分离能力更强，高光谱里用得更多。",
      11.5, before=4, ls=1.2)])
rect(s, 0.5, 4.85, 12.33, 1.0, NAVY)
text(s, 0.8, 5.02, 11.8, 0.7,
     [P("一句话：PCA 看方差大不大，MNF 看信噪比高不高。高光谱里 MNF 用得更多。",
        14, True, WHITE, align=PP_ALIGN.CENTER)],
     anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.5, 6.05, 12.3, 0.7,
     [P("【文献出处】Gautam 2015：PCA 按方差排序的局限；MNF 按 SNR 排序与噪声分离能力。",
        11, True, GOLD, align=PP_ALIGN.CENTER, ls=1.15)])

# --- 3.7F Literature figures: preprocessed spectra + PCA scores -------------
s = content("Figures from the Literature · Preprocessed Spectra & PCA Scores",
            "Part 3 · Preprocessing & Dimensionality Reduction",
            "Gautam et al., 2015")
pic_fit(s, os.path.join(MEDIA, "fig_raman_preproc.png"),
        0.5, 1.45, 5.7, 4.95)
fcap(s, 0.5, 6.42, 5.7,
     "Fig. 4. Raw (top) and preprocessed (bottom) Raman spectra of muscle "
     "tissue (control CS flies, 2 days old); shaded band = ±1 SD around the "
     "mean. Preprocessing enhances the diagnostic Raman features. "
     "(Gautam et al., 2015)")
pic_fit(s, os.path.join(MEDIA, "fig_pca_scores.png"),
        6.45, 1.45, 6.38, 4.25)
fcap(s, 6.45, 5.72, 6.38,
     "Fig. 5. PC-LDA 3-D score plots of 2- and 12-day-old flies: upshed "
     "mutants (blue / magenta) separate well from control CS (black), "
     "whereas the two control age groups almost merge. (Gautam et al., 2015)")
rect(s, 6.45, 6.45, 6.38, 0.42, BG)
text(s, 6.6, 6.49, 6.1, 0.35,
     [P("Score plots visualise class separation — the goal of dimensionality "
        "reduction before classification.", 10, True, NAVY,
        align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE)

# --- 3.8 SAM ------------------------------------------------------------------
s = content("Classification · Spectral Angle Mapper  分类：光谱角度匹配",
            "Part 3 · Step 3 — Classification & Recognition",
            "Roussel et al., 2017")
sams = [
    ("SAM（Spectral Angle Mapper，光谱角度匹配）",
     "把每条光谱看成一条向量，比较两条向量的夹角；夹角越小越像。", NAVY),
    ("关键：只看形状，不看亮度",
     "阴影像素虽然整体变暗，但光谱形状没变，照样能和光照下的同类对上号。", TEAL),
    ("Sun-Shadow Strategy（光照-阴影分步策略）",
     "先用光照像元（Sunlit Ground Truth, SGT）做分类（K-Means / SVM，SS-KM / SS-SVM），"
     "再用 SAM 去认阴影像元。", GOLD),
    ("【文献出处】Roussel 2017",
     "光照-阴影分步策略、用 SAM 匹配阴影像元、训练集只有光照像元（SGT）的真实城市场景。", RED),
]
for i, (h, b, c) in enumerate(sams):
    x = 0.5 + (i % 2) * 6.28
    y = 1.55 + (i // 2) * 2.0
    card(s, x, y, 6.05, 1.8, accent='left', ac=c)
    text(s, x + 0.28, y + 0.14, 5.6, 0.4, [P(h, 12.5, True, c)])
    text(s, x + 0.28, y + 0.6, 5.6, 1.1, [P(b, 11, ls=1.16)])
quote_card(s, 0.5, 5.7, 12.33, 1.1, [
    "“…a Spectral Angle Mapper (SAM) classification has been chosen for its ability to focus "
    "on the shape of spectra, which remains globally similar for a pair of pixels associated to "
    "the same material, even if one is located in a sunlit area and the other in a shadow area.”"],
    src="— Roussel et al., 2017")

# --- 3.9 Validation -----------------------------------------------------------
s = content("Validation of Spectral Models  模型验证",
            "Part 3 · Step 3 — Validation", "Gautam et al., 2015")
vals3 = [
    ("Cross-Validation（交叉验证）",
     "常用 K-fold（K 折交叉验证）轮换训练 / 验证子集，检验模型的泛化能力。", NAVY),
    ("Confusion Matrix（混淆矩阵）",
     "TP 真阳性、TN 真阴性、FP 假阳性、FN 假阴性；由此算出 Sensitivity（灵敏度）、"
     "Specificity（特异度）和 Overall Accuracy（总精度）。", TEAL),
    ("ROC Curve & AUC",
     "ROC 曲线与曲线下面积 AUC，用于评价不同阈值下的分类性能。", GOLD),
    ("Overfitting & Negative Controls",
     "警惕 Overfitting（过拟合）；用阴性对照（negative controls）防止伪相关。", RED),
]
for i, (h, b, c) in enumerate(vals3):
    x = 0.5 + (i % 2) * 6.28
    y = 1.55 + (i // 2) * 2.45
    card(s, x, y, 6.05, 2.25, accent='top', ac=c)
    text(s, x + 0.22, y + 0.18, 5.6, 0.4, [P(h, 13, True, c)])
    text(s, x + 0.22, y + 0.65, 5.6, 1.5, [P(b, 11.3, ls=1.22)])
text(s, 0.5, 6.55, 12.3, 0.35,
     [P("【文献出处】Gautam 2015：交叉验证、混淆矩阵、灵敏度 / 特异度、ROC-AUC、"
        "阴性对照防止伪相关。", 10.5, True, GOLD, align=PP_ALIGN.CENTER)])

# --- 3.9F Literature figures: classification maps + ROC ---------------------
s = content("Figures from the Literature · Classification Maps & ROC Validation",
            "Part 3 · Classification & Validation",
            "Roussel et al., 2017 · Gautam et al., 2015")
pic_fit(s, os.path.join(MEDIA, "fig_roussel_classif.png"),
        0.5, 1.4, 4.4, 5.05)
fcap(s, 0.5, 6.48, 4.4,
     "Figure 8. Classification results over four urban study areas for eight "
     "processing chains (CM/EM × KM, SS-KM, SVM, SS-SVM). (Roussel et al., 2017)")
pic_fit(s, os.path.join(MEDIA, "fig_roc.png"),
        5.15, 1.45, 4.5, 2.9)
fcap(s, 5.15, 4.37, 7.7,
     "Fig. 9. Receiver-operating-characteristic (ROC) plot: ideal and "
     "moderate models vs. the line of no discrimination. (Gautam et al., 2015)")
card(s, 9.85, 1.45, 3.0, 2.9, accent='top', ac=RED)
text(s, 10.05, 1.62, 2.62, 2.65, [
    P("Reading the ROC", 11.5, True, RED),
    P("•  Curve to the upper-left corner = 100 % sensitivity & specificity "
      "(ideal model).", 9.6, before=3, ls=1.12),
    P("•  45° diagonal = line of no discrimination (random labels).",
      9.6, before=3, ls=1.12),
    P("•  AUC near 1: strong model; below 0.5: worse than random.",
      9.6, before=3, ls=1.12)])
card(s, 5.15, 5.05, 7.7, 1.85, accent='left', ac=NAVY)
text(s, 5.42, 5.18, 7.25, 1.65, [
    P("How to read these figures", 11.5, True, NAVY),
    P("•  Maps let us compare algorithms visually: classes are water, "
      "vegetation, tile, asphalt and gravel — SAM-based chains recover "
      "shadowed pixels trained only on sunlit spectra.", 9.6, before=3, ls=1.12),
    P("•  ROC curves trade sensitivity against false-positive rate across "
      "thresholds; AUC summarises overall discrimination in one number.",
      9.6, before=3, ls=1.12)])

# --- 3.10 Excerpt 1 -----------------------------------------------------------
s = content("Paper Excerpt 1 · MSI Limitations & Atmospheric Correction",
            "Part 3 · Original Text — Roussel et al., 2017",
            "Roussel et al., 2017, Int. J. Remote Sensing")
quote_card(s, 0.5, 1.55, 12.33, 1.9, [
    "However, multispectral imagery is limited regarding spectral analysis. Its low spectral "
    "resolution does not allow the discrimination among the large variety of urban materials. "
    "Hyperspectral imagery, which is characterized by a very high spectral resolution and whose "
    "spatial resolution tends to improve (Briottet et al. 2011), has proved to be a promising "
    "tool to overcome this matter."], ac=NAVY)
quote_card(s, 0.5, 3.6, 12.33, 2.55, [
    "One of the keypoints to achieve these applications is the atmospheric correction phase which "
    "aims to retrieve, from at-sensor radiance, the reflectance associated to the targeted "
    "surface, which is by nature independent of the irradiance conditions on the one hand and of "
    "the environment topography on the other hand. Different correction methods exist. ATREM "
    "(Goetz et al. 1997) for ‘Atmospheric REMoval program’ and ACORN (Miller 2002) for "
    "‘Atmosphere CORrection Now’ assume a flat homogeneous ground hypothesis with a Lambertian "
    "surface."], ac=GOLD)
for i, (t, c) in enumerate([
    ("Briottet et al. 2011", NAVY),
    ("Goetz et al. 1997 · ATREM", TEAL),
    ("Miller 2002 · ACORN", GOLD),
]):
    x = 0.5 + i * 4.16
    rect(s, x, 6.35, 3.98, 0.45, c)
    text(s, x, 6.42, 3.98, 0.32, [P(t, 11.5, True, WHITE,
                                     align=PP_ALIGN.CENTER)])

# --- 3.11 Excerpt 2 PCA --------------------------------------------------------
s = content("Paper Excerpt 2 · Principal Component Analysis (PCA)",
            "Part 3 · Original Text — Gautam et al., 2015",
            "Gautam et al., EPJ Techniques and Instrumentation, 2015")
quote_card(s, 0.5, 1.6, 12.33, 2.3, [
    "Principal component analysis (PCA) is an unsupervised data transformation procedure of "
    "complex data sets. PCA is used for projecting a higher dimensional data matrix “X” onto a "
    "low component subspace. It reduces a set of variables into a smaller set of orthogonal, and "
    "therefore independent, principal components (PCs) in the direction of maximal variation — "
    "i.e. it reduces the dimensionality and retains the most significant information for further "
    "analysis."], ac=TEAL)
core = [
    ("Unsupervised transform", "of complex, high-dimensional data sets", NAVY),
    ("X → low-dimensional subspace", "project the high-dimensional matrix X", TEAL),
    ("Orthogonal, independent PCs", "smaller set of uncorrelated components", GOLD),
    ("Maximal-variance direction", "retains the most significant information", RED),
]
for i, (h, b, c) in enumerate(core):
    x = 0.5 + (i % 2) * 6.28
    y = 4.15 + (i // 2) * 1.25
    card(s, x, y, 6.05, 1.05, accent='left', ac=c)
    text(s, x + 0.28, y + 0.13, 5.6, 0.35, [P(h, 12.5, True, c)])
    text(s, x + 0.28, y + 0.5, 5.6, 0.45, [P(b, 11, False, GRAY)])

# --- 3.12 Excerpt 3 HISUI intro ------------------------------------------------
s = content("Paper Excerpt 3 · HISUI: Applications & Calibration Need",
            "Part 3 · Original Text — Yamamoto et al., 2022",
            "Yamamoto et al., IEEE TGRS, 60, 2022")
quote_card(s, 0.5, 1.55, 12.33, 2.75, [
    "Hyperspectral data can be used to extract various information from discrete absorption and "
    "reflection features of a target surface or atmosphere. Thus, HISUI data are expected to be "
    "useful in various fields, such as natural resources, agriculture, forestry, environmental "
    "monitoring, and Earth science [1]. For such applications, both an accurate spectral "
    "calibration and a radiometric calibration are necessary for the reliability of the "
    "information extracted from hyperspectral data (see, e.g., [2]–[4]). In particular, for "
    "push-broom-type sensors, it is important to evaluate and calibrate the spectral smile, which "
    "is a phenomenon showing a cross-track dependence in a deviation from the original wavelength "
    "assignment caused by optical distortions incident on the detector array."], ac=NAVY)
apps = ["Natural resources", "Agriculture", "Forestry",
        "Environmental monitoring", "Earth science"]
for i, a in enumerate(apps):
    x = 0.5 + i * 2.51
    rect(s, x, 4.55, 2.42, 0.7, [NAVY, TEAL, GOLD, TEAL, NAVY][i])
    text(s, x + 0.1, 4.68, 2.22, 0.5,
         [P(a, 11.5, True, WHITE, align=PP_ALIGN.CENTER, ls=1.0)])
rect(s, 0.5, 5.55, 12.33, 1.2, BG); rect(s, 0.5, 5.55, 0.12, 1.2, GOLD)
text(s, 0.82, 5.7, 11.9, 1.0, [
    P("In-text numbered citations", 12, True, GOLD),
    P("[1] HISUI mission overview  ·  [2]–[4] hyperspectral spectral & radiometric calibration "
      "studies — accurate calibration is essential for the reliability of extracted information.",
      11, before=2, ls=1.2)])

# --- 3.13 Excerpt 4 HISUI method -----------------------------------------------
s = content("Paper Excerpt 4 · Evaluating Spectral Smile by Atmospheric Correction",
            "Part 3 · Original Text — Yamamoto et al., 2022",
            "Yamamoto et al., IEEE TGRS, 60, 2022")
text(s, 0.5, 1.4, 12.3, 0.35,
     [P("B. Evaluation of the Spectral Smile by Atmospheric Correction",
        14, True, NAVY)])
quote_card(s, 0.5, 1.8, 12.33, 2.95, [
    "The analytical procedure to evaluate the spectral smile by atmospheric correction was given "
    "as follows. In this analysis, we used the modeled radiance incident on HISUI from the target "
    "site, which was calculated using MODTRAN 6. MODTRAN calculations were performed using the "
    "U.S. Standard 1976 Atmospheric Profile, the desert aerosol model, and a Lambertian "
    "desert-barren surface type as representative parameter values. In addition, solar altitude, "
    "target latitude and longitude, ground height, and seasonal parameters were provided with "
    "values for each target and observation timing. These settings are a simple and efficient "
    "method for evaluating spectral smile for large numbers of pixels in a variety of HISUI "
    "scenes. Note that fine-tuning of MODTRAN parameters was not conducted for this analysis "
    "because the objective of this study was not to obtain accurate surface reflectance, but "
    "rather to estimate δλ using atmospheric absorption bands."], ac=TEAL)
params = [
    ("MODTRAN 6", "radiative-transfer model"),
    ("U.S. Standard 1976", "atmospheric profile"),
    ("Desert aerosol", "aerosol model"),
    ("Lambertian desert-barren", "surface type"),
    ("Solar altitude · lat/lon", "ground height · seasonal"),
    ("No fine-tuning", "goal: estimate δλ, not reflectance"),
]
for i, (h, b) in enumerate(params):
    x = 0.5 + (i % 3) * 4.16
    y = 4.95 + (i // 3) * 0.95
    card(s, x, y, 3.98, 0.82, accent='top',
         ac=[NAVY, TEAL, GOLD, RED, NAVY, TEAL][i])
    text(s, x + 0.15, y + 0.08, 3.7, 0.3, [P(h, 11, True, NAVY)])
    text(s, x + 0.15, y + 0.4, 3.7, 0.35, [P(b, 9.8, False, GRAY)])

# ########################################################## PART 4 #########
divider(4, "Applications & Future Trends", "应用案例与未来趋势",
        "Remote Sensing · Environmental Monitoring · Precision Agriculture\n"
        "Biomedical Imaging · Industrial Sorting\n"
        "Miniaturization · Real-time AI · Future trends")
SRC4 = "Shaw & Burke 2003 · Tolentino et al. 2025 · Raja et al. 2025\n" \
       "Tran & Fei 2023 · Romaniello et al. 2024 · Mukhtar et al. 2025"

# --- 4.1 Remote Sensing ------------------------------------------------------
s = content("Application 1 · Remote Sensing",
            "Part 4 · Applications & Future Trends", "Shaw & Burke, 2003")
card(s, 0.5, 1.45, 7.2, 2.4, accent='left', ac=NAVY)
text(s, 0.82, 1.6, 6.75, 2.1, [
    P("Background & Motivation", 14, True, NAVY),
    P("Spectral imaging arose as an alternative to high-spatial-resolution, "
      "large-aperture satellite imaging systems, using spectral signatures "
      "rather than spatial shapes to classify ground cover.", 11.5, before=4,
      ls=1.18)])
# sensor timeline
for i, (yr, name, desc, c) in enumerate([
    ("1972", "Landsat-1", "First spaceborne multispectral imager", NAVY),
    ("1987", "AVIRIS", "First airborne hyperspectral imager (full solar-reflective)", TEAL),
    ("2000", "Hyperion", "First spaceborne HSI — 220 bands, 30 m GSD", GOLD),
]):
    x = 0.5 + i * 2.51
    rect(s, x, 4.05, 2.42, 1.7, c)
    text(s, x + 0.12, 4.18, 2.18, 0.4, [P(yr, 18, True, WHITE,
                                            align=PP_ALIGN.CENTER)])
    text(s, x + 0.12, 4.6, 2.18, 0.35, [P(name, 12, True, WHITE,
                                           align=PP_ALIGN.CENTER)])
    text(s, x + 0.12, 5.0, 2.18, 0.7, [P(desc, 9.5, False, WHITE,
                                         align=PP_ALIGN.CENTER, ls=1.08)])
# three categories
card(s, 7.95, 1.45, 4.88, 5.35, accent='top', ac=TEAL)
text(s, 8.2, 1.65, 4.4, 0.4, [P("Three Major Application Categories", 12.5, True, TEAL)])
cats = [
    ("Anomaly Detection", "isolate uncommon features — e.g. man-made materials in natural backgrounds"),
    ("Target Recognition", "identify specific materials using a priori spectral libraries"),
    ("Background Characterization", "holistic scene analysis: land, ocean, and atmosphere"),
]
yy = 2.15
for h, b in cats:
    text(s, 8.2, yy, 4.4, 0.35, [P(h, 12, True, NAVY)])
    text(s, 8.2, yy + 0.38, 4.4, 0.7, [P(b, 10.2, ls=1.12)])
    yy += 1.15
text(s, 8.2, 6.4, 4.4, 0.3, [P("Shaw & Burke, 2003, pp.1, 9, 13–14, 19–20",
                                9, True, GRAY, it=True)])

# --- 4.2 Environmental Monitoring (Uranium mine) ---------------------------
s = content("Application 2 · Environmental Monitoring",
            "Part 4 · Applications & Future Trends",
            "Tolentino et al., 2025")
card(s, 0.5, 1.45, 6.05, 2.0, accent='left', ac=NAVY)
text(s, 0.82, 1.6, 5.65, 1.75, [
    P("Case: Mary Kathleen Uranium Legacy Mine, Australia", 13, True, NAVY),
    P("Tailings storage facility (~1.3 km², 5.5–7.5 Mt tailings) with acid "
      "mine drainage and heavy-metal / radionuclide migration risks.",
      10.8, before=4, ls=1.16)])
card(s, 6.78, 1.45, 6.05, 2.0, accent='left', ac=GOLD)
text(s, 7.1, 1.6, 5.65, 1.75, [
    P("Drone-Based HSI System", 13, True, GOLD),
    P("Sensor: HySpex Mjolnir VS-620 · VNIR–SWIR 400–2500 nm, 410 bands · "
      "Spatial resolution 6–10 cm/pixel (120 m altitude). Centimetre GSD "
      "reduces mixed-pixel effects.", 10.5, before=4, ls=1.14)])
# processing methods
card(s, 0.5, 3.62, 6.05, 1.55, accent='top', ac=TEAL)
text(s, 0.75, 3.78, 5.55, 1.3, [
    P("Processing Methods", 12.5, True, TEAL),
    P("•  SAM (Spectral Angle Mapper) — data-driven; classifies by spectral "
      "angle to endmembers", 10.5, before=3, ls=1.15),
    P("•  BR (Band Ratios) — knowledge-driven; reactivity & clay-mixture indices",
      10.5, before=2, ls=1.15)])
card(s, 6.78, 3.62, 6.05, 1.55, accent='top', ac=RED)
text(s, 7.03, 3.78, 5.55, 1.3, [
    P("Key Results", 12.5, True, RED),
    P("•  SAM differentiated mineral endmembers (gypsum, chlorite, clay) in "
      "visually uniform areas", 10.2, before=3, ls=1.1),
    P("•  Mapped evaporite salt pathways; identified EP & tailings-barrier "
      "degradation points", 10.2, before=2, ls=1.1)])
quote_card(s, 0.5, 5.35, 12.33, 1.45, [
    "“The results indicate that drone-based HSI can capture and distinguish "
    "complex surface trends, demonstrating the technology's potential to "
    "enhance the assessment and monitoring of environmental conditions at a "
    "mine site.”"], src="— Tolentino et al., 2025, Drones 9:313")

# --- 4.2F Literature figures: UAS platform + reactivity map -----------------
s = content("Figures from the Literature · Drone HSI at the Uranium Mine Site",
            "Part 4 · Environmental Monitoring",
            "Tolentino et al., 2025")
pic_fit(s, os.path.join(MEDIA, "fig_uas_drone.png"),
        0.45, 1.5, 6.1, 4.45)
fcap(s, 0.45, 5.98, 6.1,
     "Figure 3. The hyperspectral UAS: BFD SE-8 octocopter carrying a "
     "HySpex Mjolnir VS-620 camera and Velodyne LiDAR on a Gremsy gimbal. "
     "(Tolentino et al., 2025)")
pic_fit(s, os.path.join(MEDIA, "fig_reactivity_map.png"),
        6.75, 1.5, 6.1, 4.45)
fcap(s, 6.75, 5.98, 6.1,
     "Figure 11. Distinct spectral responses of reactive (red) and "
     "non-reactive (blue) surfaces captured by the “Reactivity” band ratio "
     "over a section of Site 2, with the resulting classification map. "
     "(Tolentino et al., 2025)")

# --- 4.3 Precision Agriculture (Rh-B) ---------------------------------------
s = content("Application 3 · Precision Agriculture",
            "Part 4 · Applications & Future Trends", "Raja et al., 2025")
card(s, 0.5, 1.45, 12.33, 1.7, accent='left', ac=NAVY)
text(s, 0.82, 1.6, 11.9, 1.5, [
    P("Challenge: Crop–Weed Differentiation in High-Density Fields", 14, True, NAVY),
    P("In organic farming, crop and weed foliage intertwine, defeating "
      "conventional classifiers — especially in celery. Innovation: Crop "
      "Signalling — pre-transplantation treatment of celery seedlings with "
      "Rhodamine B (Rh-B), a fluorescent compound producing machine-readable "
      "signals. Imaging: photometric monochrome camera + green LEDs (523 nm) "
      "+ bandpass filter (575/25 nm); conveyor speed 2.4 km/h mimics tractor "
      "field speed.", 10.5, before=4, ls=1.14)])
# three big numbers
for i, (num, label, sub, c) in enumerate([
    ("100%", "Crop–Weed Accuracy", "No false positives across 313 images", GREEN),
    ("99.66%", "Stem Location Precision", "Avg. error 3.58 mm", TEAL),
    ("30 ms", "Processing Time / Frame", "Enables real-time robotic weeding", GOLD),
]):
    x = 0.5 + i * 4.16
    rect(s, x, 3.35, 3.98, 2.6, WHITE, line=BORDER)
    rect(s, x, 3.35, 3.98, 0.12, c)
    text(s, x, 3.6, 3.98, 0.9, [P(num, 34, True, c, align=PP_ALIGN.CENTER)])
    text(s, x + 0.2, 4.55, 3.58, 0.4, [P(label, 13, True, NAVY,
                                           align=PP_ALIGN.CENTER)])
    text(s, x + 0.2, 4.95, 3.58, 0.85, [P(sub, 10.5, False, GRAY,
                                           align=PP_ALIGN.CENTER, ls=1.12)])
quote_card(s, 0.5, 6.1, 12.33, 0.8, [
    "“…achieving a 100% accuracy rate in detecting and distinguishing crop "
    "plants from weeds in densely populated fields, with no instances of "
    "false positives.”"], src="— Raja et al., 2025")

# --- 4.3F Literature figures: Rh-B imaging rig + fluorescence image --------
s = content("Figures from the Literature · Rh-B Fluorescence Imaging in the Field",
            "Part 4 · Precision Agriculture",
            "Raja et al., 2025")
pic_fit(s, os.path.join(MEDIA, "fig_rhb_setup.png"),
        0.5, 1.5, 7.4, 4.55)
fcap(s, 0.5, 6.08, 7.4,
     "Fig. 1. Fluorescence macroscopic imaging system: photometric camera, "
     "bandpass filter-lens, 12 green LEDs (523 nm) and the treated plant "
     "sample, with a captured Rh-B fluorescence image. (Raja et al., 2025)")
pic_fit(s, os.path.join(MEDIA, "fig_celery_fluoro.png"),
        8.1, 1.5, 4.73, 4.55)
fcap(s, 8.1, 6.08, 4.73,
     "Fig. 7. (a) Monochrome image under green-light illumination and "
     "(b) false-colour analysis highlighting celery crop among randomly "
     "placed weeds. (Raja et al., 2025)")

# --- 4.4 Biomedical Imaging (I) ---------------------------------------------
s = content("Application 4 · Biomedical Imaging",
            "Part 4 · Applications & Future Trends", "Tran & Fei, 2023")
card(s, 0.5, 1.45, 12.33, 1.55, accent='left', ac=NAVY)
text(s, 0.82, 1.58, 11.85, 1.35, [
    P("Why Spectral Imaging in Biomedicine?", 14, True, NAVY),
    P("Reveals physiological processes beyond RGB: metabolic processes, "
      "retinal oxygen saturation, tumours (skin / tongue / mucosa), and "
      "ischaemia (intestine & brain). Non-ionising, minimally invasive "
      "(VIS-NIR, 400–1500 nm).", 11, before=3, ls=1.16)])
card(s, 0.5, 3.15, 5.9, 1.1, accent='top', ac=TEAL)
text(s, 0.75, 3.3, 5.45, 0.85, [
    P("Compact / Ultracompact Definition", 12.5, True, TEAL),
    P("Compact: ≤ 5 kg (no external lens / cables)   ·   Ultracompact: < 500 g",
      10.5, before=3, ls=1.1)])
# application cards 1-3
apps1 = [
    ("Skin Cancer Diagnosis",
     "100% sensitivity, 85% specificity (10 bands, 63 melanoma + 183 nevi images)",
     NAVY),
    ("Wound & Burn Healing",
     "Hemoglobin concentration & oxygenation monitored over 2 weeks", TEAL),
    ("Retinal Diseases",
     "Oxygen-saturation repeatability SD = 1.4% (fundus + compact SRDA/FPI)",
     GOLD),
]
for i, (h, b, c) in enumerate(apps1):
    x = 0.5 + i * 4.16
    card(s, x, 4.45, 3.98, 2.35, accent='left', ac=c)
    text(s, x + 0.22, 4.63, 3.55, 0.4, [P(h, 12.5, True, c)])
    text(s, x + 0.22, 5.1, 3.55, 1.5, [P(b, 10.5, ls=1.18)])
text(s, 0.5, 6.95, 12.3, 0.25, [P("Tran & Fei, 2023, pp.2, 28–34", 9, True, GRAY, it=True)])

# --- 4.5 Biomedical Imaging (II) --------------------------------------------
s = content("Application 4 · Biomedical Imaging (cont.)",
            "Part 4 · Applications & Future Trends",
            "Tran & Fei, 2023 · Mukhtar et al., 2025")
apps2 = [
    ("Surgical Guidance", NAVY,
     [P("Laparoscopic HSI system", 12.5, True, NAVY),
      P("Simultaneous high-resolution video + hyperspectral imaging.", 10.5,
        before=3, ls=1.12),
      P("SNR 30–43 dB · acquisition as low as 4.6 s — overcomes motion "
        "artefacts of conventional pushbroom systems.", 10.5, before=3,
        ls=1.12),
      P("Intraoperative HSI (iHSI): wide-field, real-time, seamlessly "
        "integrated with surgical workflow.", 10.5, before=3, ls=1.12)]),
    ("Tumour Diagnosis", GOLD,
     [P("Colorectal, head & neck, breast cancers", 12.5, True, GOLD),
      P("Normal mucosa vs. adenocarcinoma differ significantly in absorbance "
        "at 525 nm; in-vivo sensitivity up to 75%.", 10.5, before=3, ls=1.12),
      P("NIR-II (1000–1700 nm) imaging significantly enhances "
        "tumour-to-background ratio, enabling deeper tissue localisation "
        "— e.g. liver cancer surgery.", 10.5, before=3, ls=1.12)]),
]
for i, (h, c, body) in enumerate(apps2):
    x = 0.5 + i * 6.28
    card(s, x, 1.5, 6.05, 4.3, accent='top', ac=c)
    text(s, x + 0.25, 1.7, 5.6, 0.4, [P(h, 15, True, c)])
    text(s, x + 0.25, 2.2, 5.55, 3.45, body)
quote_card(s, 0.5, 5.95, 12.33, 1.05, [
    "“a signal-to-noise ratio of 30–43 dB and acquisition times as low as "
    "4.6 seconds.”   —   “Their intraoperative application in liver cancer "
    "surgeries showed that NIR-II imaging significantly enhanced "
    "tumour-to-background ratio…”"], src="— Mukhtar et al., 2025; Tran & Fei, 2023")

# --- 4.5F Literature figures: retinal saturation + cancer heat maps ---------
s = content("Figures from the Literature · Oxygenation Maps & Cancer Heat Maps",
            "Part 4 · Biomedical Imaging",
            "Lu & Fei, 2014 · Tran & Fei, 2023")
pic_fit(s, os.path.join(MEDIA, "fig_retina_sat.png"),
        0.5, 1.45, 5.5, 5.0)
fcap(s, 0.5, 6.48, 5.5,
     "Fig. 4. Retinal oxygen-saturation maps of a healthy eye (a, c) with "
     "the corresponding general retinal images (b, d); vessels are "
     "separated from the background. (Lu & Fei, 2014)")
pic_fit(s, os.path.join(MEDIA, "fig_skin_cancer.png"),
        6.2, 1.45, 6.63, 3.9)
fcap(s, 6.2, 5.4, 6.63,
     "Fig. 12. (a) Compact hyperspectral Snapscan camera on a microscope; "
     "(b) synthesised-RGB pathology images and machine-learning probability "
     "heat maps of squamous head-and-neck carcinoma. (Tran & Fei, 2023)")
rect(s, 6.2, 6.24, 6.63, 0.62, BG)
text(s, 6.38, 6.3, 6.3, 0.52,
     [P("HSI cubes are converted into physiological maps (saturation) and "
        "probability maps (cancer / normal tissue).", 10, True, NAVY,
        align=PP_ALIGN.CENTER, ls=1.12)], anchor=MSO_ANCHOR.MIDDLE)

# --- 4.5F2 Literature figure: NIR image-guided surgery ----------------------
s = content("Figures from the Literature · NIR Spectral Imaging in the OR",
            "Part 4 · Biomedical Imaging · Image-Guided Surgery",
            "Mukhtar et al., 2025 (Laser & Photonics Reviews)")
pic_fit(s, os.path.join(MEDIA, "fig_biomed_surgery.png"),
        0.9, 1.45, 11.53, 4.15)
fcap(s, 0.9, 5.62, 11.53,
     "Figure 3 (I). Liver-surface examination of a liver-cancer patient with "
     "an integrated NIR-I/NIR-II and visible spectral instrument, and the "
     "resected tumours acquired during the first MS-fluorescence-guided "
     "liver-tumour surgery. (Mukhtar et al., 2025)")
rect(s, 0.9, 6.32, 11.53, 0.6, BG)
text(s, 1.15, 6.38, 11.0, 0.5,
     [P("Excitation laser + visible / NIR-I / NIR-II detectors deliver "
        "real-time wide-field guidance; resected slices are validated by "
        "pathological analysis.", 10.5, True, NAVY,
        align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE)

# --- 4.6 Industrial Sorting --------------------------------------------------
s = content("Application 5 · Industrial Sorting",
            "Part 4 · Applications & Future Trends", "Romaniello et al., 2024")
card(s, 0.5, 1.45, 6.05, 1.85, accent='left', ac=NAVY)
text(s, 0.82, 1.6, 5.65, 1.6, [
    P("Problem: Separating Gluten Contaminants from Legumes", 12.5, True, NAVY),
    P("Coeliac disease drives demand for gluten-free food. Must fully remove "
      "wheat / barley / oat from faba beans, chickpeas, and lentils — "
      "mechanical separation fails due to uneven shape & colour.", 10.2,
      before=3, ls=1.13)])
card(s, 6.78, 1.45, 6.05, 1.85, accent='left', ac=GOLD)
text(s, 7.1, 1.6, 5.65, 1.6, [
    P("Why HSI in the Food Industry?", 12.5, True, GOLD),
    P("Speed, objectivity, low cost, and non-destructive — enables analysis "
      "of the entire production batch.", 10.5, before=3, ls=1.13)])
card(s, 0.5, 3.48, 6.05, 1.75, accent='top', ac=TEAL)
text(s, 0.75, 3.65, 5.55, 1.5, [
    P("Lab HSI System & Classifier", 12.5, True, TEAL),
    P("•  VIS/NIR: 400–1000 nm · SWIR: 1000–1700 nm (InGaAs)", 10.2,
      before=3, ls=1.1),
    P("•  FS-MRMR feature selection + SVM-linear classifier", 10.2, before=2,
      ls=1.1),
    P("•  100% Correct Classification Rate (CCR) across all 6 datasets",
      10.2, True, GREEN, before=2, ls=1.1)])
card(s, 6.78, 3.48, 6.05, 1.75, accent='top', ac=RED)
text(s, 7.03, 3.65, 5.55, 1.5, [
    P("Industrial Sorter Validation", 12.5, True, RED),
    P("•  2× NIR cameras (15,000 Hz, 0.06 mm) + 2× RGB (16 M colours)",
      10.2, before=3, ls=1.1),
    P("•  Free-fall detection + compressed-air ejection of contaminants",
      10.2, before=2, ls=1.1)])
# big results
for i, (num, label, sub, c) in enumerate([
    ("FPR = 0%", "False Positive Rate", "No contaminants pass to product", RED),
    ("TPR > 99%", "True Positive Rate", "Legumes correctly identified", GREEN),
    ("FNR 0.33–0.64%", "False Negative Rate", "Minimal product waste only", GOLD),
]):
    x = 0.5 + i * 4.16
    rect(s, x, 5.4, 3.98, 1.55, WHITE, line=BORDER)
    rect(s, x, 5.4, 3.98, 0.1, c)
    text(s, x, 5.55, 3.98, 0.55, [P(num, 19, True, c, align=PP_ALIGN.CENTER)])
    text(s, x + 0.15, 6.12, 3.68, 0.35, [P(label, 11, True, NAVY,
                                              align=PP_ALIGN.CENTER)])
    text(s, x + 0.15, 6.45, 3.68, 0.4, [P(sub, 9.5, False, GRAY,
                                            align=PP_ALIGN.CENTER)])

# --- 4.6F Literature figures: lab HSI + industrial sorter -------------------
s = content("Figures from the Literature · From Lab HSI to the Optical Sorter",
            "Part 4 · Industrial Sorting",
            "Romaniello et al., 2024")
pic_fit(s, os.path.join(MEDIA, "fig_lab_hsi.png"),
        0.5, 1.5, 6.0, 4.6)
fcap(s, 0.5, 6.12, 6.0,
     "Figure 2. Pushbroom hyperspectral imaging system: (a) the VIS/NIR and "
     "SWIR sensors with 45° mirrors, (b) fibre optics and light "
     "collimators, (c) pseudo-image of the VIS/NIR camera, (d) reflectance "
     "spectra of the segmented legumes. (Romaniello et al., 2024)")
pic_fit(s, os.path.join(MEDIA, "fig_sorter.png"),
        6.75, 1.5, 6.08, 4.6)
fcap(s, 6.75, 6.12, 6.08,
     "Figure 4. The five-channel industrial hyperspectral sorter: products "
     "fall from the hopper past VIS and NIR classification stations, which "
     "trigger compressed-air ejection into separate final boxes. "
     "(Romaniello et al., 2024)")

# --- 4.7 Miniaturization (4 paradigms) --------------------------------------
s = content("Future Trend 1 · Miniaturization",
            "Part 4 · Future Trends", "Mukhtar et al., 2025")
para = [
    ("DIY", NAVY,
     "COTS camera + off-the-shelf optics + 3D printing",
     "Low-cost, customisable",
     "Large mechanical tolerance, tedious calibration"),
    ("Freeform Optics", TEAL,
     "Dispersion + aberration + focusing in one non-axisymmetric surface",
     "Wide FOV, high fidelity, meets CubeSat / UAV limits",
     "High manufacturing cost, long lead time"),
    ("Filter-on-Chip", GOLD,
     "Fabry-Pérot / photonic-crystal filters monolithically on CMOS",
     "No moving parts, true snapshot, high SWaP efficiency",
     "Difficult large-area nanofabrication"),
    ("Metasurface", RED,
     "Subwavelength meta-atoms for spectral / polarisation / computational control",
     "Ultrathin, multifunctional, video-rate HSI",
     "nm-precision fabrication across cm apertures"),
]
for i, (name, c, core, adv, lim) in enumerate(para):
    x = 0.5 + (i % 2) * 6.28
    y = 1.5 + (i // 2) * 2.45
    card(s, x, y, 6.05, 2.25, accent='left', ac=c)
    text(s, x + 0.22, y + 0.14, 5.6, 0.38, [P(name, 15, True, c)])
    text(s, x + 0.22, y + 0.56, 5.6, 0.55, [P(core, 10.2, ls=1.1)])
    text(s, x + 0.22, y + 1.18, 5.6, 0.3, [P("✓  " + adv, 10, True, GREEN)])
    text(s, x + 0.22, y + 1.5, 5.6, 0.55, [P("✗  " + lim, 10, True, RED)])
rect(s, 0.5, 6.55, 12.33, 0.45, NAVY)
text(s, 0.8, 6.62, 11.8, 0.35,
     [P("From 48 kg (1972 MSS) to < 30 g snapshot cameras — progress driven "
        "by manufacturing maturity, not new optical architectures.",
        11.5, True, WHITE, align=PP_ALIGN.CENTER)],
     anchor=MSO_ANCHOR.MIDDLE)

# --- 4.7F Literature figures: four paradigms + size timeline ----------------
s = content("Figures from the Literature · Spectrometer Paradigms & 50 Years of Shrinking",
            "Part 4 · Future Trend · Miniaturization",
            "Mukhtar et al., 2025 · Tran & Fei, 2023")
pic_fit(s, os.path.join(MEDIA, "fig_4paradigms.png"),
        0.45, 1.45, 7.5, 5.35)
fcap(s, 0.45, 6.42, 7.5,
     "Figure 15. Three decades of compact / miniaturized spectrometers: "
     "(A) dispersive optics, (B) narrowband filters, (C) Fourier-transform "
     "interferometers and (D) computational spectral reconstruction. "
     "(Mukhtar et al., 2025)")
pic_fit(s, os.path.join(MEDIA, "fig_mini_timeline.png"),
        8.15, 1.45, 4.7, 3.45)
fcap(s, 8.15, 4.92, 4.7,
     "Fig. 1. System mass vs. year of spectral imagers, from MSS-1 (1972) "
     "to Specim IQ (2018). (Tran & Fei, 2023)")
card(s, 8.15, 5.72, 4.7, 1.18, accent='left', ac=GOLD)
text(s, 8.38, 5.83, 4.3, 1.0, [
    P("The shrinking trend", 11, True, GOLD),
    P("After 2000, manufacturing advances made systems dramatically smaller "
      "— down to < 30 g snapshot cameras.", 9.5, before=2, ls=1.1)])

# --- 4.8 Real-time Processing & AI ------------------------------------------
s = content("Future Trend 2 · Real-time Processing & AI",
            "Part 4 · Future Trends", "Mukhtar et al., 2025")
rt = [
    ("Industrial Sorting", "NIR cameras at 15,000 Hz · free-fall detection",
     "Romaniello et al.", NAVY),
    ("Precision Weeding", "30 ms per frame · real-time robotic control",
     "Raja et al.", TEAL),
    ("Surgical Guidance", "Acquisition as low as 4.6 s · SNR 30–43 dB",
     "Mukhtar et al.", GOLD),
]
for i, (h, b, src, c) in enumerate(rt):
    x = 0.5 + i * 4.16
    card(s, x, 1.5, 3.98, 1.85, accent='top', ac=c)
    text(s, x + 0.2, 1.68, 3.58, 0.4, [P(h, 13.5, True, c)])
    text(s, x + 0.2, 2.15, 3.58, 0.7, [P(b, 10.5, ls=1.12)])
    text(s, x + 0.2, 2.95, 3.58, 0.3, [P(src, 9.5, True, GRAY, it=True)])
text(s, 0.5, 3.6, 12.3, 0.35,
     [P("AI & Computational Imaging Integration", 14, True, NAVY)])
ai_items = [
    ("Computational Spectral Reconstruction",
     "Compressed sensing & deep-learning demultiplexing reduce hardware "
     "burden without losing spectral resolution."),
    ("Edge Intelligence",
     "ML models embedded directly in handheld / UAV devices for on-site, "
     "real-time analysis (e.g. plant health, pollutant detection)."),
    ("Algorithm–Hardware Co-Design",
     "Physics-aware neural networks on ASICs → sub-Watt on-device spectral "
     "analytics for autonomous drones and handheld diagnostics."),
]
for i, (h, b) in enumerate(ai_items):
    y = 4.05 + i * 0.95
    card(s, 0.5, y, 12.33, 0.82, accent='left',
         ac=[TEAL, GOLD, RED][i])
    text(s, 0.85, y + 0.08, 4.5, 0.65, [P(h, 12, True, NAVY)],
         anchor=MSO_ANCHOR.MIDDLE)
    text(s, 5.45, y + 0.08, 7.2, 0.65, [P(b, 10.5, ls=1.12)],
         anchor=MSO_ANCHOR.MIDDLE)

# --- 4.9 Other Future Trends ------------------------------------------------
s = content("Future Trend 3 · Other Key Directions",
            "Part 4 · Future Trends",
            "Mukhtar et al., 2025 · Tran & Fei, 2023")
trends = [
    ("Tunable Metasurfaces",
     "Reconfigurable spectral response in real time based on task "
     "requirements, with minimal size / power increase.", NAVY),
    ("Expanded Spectral Coverage",
     "Extend from VIS-NIR to ultraviolet and mid-infrared — unlocks "
     "astronomy, chemical sensing, security.", TEAL),
    ("Low-Cost & Open-Source",
     "COTS components, 3D printing, open hardware / software; smartphones "
     "as camera + control + IoT node.", GOLD),
    ("Multimodal Fusion",
     "Combine with OCT (depth), LSCI (vasculature), Raman (chemistry), "
     "photoacoustic (up to 5 cm penetration).", RED),
    ("IoT & Edge Networks",
     "UAV swarms / field sensors process data locally, transmit only key "
     "insights for scalable environmental monitoring.", NAVY),
    ("Scalable Manufacturing",
     "Roll-to-roll nanoimprint, high-throughput DUV lithography, open "
     "calibration protocols → mass-market products.", TEAL),
]
for i, (h, b, c) in enumerate(trends):
    x = 0.5 + (i % 2) * 6.28
    y = 1.5 + (i // 2) * 1.72
    card(s, x, y, 6.05, 1.5, accent='left', ac=c)
    text(s, x + 0.28, y + 0.12, 5.6, 0.38, [P(h, 12.5, True, c)])
    text(s, x + 0.28, y + 0.55, 5.55, 0.85, [P(b, 10.2, ls=1.12)])
text(s, 0.5, 6.75, 12.3, 0.25,
     [P("Mukhtar et al., 2025, pp.51–52 · Tran & Fei, 2023, pp.35–38",
        9, True, GRAY, it=True)])

# --- 4.10 Summary ------------------------------------------------------------
s = content("Summary · Key Takeaways",
            "Part 4 · Applications & Future Trends", "All 6 papers · 2003–2025")
card(s, 0.5, 1.45, 6.05, 5.35, accent='left', ac=NAVY)
text(s, 0.82, 1.6, 5.6, 0.4, [P("Applications & Key Results", 14, True, NAVY)])
apps_sum = [
    ("Remote Sensing", "Anomaly detection, target recognition, background characterization"),
    ("Environmental Monitoring", "Drone HSI maps uranium-mine contamination at cm-scale"),
    ("Precision Agriculture", "100% accuracy, 30 ms/frame with Rh-B crop signalling"),
    ("Biomedical Imaging", "100% skin-cancer sensitivity; surgery at 4.6 s"),
    ("Industrial Sorting", "0% FPR, >99% TPR for gluten-free legume sorting"),
]
yy = 2.1
for h, b in apps_sum:
    text(s, 0.82, yy, 5.6, 0.3, [P("•  " + h, 11.5, True, TEAL)])
    text(s, 1.0, yy + 0.32, 5.4, 0.5, [P(b, 10, False, DARK, ls=1.1)])
    yy += 0.88
card(s, 6.78, 1.45, 6.05, 5.35, accent='left', ac=GOLD)
text(s, 7.1, 1.6, 5.6, 0.4, [P("Future Trends", 14, True, GOLD)])
fut_sum = [
    ("Miniaturization", "DIY / Freeform Optics / Filter-on-Chip / Metasurface — snapshot cameras (< 30 g) & on-chip integration"),
    ("Real-time Processing + AI", "Edge intelligence & algorithm–hardware co-design — sub-Watt on-device spectral analytics"),
    ("Other Directions", "Tunable metasurfaces, UV/MIR expansion, low-cost, multimodal fusion, IoT networks, scalable manufacturing"),
]
yy = 2.1
for h, b in fut_sum:
    text(s, 7.1, yy, 5.6, 0.3, [P("•  " + h, 11.5, True, GOLD)])
    text(s, 7.3, yy + 0.32, 5.4, 0.95, [P(b, 10, False, DARK, ls=1.12)])
    yy += 1.35
rect(s, 0.5, 6.92, 12.33, 0.28, BG)
text(s, 0.8, 6.95, 11.8, 0.25,
     [P("All papers: 2003–2025", 10, True, NAVY, align=PP_ALIGN.CENTER)])

# ============================================================ REFERENCES ====
refs_p1_3 = [
    ("[1]", "Garini, Y.; Young, I.T.; McNamara, G. Spectral imaging: principles "
            "and applications. Cytometry Part A, 2006, 69(8): 735–747."),
    ("[2]", "Prasad, R.D.; Sarvalkar, P.D.; Prasad, N.; et al. A review on "
            "spectroscopic techniques for analysis of nanomaterials and "
            "biomaterials. ES Energy and Environment, 2024, 27: 1264."),
    ("[3]", "Mukhtar, S.; Arbabi, A.; Viegas, J. Advances in Spectral Imaging: "
            "A Review of Techniques and Technologies. IEEE Access, 2025, 13: "
            "35848–35902. DOI: 10.1109/ACCESS.2025.3544476"),
    ("[4]", "Lu, G.; Fei, B. Medical hyperspectral imaging: a review. Journal "
            "of Biomedical Optics, 2014, 19(1): 010901. "
            "DOI: 10.1117/1.JBO.19.1.010901"),
    ("[5]", "Roussel, G.; Weber, C.; Briottet, X.; Ceamanos, X. Comparison of "
            "two atmospheric correction methods for the classification of "
            "spaceborne urban hyperspectral data depending on the spatial "
            "resolution. International Journal of Remote Sensing, 2017, "
            "39(5): 1593–1614. DOI: 10.1080/01431161.2017.1410247"),
    ("[6]", "Gautam, R.; Vanga, S.; Ariese, F.; Umapathy, S. Review of "
            "multidimensional data processing approaches for Raman and "
            "infrared spectroscopy. EPJ Techniques and Instrumentation, "
            "2015, 2: 8. DOI: 10.1140/epjti/s40485-015-0018-6"),
    ("[7]", "Yamamoto, S.; Tsuchida, S.; Urai, M.; Mizuochi, H.; Iwao, K.; "
            "Iwasaki, A. Initial Analysis of Spectral Smile Calibration of "
            "HISUI Using Atmospheric Absorption Bands. IEEE Transactions on "
            "Geoscience and Remote Sensing, 2022, 60: 5534215. "
            "DOI: 10.1109/TGRS.2022.3190486"),
]
refs_p4 = [
    ("[8]", "Shaw, G.A.; Burke, H.K. Spectral Imaging for Remote Sensing. "
            "Lincoln Laboratory Journal, 2003, 14(1)."),
    ("[9]", "Tolentino, V.; Ortega Lucero, A.; Koerting, F.; Savinova, E.; "
            "Hildebrand, J.C.; Micklethwaite, S. Drone-Based VNIR–SWIR "
            "Hyperspectral Imaging for Environmental Monitoring of a Uranium "
            "Legacy Mine Site. Drones, 2025, 9: 313."),
    ("[10]", "Raja, R.; Su, W.-H.; Slaughter, D.C.; Fennimore, S.A. "
             "Real-time precision crop identification in high weed-density "
             "environments for robotic weed control using spectral "
             "fluorescence imaging in celery. Computers and Electronics in "
             "Agriculture, 2025, 231: 110022."),
    ("[11]", "Tran, M.H.; Fei, B. Compact and ultracompact spectral imagers: "
             "technology and applications in biomedical imaging. Journal of "
             "Biomedical Optics, 2023, 28(4): 040901."),
    ("[12]", "Romaniello, R.; Barrasso, A.E.; Perone, C.; Tamborrino, A.; "
             "Berardi, A.; Leone, A. Optimisation of an Industrial Optical "
             "Sorter of Legumes for Gluten-Free Production Using Hyperspectral "
             "Imaging Techniques. Foods, 2024, 13: 404."),
    ("[13]", "Mukhtar, S.; Arbabi, A.; Viegas, J. Compact Spectral Imaging: "
             "A Review of Miniaturized and Integrated Systems. Laser & "
             "Photonics Reviews, 2025, 19: e01042."),
]
s = content("References",
            "Bibliography · 13 sources across four parts", None)

def _ref_item(s, x, w, yy, num, body, num_color, body_sz=9.3, h=0.72):
    text(s, x, yy, 0.42, 0.3, [P(num, 10, True, num_color)])
    text(s, x + 0.42, yy - 0.01, w - 0.42, h,
         [P(body, body_sz, False, DARK, ls=1.06)])

# ---- left column: Parts 1–3 (7 refs) ----
text(s, 0.5, 1.3, 6.1, 0.3,
     [P("Part 1 · Fundamentals of Spectroscopy", 11.5, True, NAVY)])
yy = 1.6
for num, body in refs_p1_3[:2]:
    _ref_item(s, 0.55, 5.85, yy, num, body, TEAL); yy += 0.62
text(s, 0.5, yy + 0.04, 6.1, 0.3,
     [P("Part 2 · Principles of Spectral Imaging", 11.5, True, NAVY)])
yy += 0.34
for num, body in refs_p1_3[2:4]:
    _ref_item(s, 0.55, 5.85, yy, num, body, TEAL); yy += 0.62
text(s, 0.5, yy + 0.04, 6.1, 0.3,
     [P("Part 3 · Data Processing & Analysis", 11.5, True, NAVY)])
yy += 0.34
for num, body in refs_p1_3[4:7]:
    _ref_item(s, 0.55, 5.85, yy, num, body, TEAL, body_sz=9.0, h=0.78)
    yy += 0.76

# ---- right column: Part 4 (6 refs) ----
text(s, 7.0, 1.3, 5.85, 0.3,
     [P("Part 4 · Applications & Future Trends", 11.5, True, NAVY)])
yy = 1.6
for num, body in refs_p4:
    rect(s, 7.0, yy - 0.03, 5.83, 0.78, BG)
    rect(s, 7.0, yy - 0.03, 0.08, 0.78, GOLD)
    text(s, 7.2, yy + 0.05, 0.55, 0.3, [P(num, 10.5, True, GOLD)])
    text(s, 7.78, yy + 0.03, 4.95, 0.72,
         [P(body, 9.0, False, DARK, ls=1.06)])
    yy += 0.82
rect(s, 0.5, 6.62, 12.33, 0.4, NAVY)
text(s, 0.8, 6.67, 11.8, 0.3,
     [P("Total: 13 references  ·  Part 1 (2) + Part 2 (2) + Part 3 (3) "
        "+ Part 4 (6)",
        11.5, True, WHITE, align=PP_ALIGN.CENTER)],
     anchor=MSO_ANCHOR.MIDDLE)

# ============================================================ THANK YOU =====
s = slide(); PAGE += 1
rect(s, 0, 0, 13.333, 7.5, NAVY)
rect(s, 0, 2.62, 13.333, 0.08, TEAL)
rect(s, 0, 4.62, 13.333, 0.04, CYAN)
text(s, 0.8, 1.6, 11.73, 1.2,
     [P("Thank You", 56, True, WHITE, align=PP_ALIGN.CENTER)])
text(s, 0.8, 2.95, 11.73, 0.6,
     [P("Questions & Discussion", 24, True, CYAN, align=PP_ALIGN.CENTER)])
text(s, 0.8, 3.95, 11.73, 0.6,
     [P("Spectroscopy and Spectral Imaging", 20, False, GOLD,
        align=PP_ALIGN.CENTER)])
text(s, 0.8, 5.1, 11.73, 0.5,
     [P("Fundamentals · Principles · Data Processing · Applications & Trends",
        14, False, LIGHT, align=PP_ALIGN.CENTER)])
text(s, 0.4, 7.05, 3.0, 0.3, [P(f"{PAGE} / {TOTAL}", 9, False, GRAY)])

# ============================================================ SAVE ==========
print(f"Total pages generated: {PAGE}")
out = r"e:\Tech_English\Spectroscopy_and_Spectral_Imaging.pptx"
prs.save(out)
print(f"Saved to: {out}")






