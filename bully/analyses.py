# -*- coding: utf-8 -*-
"""報告第 3 節的各項分析。每個函式回傳一個 dict,由 run_all.py 彙整成 results/report_numbers.json"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from .data import COPE, ROLES, RISK5
from .models import logit, odds_ratio, compare, ladder

# 控制變項
VICTIM_BASE = 'escape ~ female + vict_sev + perp'                        # 受害者:性別、受害嚴重度、是否也加害
PERP_BASE = 'stop ~ female + perp_sev + cls_perp_rate'                   # 加害者:性別、加害嚴重度、班級加害率
PERP_BASE_V = PERP_BASE + ' + victim'                                    # 再加上是否同時受害


def victim_coping(V):
    """3.1 受害者的 7 種因應方式與一年後脫離受害"""
    out = {'n_受害者': len(V), '脫離率': round(float(V.escape.mean()) * 100, 1),
           'n_有回答因應題': int(V['as51c9'].notna().sum())}
    out['因應'] = {name: compare(V, v, 'escape', VICTIM_BASE) for v, name in COPE.items()}
    return out


def flow(D):
    """3.2 2023 加害者 → 2024 角色的人數(流向圖)"""
    S = D[(D.perp == 1) & D.role2.notna()]
    cnt = {s: {r: int(((S.role == s) & (S.role2 == r)).sum()) for r in ROLES} for s in ['純加害', '加害受害']}
    out = {'人數': cnt}
    for s, row in cnt.items():
        tot = sum(row.values())
        out[s] = {'n': tot, '停手%': round((row['無涉入'] + row['純受害']) / tot * 100, 1),
                  '完全停手%': round(row['無涉入'] / tot * 100, 1), '持續加害受害%': round(row['加害受害'] / tot * 100, 1)}
    return out


def individual_factors(S):
    """3.3 個別風險因素與停手(同時受害一列不能再控制 victim)"""
    rows = {'家裡會打(學生或家長說)': 'any_hit', '家長常批評指責': 's_criticize', '同時也被欺負': 'victim',
            '也在網路上霸凌': 'cyber_perp', '網路成癮偏高': 'addict_hi', '跟導師親近(2024 學生自評)': 'tclose_hi'}
    out = {'n_加害者': len(S), '停手率': round(float(S.stop.mean()) * 100, 1)}
    for name, v in rows.items():
        out[name] = compare(S, v, 'stop', PERP_BASE if v == 'victim' else PERP_BASE_V)
    return out


def hit_by_role(D):
    """3.3 「家長處罰時會打」(學生說)在四種角色的比例"""
    x = D.dropna(subset=['s_hit', 'role'])
    out = {r: round(float(x.loc[x.role == r, 's_hit'].mean()) * 100, 1) for r in ROLES}
    out['n_全部'] = len(x)
    out['n_無涉入+加害受害'] = int(x.role.isin(['無涉入', '加害受害']).sum())     # 報告比較的兩組
    return out


def cumulative(S):
    """3.3 累積風險與累積保護因子"""
    out = {}
    for var, cap in [('risk5', 4), ('risk4_nofamily', 4), ('prot3', 3)]:
        m, used = logit(f'{PERP_BASE} + {var}', S)
        out[var] = {**ladder(S, var, 'stop', cap), '每多一項': odds_ratio(m, var), 'n_模型': len(used)}
    # 合成一個指數 vs 五個因素分開放入(同一批樣本比較 AIC)
    x = S.dropna(subset=RISK5 + ['female', 'perp_sev', 'cls_perp_rate'])
    m_sep, _ = logit(f'{PERP_BASE} + ' + ' + '.join(RISK5), x)
    m_idx, _ = logit(f'{PERP_BASE} + risk5', x)
    out['AIC'] = {'n': len(x), '指數': round(float(m_idx.aic), 1), '分開': round(float(m_sep.aic), 1)}
    return out


def no_difference(S):
    """3.4 以為有用、其實看不出差別的因素"""
    rows = {'父母離婚': 'divorced', '家境不富裕': 'poor', '導師:通知父母': 'notify', '導師:請輔導老師協助': 'counsel',
            '導師:處罰學生': 'punish', '導師:召開學生家長會議': 'meeting', '導師:隔開雙方': 'separate'}
    out = {name: compare(S, v, 'stop', PERP_BASE_V) for name, v in rows.items()}
    out['n_有導師資料'] = int(S.notify.notna().sum())
    out['肢體或財物霸凌'] = compare(S, 'physical', 'stop', PERP_BASE_V)
    return out


def _effect(d):
    m = smf.logit(f'{PERP_BASE} + risk5', data=d).fit(disp=0)
    base = m.predict(d).mean()
    a = d.copy(); a['risk5'] = (a.risk5 - 1).clip(lower=0)                              # 情境一:每位有風險的加害者少一項
    b = d.copy(); b['risk5'] = np.where(b.risk5 >= 3, b.risk5 - 1, b.risk5)             # 情境二:只優先輔導風險 3 項以上者,各少一項
    return {'基準停手率': base * 100, '人人少一項': (m.predict(a).mean() - base) * 100,
            '高風險(3項以上)少一項': (m.predict(b).mean() - base) * 100, '高風險者占比': (d.risk5 >= 3).mean() * 100}


def expected_effect(S, n_boot=1000, seed=2026):
    """4 預期成效(情境推算):若輔導讓加害者的風險少一項,停手比例預期增加多少個百分點。
    用 3.3 的累積風險模型預測;信賴區間以班級為單位重抽(群聚拔靴法)。假設風險能被減少,不是因果保證"""
    x = S.dropna(subset=RISK5 + ['female', 'perp_sev', 'cls_perp_rate', 'stop', 'risk5', 'cls']).copy()
    est = _effect(x)
    rng = np.random.default_rng(seed); groups = {c: g for c, g in x.groupby('cls')}; cls = list(groups)
    B = pd.DataFrame([_effect(pd.concat([groups[c] for c in rng.choice(cls, len(cls))], ignore_index=True)) for _ in range(n_boot)])
    return {'n': len(x), **{k: [round(float(v), 1), round(float(B[k].quantile(.025)), 1), round(float(B[k].quantile(.975)), 1)] for k, v in est.items()}}
