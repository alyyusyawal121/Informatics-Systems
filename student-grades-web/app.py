from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import (
    LoginManager, login_user, login_required,
    current_user, logout_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pandas as pd
import numpy as np

from models import db, User, UploadedFile, DataRaw, DataPreprocessed
from preprocessing import preprocess_dataframe

MAX_DATASETS = 3


# =====================================================
# APP INITIALIZATION
# =====================================================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


# =====================================================
# LOGIN MANAGER SETUP
# =====================================================
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# =====================================================
# CREATE DATABASE (RUN ONCE AUTOMATICALLY)
# =====================================================
with app.app_context():
    db.create_all()


# =====================================================
# DELETE OLD DATASETS (keep only last MAX_DATASETS)
# =====================================================
def delete_old_datasets_if_needed(user_id):
    files = (
        UploadedFile.query
        .filter_by(user_id=user_id)
        .order_by(UploadedFile.upload_time.asc())
        .all()
    )
    if len(files) > MAX_DATASETS:
        excess = len(files) - MAX_DATASETS
        for i in range(excess):
            db.session.delete(files[i])
        db.session.commit()


# =====================================================
# REGISTER
# =====================================================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        if User.query.filter_by(email=email).first():
            flash("Email sudah terdaftar!", "danger")
            return redirect(url_for("register"))

        hashed_pw = generate_password_hash(password)
        new_user = User(name=name, email=email, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        flash("Registrasi berhasil, silakan login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# =====================================================
# LOGIN
# =====================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            flash("Email atau password salah!", "danger")

    return render_template("login.html")


# =====================================================
# LOGOUT
# =====================================================
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# =====================================================
# DASHBOARD (GRAFIK)
# =====================================================
@app.route("/")
@login_required
def dashboard():
    # semua file milik user
    user_files = (
        UploadedFile.query
        .filter_by(user_id=current_user.id)
        .order_by(UploadedFile.upload_time.desc())
        .all()
    )

    if not user_files:
        return render_template("dashboard.html", no_data=True)

    # pilih dataset (default: terbaru)
    selected_file_id = request.args.get("file_id", type=int)
    if selected_file_id:
        selected_file = UploadedFile.query.filter_by(
            id=selected_file_id, user_id=current_user.id
        ).first() or user_files[0]
    else:
        selected_file = user_files[0]

    # ambil raw & preprocessed
    raw_rows = DataRaw.query.filter_by(file_id=selected_file.id).all()
    pre_rows = (
        DataPreprocessed.query
        .join(DataRaw, DataPreprocessed.raw_id == DataRaw.id)
        .filter(DataRaw.file_id == selected_file.id)
        .all()
    )

    df_raw = pd.DataFrame([r.row_json for r in raw_rows]) if raw_rows else pd.DataFrame()
    df_pre = pd.DataFrame([p.row_json for p in pre_rows]) if pre_rows else pd.DataFrame()
    outlier_flags = [p.any_outlier for p in pre_rows]

    # --- METRIK DASAR ---
    total_rows = len(df_raw)
    total_cols = len(df_raw.columns)
    missing_total = int(df_raw.isna().sum().sum()) if not df_raw.empty else 0
    outlier_count = outlier_flags.count("Outlier")

    chart_data = {}


    # --- NUMERIC FEATURES (untuk histogram & korelasi) ---
    if not df_pre.empty:
        numeric_cols = df_pre.select_dtypes(include=[np.number]).columns.tolist()
    else:
        numeric_cols = []

    # =========== HISTOGRAM ===========
    # =========================================================
    # HISTOGRAM (RAW & SCALED)
    # =========================================================
    if not df_pre.empty:
        numeric_cols = df_pre.select_dtypes(include=[np.number]).columns.tolist()
    else:
        numeric_cols = []

    # ambil pilihan fitur histogram dari dropdown
    hist_col = request.args.get("hist_col")
    hist_mode = request.args.get("hist_mode", "raw")  # default raw

    if hist_col not in numeric_cols:
        # kalau user belum memilih fitur → pakai pertama
        hist_col = numeric_cols[0] if numeric_cols else None

    chart_data["hist_col"] = hist_col
    chart_data["hist_choices"] = numeric_cols
    chart_data["hist_mode"] = hist_mode

    # RAW HISTOGRAM
    if hist_col and hist_mode == "raw":
        if hist_col in df_raw.columns:
            chart_data["hist_values"] = df_raw[hist_col].dropna().tolist()
        else:
            # kalau fitur baru hasil OHE / scaling → tidak ada di raw
            chart_data["hist_values"] = []
    # SCALED HISTOGRAM
    elif hist_col and hist_mode == "scaled":
        chart_data["hist_values"] = df_pre[hist_col].dropna().tolist()
    else:
        chart_data["hist_values"] = []


    # =========== CORRELATION (DROPDOWN) ===========
    if len(numeric_cols) >= 2:

        # ambil target fitur dari dropdown
        corr_target = request.args.get("corr_target")

        # jika tidak ada → pakai fitur numerik pertama
        if corr_target not in numeric_cols:
            corr_target = numeric_cols[0]

        corr = df_pre[numeric_cols].corr()
        corr_to_target = corr[corr_target].drop(labels=[corr_target])

        chart_data["corr_target"] = corr_target
        chart_data["corr_choices"] = numeric_cols
        chart_data["corr_labels"] = corr_to_target.index.tolist()
        chart_data["corr_values"] = corr_to_target.values.tolist()

    else:
        chart_data["corr_target"] = None
        chart_data["corr_choices"] = None
        chart_data["corr_labels"] = None
        chart_data["corr_values"] = None

    # --- CATEGORICAL FEATURES (untuk bar chart kategori) ---
    if not df_raw.empty:
        cat_cols = df_raw.select_dtypes(exclude=[np.number]).columns.tolist()
    else:
        cat_cols = []

    if cat_cols:
        col_cat = cat_cols[0]
        counts = df_raw[col_cat].value_counts().sort_values(ascending=False)
        max_cats = 8

        chart_data["cat_column"] = col_cat
        chart_data["cat_labels"] = counts.index[:max_cats].tolist()
        chart_data["cat_counts"] = counts.values[:max_cats].tolist()
    else:
        chart_data["cat_column"] = None
        chart_data["cat_labels"] = None
        chart_data["cat_counts"] = None

    # --- Outlier summary ---
    chart_data["outlier_counts"] = {
        "Normal": outlier_flags.count("Normal"),
        "Outlier": outlier_flags.count("Outlier")
    }

    return render_template(
        "dashboard.html",
        no_data=False,
        user_files=user_files,
        selected_file_id=selected_file.id,
        total_rows=total_rows,
        total_cols=total_cols,
        missing_total=missing_total,
        outlier_count=outlier_count,
        chart_data=chart_data
    )


# =====================================================
# RAW DATA TABLE
# =====================================================
@app.route("/data-raw/<int:file_id>")
@login_required
def data_raw_view(file_id):
    file = UploadedFile.query.filter_by(id=file_id, user_id=current_user.id).first()
    if not file:
        flash("Dataset tidak ditemukan atau bukan milik Anda.", "danger")
        return redirect(url_for("dashboard"))

    raw_rows = DataRaw.query.filter_by(file_id=file_id).all()
    df_raw = pd.DataFrame([r.row_json for r in raw_rows]) if raw_rows else None

    return render_template("table_raw.html", file=file, df_raw=df_raw)


# =====================================================
# PREPROCESSED DATA TABLE
# =====================================================
@app.route("/data-preprocessed/<int:file_id>")
@login_required
def data_preprocessed_view(file_id):
    file = UploadedFile.query.filter_by(id=file_id, user_id=current_user.id).first()
    if not file:
        flash("Dataset tidak ditemukan atau bukan milik Anda.", "danger")
        return redirect(url_for("dashboard"))

    pre_rows = (
        DataPreprocessed.query
        .join(DataRaw, DataPreprocessed.raw_id == DataRaw.id)
        .filter(DataRaw.file_id == file_id)
        .all()
    )

    if not pre_rows:
        df_pre = None
    else:
        df_pre = pd.DataFrame([p.row_json for p in pre_rows])
        df_pre["Outlier"] = [p.any_outlier for p in pre_rows]

    return render_template("table_pre.html", file=file, df_pre=df_pre)


# =====================================================
# UPLOAD CSV
# =====================================================
@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            flash("Tidak ada file yang diupload.", "danger")
            return redirect(url_for("upload"))

        try:
            df_raw = pd.read_csv(file)
        except Exception as e:
            flash(f"Gagal membaca CSV: {e}", "danger")
            return redirect(url_for("upload"))

        if df_raw.empty:
            flash("File CSV kosong.", "warning")
            return redirect(url_for("upload"))

        uploaded = UploadedFile(
            user_id=current_user.id,
            filename=file.filename,
            upload_time=datetime.utcnow()
        )
        db.session.add(uploaded)
        db.session.commit()

        df_processed, outlier_flags = preprocess_dataframe(df_raw)

        for idx, row in df_raw.iterrows():
            raw_row = DataRaw(
                file_id=uploaded.id,
                row_json=row.to_dict()
            )
            db.session.add(raw_row)
            db.session.flush()

            processed_row = DataPreprocessed(
                raw_id=raw_row.id,
                row_json=df_processed.iloc[idx].to_dict(),
                any_outlier=outlier_flags.iloc[idx],
            )
            db.session.add(processed_row)

        db.session.commit()

        delete_old_datasets_if_needed(current_user.id)

        flash("Dataset berhasil diupload dan dipreprocess.", "success")
        return redirect(url_for("dashboard"))

    return render_template("upload.html")


# =====================================================
# RUN APP
# =====================================================
if __name__ == "__main__":
    app.run(debug=True)
