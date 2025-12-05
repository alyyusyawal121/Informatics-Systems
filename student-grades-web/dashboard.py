@app.route("/")
@login_required
def dashboard():
    # ambil semua file milik user
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

    # Histogram: pakai kolom numerik pertama (kalau ada)
    if numeric_cols:
        col_hist = numeric_cols[0]
        chart_data["hist_column"] = col_hist
        chart_data["hist_values"] = df_pre[col_hist].tolist()
    else:
        chart_data["hist_column"] = None
        chart_data["hist_values"] = None

    # Correlation heatmap: butuh minimal 2 kolom numerik
    if len(numeric_cols) >= 2:
        corr = df_pre[numeric_cols].corr()
        chart_data["corr_labels"] = numeric_cols
        chart_data["corr_matrix"] = corr.values.tolist()
    else:
        chart_data["corr_labels"] = []
        chart_data["corr_matrix"] = None

    # --- CATEGORICAL FEATURES (untuk bar chart kategori) ---
    if not df_raw.empty:
        cat_cols = df_raw.select_dtypes(exclude=[np.number]).columns.tolist()
    else:
        cat_cols = []

    if cat_cols:
        # pilih 1 kolom kategori pertama
        col_cat = cat_cols[0]
        counts = df_raw[col_cat].value_counts().sort_values(ascending=False)
        max_cats = 8  # biar tidak terlalu banyak batang

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
