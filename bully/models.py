# -*- coding: utf-8 -*-
"""統計模型:邏輯斯迴歸(班級群聚標準誤)與常用的整理函式"""
import re

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


def logit(formula, df, cluster='cls'):
    """先依公式用到的變數刪除遺漏值,再估計 logit,標準誤依班級群聚校正。
    回傳 (模型, 實際使用的資料)"""
    cols = [c for c in set(re.findall(r'[A-Za-z_][A-Za-z0-9_]*', formula)) if c in df.columns]
    x = df.dropna(subset=cols)
    groups = pd.factorize(x[cluster])[0]
    m = smf.logit(formula, data=x).fit(disp=0, cov_type='cluster', cov_kwds={'groups': groups})
    return m, x


def odds_ratio(m, var):
    """勝算比 exp(β)、95% 信賴區間與 p 值"""
    lo, hi = m.conf_int().loc[var]
    return {'OR': round(float(np.exp(m.params[var])), 2), 'CI': [round(float(np.exp(lo)), 2), round(float(np.exp(hi)), 2)],
            'p': round(float(m.pvalues[var]), 3)}


def compare(df, var, outcome, formula_base):
    """「有 / 沒有」某特徵者的結果比例,加上控制變項後的勝算比"""
    x = df.dropna(subset=[var])
    m, used = logit(f'{formula_base} + {var}', df)
    return {'有': round(float(x.loc[x[var] == 1, outcome].mean() * 100), 1),
            '沒有': round(float(x.loc[x[var] == 0, outcome].mean() * 100), 1),
            'n有': int((x[var] == 1).sum()), 'n沒有': int((x[var] == 0).sum()),
            'n_模型': len(used), **odds_ratio(m, var)}


def ladder(df, var, outcome, cap):
    """累積指數的階梯:各項數的結果比例(cap 以上合併)"""
    x = df.dropna(subset=[var]).copy()
    x['k'] = x[var].clip(upper=cap)
    g = x.groupby('k')[outcome].agg(['mean', 'size'])
    return {'k': [int(k) for k in g.index], 'rate': [round(float(v) * 100, 1) for v in g['mean']],
            'n': [int(v) for v in g['size']], 'N': len(x)}
