\# 360 度績效互評系統（360-Degree Performance Review System）



本專案為360 度績效互評系統，  

以教學與研究為導向，示範如何透過 \*\*多角色評分機制\*\* 整合個人、自我、同儕與教師（或主管）之評估結果，  

並以結構化指標進行資料彙整與分析。



系統採用 \*\*FastAPI 後端 + 純前端（HTML / CSS / JavaScript）\*\* 架構，  

適用於課堂實作、制度設計示範與系統分析練習。



---



\## 系統目的

本系統旨在：


\- 示範 360 度績效評估制度之實作方式

\- 練習多角色評分資料的整合與權重設計

\- 建立可擴充之前後端分離架構

\- 作為課堂專題或研究型系統原型


---


\## 績效評估指標（六大構面）

系統採用六項績效構面作為評估基準：
工作態度、工作績效、紀律規範、專業能力、學習成長、溝通協作

---

\## 評分角色與機制

系統支援多角色評分，包含：

\- 教師／主管評分（Teacher）

\- 自我評分（Self）

\- 同儕評分（Peer）


\### 同儕評分設計

\- 每位使用者固定評分 2 位同儕

\- 系統設計保留彈性，可擴充評分人數


\### 權重設計

\- 教師評分：40%

\- 自我評分：20%

\- 同儕評分：40%（平均分配）

---

\## 系統架構概述


\- 前端：純靜態頁面（HTML / CSS / JavaScript）

\- 後端：FastAPI

\- 資料來源：CSV


系統採前後端分離設計，便於後續擴充為資料庫版本（SQLite等）。

---
\## 專案結構

```text

PA360/

├── backend/

│   ├── app/

│   │   ├── api/              # API 路由

│   │   ├── schemas/          # Pydantic 資料模型

│   │   ├── services/         # 評分與分派邏輯

│   │   ├── data/             # 範例資料（CSV / JSON）

│   │   ├── db.py

│   │   ├── deps.py

│   │   └── main.py           # FastAPI 啟動點

│   ├── requirements.txt

│   └── .venv/                # 虛擬環境（未納入版本控制）

│

├── frontend/

│   ├── login.html

│   ├── student/              # 學生介面（自評 / 同儕評分）

│   ├── teacher/              # 教師評分介面

│   ├── master/               # 管理與總覽頁面

│   └── assets/

│

├── .gitignore

└── README.md

 環境需求

Python 3.9 以上

 安裝與執行方式

1 建立虛擬環境


複製程式碼

cd backend

python -m venv .venv

啟動虛擬環境（Windows）：



bash

複製程式碼

.\\.venv\\Scripts\\activate

2 安裝套件

bash

複製程式碼

pip install -r requirements.txt

3 啟動後端服務

bash

複製程式碼

uvicorn app.main:app --reload

API 位置：http://127.0.0.1:8000



API 文件：http://127.0.0.1:8000/docs



 前端操作方式

前端為靜態頁面，可透過任一 HTTP Server 開啟：



登入頁：frontend/login.html



學生功能：自評、同儕評分



教師功能：績效評分



管理者功能：績效總覽與分析



注意事項

本系統為教學與研究用途原型



範例資料僅供示範，不涉及真實人事資料



未包含正式資安與權限控管機制



專案性質說明

本專案屬於 課堂專題／研究型系統原型（Prototype），

重點在於制度設計、系統架構與資料流程示範，而非商業系統。



授權聲明

本專案僅供學術研究與課堂教學使用。

