# -*- coding: utf-8 -*-
"""讀取 TIGPS 原始檔並建立分析用變數

build()        → 全體學生資料 D(一列一位學生,已串連家長、導師、第二波)
victims(D)     → 2023 受害者且 2024 有回答者 V(結果變數 escape = 一年後脫離受害)
perpetrators(D)→ 2023 加害者且 2024 有回答者 S(結果變數 stop = 一年後停手),含累積風險與保護因子

編碼原則:TIGPS 的負值(-6 跳答、-9 遺漏等)一律視為遺漏;
四點量表(1 從不 … 4 經常 / 1 非常不同意 … 4 非常同意)以 ≥3 視為「有」。"""
import numpy as np
import pandas as pd

from .config import find

ROLES = ['無涉入', '純受害', '純加害', '加害受害']
COPE = {'as51c9': '告訴老師', 'as51c8': '告訴家人', 'as51c7': '告訴同學朋友', 'as51c2': '要求對方停止',
        'as51c1': '好好說明澄清', 'as51c3': '忽略', 'as51c6': '回擊對抗'}
RISK5 = ['any_hit', 's_criticize', 'victim', 'addict_hi', 'friend_trouble']     # 家庭 2 + 個人 2 + 同儕 1
RISK4_NOFAMILY = ['victim', 'addict_hi', 'friend_trouble', 'cyber_perp']        # 不含家庭題(全部加害者都能算)
PROT3 = ['like_school', 'cohesion_hi', 'tclose_w1_hi']                           # 皆為 2023 年測量
TEACHER_ACTIONS = {'at50_4': 'notify', 'at50_6': 'counsel', 'at50_9': 'punish', 'at50_5': 'meeting', 'at50_7': 'separate'}


def read(key):
    return pd.read_stata(find(key), convert_categoricals=False)


def num(df, col):
    """轉成數值,負值(跳答、遺漏)設為 NaN"""
    s = pd.to_numeric(df[col], errors='coerce')
    return s.where(s >= 0)


def yes(s, lo=1, hi=4, cut=3):
    """四點量表 → 0/1(≥cut 為 1),超出範圍為 NaN"""
    return (s >= cut).astype(float).where(s.between(lo, hi))


def role(victim, perp):
    return pd.Series(np.select([(victim == 0) & (perp == 0), (victim == 1) & (perp == 0),
                                (victim == 0) & (perp == 1), (victim == 1) & (perp == 1)], ROLES, None),
                     index=victim.index).replace({None: np.nan})


def _student_w1(w1):
    d = pd.DataFrame({'id': w1.nstudent_id, 'cls': w1.school_class})
    sex = num(w1, 'as1')
    d['female'] = (sex == 1).astype(float).where(sex.isin([1, 2]))     # as1:1 女、2 男
    d['victim'] = num(w1, 'as51').map({1: 1, 2: 0})
    d['perp'] = num(w1, 'as52').map({1: 1, 2: 0})
    d['cyber_perp'] = num(w1, 'as54').map({1: 1, 2: 0})
    d['role'] = role(d.victim, d.perp)
    # 家長教養(學生回答)
    d['s_criticize'] = yes(num(w1, 'as12a'))      # 常批評指責
    d['s_hit'] = yes(num(w1, 'as12i'))            # 處罰時會打
    # 個人與同儕
    d['addict'] = pd.concat([num(w1, f'as41{c}') for c in 'abcdefghij'], axis=1).mean(axis=1)   # 網路成癮 10 題平均
    d['friend_trouble'] = yes(num(w1, 'as42b'))  # 好友會惹事生非
    # 嚴重度:8 種霸凌行為頻率(1 從未 … 4 經常 → 0 … 3)加總,至少 5 題有答
    sev = lambda pre: pd.concat([num(w1, f'{pre}{k}').map({1: 0, 2: 1, 3: 2, 4: 3}) for k in range(1, 9)],
                                axis=1).sum(axis=1, min_count=5)
    d['perp_sev'], d['vict_sev'] = sev('as52a'), sev('as51a')
    physical = pd.concat([num(w1, f'as52a{k}') >= 2 for k in (6, 7, 8)], axis=1).any(axis=1)   # 破壞、勒索、肢體
    d['physical'] = physical.astype(float)
    for v in COPE:                                                                  # 受害者因應(複選 0/1)
        d[v] = num(w1, v).where(num(w1, v).isin([0, 1]))
    # 家庭結構
    m = num(w1, 'as3'); d['divorced'] = m.isin([4, 5]).astype(float).where(m.between(1, 11))
    s = num(w1, 'as10'); d['poor'] = s.isin([1, 2]).astype(float).where(s.between(1, 4))
    # 保護因子(2023)
    d['like_school'] = yes(num(w1, 'as14a'))
    items = [num(w1, v).where(num(w1, v).between(1, 4)) for v in ['as16a', 'as16c', 'as16d', 'as16e']]
    items.append(5 - num(w1, 'as16b').where(num(w1, 'as16b').between(1, 4)))       # 反向題
    coh = pd.concat(items, axis=1).mean(axis=1)
    d['cohesion_hi'] = (coh >= coh.median()).astype(float).where(coh.notna())       # 以全體學生中位數切分
    return d


