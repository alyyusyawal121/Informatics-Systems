import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

def preprocess_dataframe(df_raw: pd.DataFrame):
    """
    df_raw : DataFrame dari CSV user (sudah dibaca)
    return : df_processed, outlier_flags (Series "Outlier"/"Normal" per row)
    """

    df = df_raw.copy()

    # 1. Pisahkan numerik & kategorik
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()

    # 2. Imputasi
    for col in num_cols:
        df[col] = df[col].fillna(df[col].median())
    for col in cat_cols:
        df[col] = df[col].fillna(df[col].mode().iloc[0])

    # 3. Outlier detection (IQR) pada numerik
    outlier_mask = pd.Series(False, index=df.index)

    for col in num_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR

        mask_col = (df[col] < lower) | (df[col] > upper)
        outlier_mask = outlier_mask | mask_col

    outlier_flags = outlier_mask.map(lambda x: "Outlier" if x else "Normal")

    # 4. One-Hot Encoding untuk kategorik
    df_encoded = pd.get_dummies(df, columns=cat_cols, drop_first=True)

    # 5. Scaling untuk kolom numerik (setelah OHE)
    num_cols_encoded = df_encoded.select_dtypes(include=[np.number]).columns.tolist()
    scaler = StandardScaler()
    df_encoded[num_cols_encoded] = scaler.fit_transform(df_encoded[num_cols_encoded])

    return df_encoded, outlier_flags
