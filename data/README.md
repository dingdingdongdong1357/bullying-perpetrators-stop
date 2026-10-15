# data/:放 TIGPS 原始資料

TIGPS 資料依釋出單位的使用規範,**不隨本專案公開**。請自行依 TIGPS 資料釋出規定申請,取得後放入本資料夾。

需要 4 個檔案(檔名需相同,放在 `data/` 底下任何子資料夾都可以,程式會自動尋找):

| 檔案 | 內容 |
|---|---|
| `TIGPSw1_s.dta` | 第一波(2023)學生問卷 |
| `TIGPSw1_p.dta` | 第一波(2023)照顧者問卷 |
| `TIGPSw1_t.dta` | 第一波(2023)導師問卷 |
| `TIGPSw2_s.dta` | 第二波(2024)學生問卷 |

例如:

```
data/
├─ 青少年2023/01_學生/TIGPSw1_s.dta
├─ 青少年2023/02_照顧者/TIGPSw1_p.dta
├─ 青少年2023/04_導師/TIGPSw1_t.dta
└─ 青少年第二波2024/TIGPSw2_s.dta
```

資料放在別處時,也可以用環境變數指定:`TIGPS_DIR=/path/to/tigps python run_all.py`。

資料來源:中央研究院社會學研究所,臺灣數位世代青少年成長歷程追蹤研究(Taiwan Integrated Growth Panel Study, TIGPS)2023、2024 年學生、照顧者與導師問卷。