def _parent(pa):
    p = pd.DataFrame({'id': pa.nstudent_id, 'p_hit': yes(num(pa, 'ap28i'))})
    return p.drop_duplicates('id')


def _teacher(te):
    t = pd.DataFrame({'cls': te.school_class})
    for v, k in TEACHER_ACTIONS.items():
        t[k] = num(te, v)
    t['t_close'] = pd.concat([num(te, f'at48{c}') for c in 'abde'], axis=1).mean(axis=1)   # 導師自評師生親近
    return t.drop_duplicates('cls')


def _student_w2(w2):
    e = pd.DataFrame({'id': w2.nstudent_id})
    e['victim2'] = num(w2, 'bs34').map({1: 1, 2: 0})
    e['perp2'] = num(w2, 'bs36').map({1: 1, 2: 0})
    s = pd.concat([num(w2, 'bs11a'), num(w2, 'bs11b')], axis=1)
    e['teacher_close2'] = s.where((s >= 1) & (s <= 4)).mean(axis=1)
    return e


def build():
    """回傳 (D, info):D 為全體學生;info 為樣本數摘要"""
    w1, w2 = read('w1_student'), read('w2_student')
    pa, te = read('w1_parent'), read('w1_teacher')
    d, p, t, e = _student_w1(w1), _parent(pa), _teacher(te), _student_w2(w2)
    D = d.merge(p, on='id', how='left').merge(t, on='cls', how='left').merge(e, on='id', how='left')
    D['role2'] = role(D.victim2, D.perp2)
    D['cls_perp_rate'] = D.groupby('cls').perp.transform('mean')                   # 班級第一波加害率
    info = {'學生_2023': len(d), '兩波配對': int(D.role2.notna().sum()),
            '配到家長問卷': int(D.p_hit.notna().sum()),                           # 家長有回答管教題
            '配到導師問卷_班級數': int(D.loc[D.notify.notna(), 'cls'].nunique())}
    return D, info


def victims(D):
    V = D[(D.victim == 1) & D.victim2.notna()].copy()
    V['escape'] = 1 - V.victim2
    return V


def perpetrators(D):
    S = D[(D.perp == 1) & D.perp2.notna()].copy()
    S['stop'] = 1 - S.perp2
    # 家裡會打:學生或家長任一方說有;兩邊都沒回答才算遺漏
    S['any_hit'] = np.where(S.s_hit.notna() | S.p_hit.notna(), ((S.s_hit == 1) | (S.p_hit == 1)).astype(float), np.nan)
    S['addict_hi'] = (S.addict >= S.addict.median()).astype(float).where(S.addict.notna())         # 加害者內中位數
    S['tclose_hi'] = (S.teacher_close2 >= 3).astype(float).where(S.teacher_close2.notna())       # 2024 學生自評
    S['tclose_w1_hi'] = (S.t_close >= S.t_close.median()).astype(float).where(S.t_close.notna())  # 2023 導師自評
    # 累積指數:每項 0/1 加總,所有項目都有資料才計算
    S['risk5'] = S[RISK5].sum(axis=1, min_count=len(RISK5))
    S['risk4_nofamily'] = S[RISK4_NOFAMILY].sum(axis=1, min_count=len(RISK4_NOFAMILY))
    S['prot3'] = S[PROT3].sum(axis=1, min_count=len(PROT3))
    return S
