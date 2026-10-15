# -*- coding: utf-8 -*-
"""一鍵重現報告所有數字與圖表
    python run_all.py
輸出:results/report_numbers.json(報告第 3 節所有數字)、results/summary.txt、figures/*.png"""
import json

from bully import analyses as A, figures as F
from bully.config import RESULTS_DIR
from bully.data import build, victims, perpetrators


def main():
    D, info = build()
    V, S = victims(D), perpetrators(D)
    R = {'樣本': info,
         '3.1 受害者因應': A.victim_coping(V),
         '3.2 加害者去向': A.flow(D),
         '3.3 個別因素': A.individual_factors(S),
         '3.3 會打比例(依角色)': A.hit_by_role(D),
         '3.3 累積指數': A.cumulative(S),
         '3.4 看不出差別': A.no_difference(S)}
    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / 'report_numbers.json').write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding='utf-8')
    for fig in [F.fig1_victim(R['3.1 受害者因應']), F.fig2_flow(R['3.2 加害者去向']),
                F.fig3_cumulative(R['3.3 累積指數']), F.fig4_nohelp(R['3.4 看不出差別'])]:
        print('圖:', fig.name)
    lines = [summary_line(k, v) for k, v in R.items()]
    (RESULTS_DIR / 'summary.txt').write_text('\n\n'.join(lines), encoding='utf-8')
    print('\n\n'.join(lines))


def summary_line(title, d):
    return f'== {title} ==\n' + json.dumps(d, ensure_ascii=False)


if __name__ == '__main__':
    main()
