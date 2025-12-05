# 🧠 Educational Informatics — Student Data Preprocessing & Dashboard System

Sistem berbasis web ini dikembangkan menggunakan **Flask**, **SQLAlchemy**, dan **Chart.js**  
untuk melakukan **upload dataset**, **preprocessing otomatis**, serta **visualisasi dashboard interaktif**.

Proyek ini dibuat sebagai bagian dari tugas besar pada mata kuliah *Educational Informatics*.

---

## 🚀 Fitur Utama

### 🔐 1. Autentikasi Pengguna
- Register & Login (Flask-Login)
- Setiap user memiliki data sendiri (data terisolasi per user)
- Session management otomatis

---

### 📤 2. Upload Dataset (CSV)
User dapat mengupload dataset dalam format **.csv**, lalu sistem akan:

- Membaca data menggunakan Pandas
- Menyimpan data mentah (raw) ke database
- Melakukan preprocessing otomatis
- Menyimpan hasil preprocessing per baris ke database

Setiap user hanya dapat menyimpan **maksimal 3 dataset**  
→ dataset lama akan otomatis dihapus (FIFO).

---

### 🛠️ 3. Preprocessing Otomatis
Preprocessing dilakukan melalui `preprocessing.py`, termasuk:

- Imputasi:
  - Numerik → Median
  - Kategorik → Mode
- One-Hot Encoding (OHE)
- StandardScaler pada fitur numerik
- Deteksi Outlier menggunakan metode **IQR**
- Output:
  - Data mentah (raw)
  - Data terproses (preprocessed)
  - Label outlier per baris

---

### 📊 4. Dashboard Analitik Interaktif
Dashboard menampilkan berbagai visualisasi:

#### 🔹 Histogram (dengan dropdown)
- Pilih fitur numerik
- Mode tampilan:
  - Raw (nilai asli)
  - Scaled (hasil StandardScaler)
- Bin otomatis (Freedman–Diaconis rule)

#### 🔹 Distribusi Outlier
- Bar chart jumlah data Normal vs Outlier

#### 🔹 Distribusi Kategorik
- Menampilkan distribusi nilai kolom kategorik pertama dalam dataset

#### 🔹 Korelasi Antar Fitur (Dropdown)
- User memilih fitur acuan untuk melihat korelasi dengan fitur numerik lainnya
- Visualisasi correlation bar chart
- Warna:
  - Biru → korelasi positif
  - Merah → korelasi negatif

---

### 📄 5. Tabel Data
User dapat melihat:

- **Raw Data Table** — data asli dari CSV
- **Preprocessed Data Table** — hasil preprocessing
- Outlier ditampilkan sebagai kolom tambahan

---
## ▶️ Cara Menjalankan Project

Clone Repository
```bash
git clone https://github.com/alyyusyawal121/Informatics-Systems.git
cd project-folder

python -m venv venv
source venv/bin/activate    # Mac/Linux
venv\Scripts\activate       # Windows

pip install -r requirements.txt

python app.py


