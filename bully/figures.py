# -*- coding: utf-8 -*-
"""報告的 4 張圖。輸入為 analyses 的結果 dict,只畫彙總數字"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager, ticker
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path

from .config import FIG_DIR, FONTS, INK, INK2, MUTED, GRID, SURF, RED, GREY, BLUE, ROLE_COLORS

_names = {f.name for f in font_manager.fontManager.ttflist}
plt.rcParams['font.family'] = next((f for f in FONTS if f in _names), 'sans-serif')
plt.rcParams['axes.unicode_minus'] = False
pct = ticker.FuncFormatter(lambda v, p: f'{int(v)}%')


def _save(f, name):
    FIG_DIR.mkdir(exist_ok=True)
    f.savefig(FIG_DIR / name, facecolor=SURF, bbox_inches='tight', pad_inches=0.2)
    plt.close(f)
    return FIG_DIR / name


def _style(ax, grid='x'):
    ax.set_facecolor(SURF)
    for s in ['top', 'right'] + (['left'] if grid == 'x' else []):
        ax.spines[s].set_visible(False)
    for s in ['bottom'] + (['left'] if grid == 'y' else []):
        ax.spines[s].set_color('#c3c6bf')
    ax.tick_params(colors=MUTED, labelsize=10, length=0)
    ax.grid(axis=grid, color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def dotplot(name, title, sub, res, color, xlim, h=None):
    """「有 vs 沒有」點圖。res: {標籤: compare() 的結果}"""
    h = h or 0.5 * len(res) + 1.6
    f = plt.figure(figsize=(9, h), dpi=200, facecolor=SURF)
    f.text(0.02, 0.97, title, fontsize=14, fontweight='bold', color=INK, va='top')
    f.text(0.02, 0.97 - 0.5 / h, sub, fontsize=9.5, color=MUTED, va='top')
    ax = f.add_axes([0.3, 0.1, 0.56, 0.9 - 1.1 / h]); _style(ax)
    items = list(res.items())[::-1]
    for i, (nm, r) in enumerate(items):
        c = color(r)
        ax.plot([r['有'], r['沒有']], [i, i], color='#c3c6bf', lw=2, zorder=1)
        ax.scatter(r['沒有'], i, s=60, facecolor=SURF, edgecolor=c, lw=1.8, zorder=2)
        ax.scatter(r['有'], i, s=60, color=c, zorder=3)
        ax.text(xlim[1] + 1, i, f"{r['有']:.0f}% vs {r['沒有']:.0f}%{'*' if r['p'] < .05 else ''}", va='center', fontsize=9, color=INK2)
    ax.set_yticks(range(len(items))); ax.set_yticklabels([nm for nm, _ in items], fontsize=9.8, color=INK2)
    ax.set_xlim(*xlim); ax.xaxis.set_major_formatter(pct)
    return _save(f, name)


def fig1_victim(vc):
    return dotplot('fig1_victim.png', '受害者怎麼做,一年後脫離的比例都差不多',
                   f"2023 年受害者(n={vc['n_受害者']:,})2024 年不再受害的比例。● 有這樣做 ○ 沒有;* p<0.05(控制性別、受害嚴重度、是否也加害)",
                   vc['因應'], lambda r: RED if r['p'] < .05 else GREY, xlim=(35, 75), h=3.9)


def fig2_flow(fl):
    """2023 加害者一年後的去向(流向圖 / Sankey)"""
    cnt = fl['人數']
    outs = [('無涉入', '完全停手'), ('純受害', '停手,但被欺負'), ('純加害', '繼續霸凌別人'), ('加害受害', '繼續霸凌,也被欺負')]
    srcs = [('純加害', '2023 純加害'), ('加害受害', '2023 加害受害')]
    f = plt.figure(figsize=(9.4, 3.3), dpi=200, facecolor=SURF)
    f.text(0.02, 0.97, '加害受害者最難停手:三分之一一年後仍在霸凌、也被欺負', fontsize=14, fontweight='bold', color=INK, va='top')
    f.text(0.02, 0.89, '2023 年霸凌他人的學生,2024 年的去向;帶子寬度代表人數', fontsize=9.5, color=MUTED, va='top')
    ax = f.add_axes([0.02, 0.02, 0.96, 0.82]); ax.set_xlim(0, 10); ax.set_ylim(0, 1); ax.axis('off')
    N = sum(sum(r.values()) for r in cnt.values()); gap = 0.035; scale = (1 - gap * 3) / N
    xl, xr, w = 2.3, 7.1, 0.25
    ly, y = {}, 0.98                                   # 左邊節點(2023)
    for s, lab in srcs:
        tot = sum(cnt[s].values()); hh = tot * scale
        ax.add_patch(Rectangle((xl - w, y - hh), w, hh, color='#6b7280'))
        ax.text(xl - w - 0.1, y - hh / 2, f"{lab}\n{tot} 人\n一年後停手 {fl[s]['停手%']:.0f}%", ha='right', va='center', fontsize=9.5, color=INK2)
        ly[s] = y; y -= hh + gap * 1.5
    ry, y = {}, 0.98                                   # 右邊節點(2024)
    for r, lab in outs:
        tot = sum(cnt[s][r] for s, _ in srcs); hh = tot * scale
        ax.add_patch(Rectangle((xr, y - hh), w, hh, color=ROLE_COLORS[r]))
        ax.text(xr + w + 0.1, y - hh / 2, f'{lab}\n{tot} 人', ha='left', va='center', fontsize=9.5, color=INK2)
        ry[r] = y; y -= hh + gap
    xm = (xl + xr) / 2                                 # 流向帶:三次貝茲曲線
    for s, _ in srcs:
        tot_s = sum(cnt[s].values())
        for r, _ in outs:
            c = cnt[s][r]; hh = c * scale
            y0t, y1t = ly[s], ry[r]; y0b, y1b = y0t - hh, y1t - hh
            verts = [(xl, y0t), (xm, y0t), (xm, y1t), (xr, y1t), (xr, y1b), (xm, y1b), (xm, y0b), (xl, y0b), (xl, y0t)]
            codes = [Path.MOVETO] + [Path.CURVE4] * 3 + [Path.LINETO] + [Path.CURVE4] * 3 + [Path.CLOSEPOLY]
            ax.add_patch(PathPatch(Path(verts, codes), facecolor=ROLE_COLORS[r], alpha=0.45, lw=0))
            if hh >= 0.05:                             # 太細的帶子不標,避免文字重疊
                ax.text(xl + 0.15, y0t - hh / 2, f'{c / tot_s * 100:.0f}%', va='center', fontsize=8.5, color=INK)
            ly[s] -= hh; ry[r] -= hh
    return _save(f, 'fig2_flow.png')


def fig3_cumulative(cu):
    """左:累積風險項數;右:累積保護因子項數"""
    f = plt.figure(figsize=(9.4, 4.1), dpi=200, facecolor=SURF)
    f.text(0.02, 0.97, '風險會疊加:每多一項,加害者停手的機會就少一截', fontsize=14, fontweight='bold', color=INK, va='top')
    f.text(0.02, 0.89, '2023 年加害者 2024 年停止霸凌他人的比例(%),依 2023 年擁有的風險 / 保護因子項數', fontsize=9.5, color=MUTED, va='top')
    panels = [([0.07, 0.13, 0.52, 0.6], cu['risk5'], RED, ['0', '1', '2', '3', '4+'], '風險項數',
               f"風險:家裡會打、常被批評、同時被欺負、網路成癮偏高、好友會惹事(n={cu['risk5']['N']:,})", 1.8),
              ([0.68, 0.13, 0.29, 0.6], cu['prot3'], BLUE, ['0', '1', '2', '3'], '保護因子項數',
               f"保護:喜歡學校、班級凝聚力高、導師自評師生親近(n={cu['prot3']['N']:,})", 2)]
    for box, d, col, ticks, xlabel, title, dy in panels:
        ax = f.add_axes(box); _style(ax, grid='y'); ax.yaxis.set_major_formatter(pct); ax.set_ylim(30, 90)
        ax.plot(d['k'], d['rate'], color=col, lw=2, marker='o', ms=7, mec=SURF, mew=1.5)
        for k, v in zip(d['k'], d['rate']):
            ax.text(k, v + dy, f'{v:.0f}%', fontsize=8.5, color=col, ha='center')
        ax.set_xticks(range(len(ticks))); ax.set_xticklabels(ticks, fontsize=10, color=INK2)
        ax.set_xlabel(xlabel, fontsize=9.5, color=MUTED); ax.set_title(title, fontsize=8.3, color=INK2, loc='left')
    return _save(f, 'fig3_cumulative.png')


def fig4_nohelp(nd):
    rows = {k: v for k, v in nd.items() if k.startswith(('父母', '家境', '導師'))}
    return dotplot('fig4_nohelp.png', '以為有用,其實看不出差別',
                   '2023 年加害者 2024 年停止霸凌他人的比例。● 有該情形 ○ 沒有(控制性別、加害嚴重度、是否同時受害、班級加害率)',
                   rows, lambda r: GREY, xlim=(40, 85))
