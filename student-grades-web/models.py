from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# =====================================================
# USERS TABLE
# =====================================================
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # RELATIONSHIP BENAR
    files = db.relationship("UploadedFile", backref="user", lazy=True)


# =====================================================
# UPLOADED FILES
# =====================================================
class UploadedFile(db.Model):
    __tablename__ = "uploaded_files"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    filename = db.Column(db.String(200), nullable=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)

    raw_rows = db.relationship(
        "DataRaw",
        backref="file",
        lazy=True,
        cascade="all, delete-orphan"
    )


# =====================================================
# RAW DATA
# =====================================================
class DataRaw(db.Model):
    __tablename__ = "data_raw"

    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey("uploaded_files.id"), nullable=False)

    row_json = db.Column(db.JSON, nullable=False)

    preprocessed = db.relationship(
        "DataPreprocessed",
        backref="raw",
        uselist=False,
        cascade="all, delete-orphan"
    )


# =====================================================
# PREPROCESSED DATA
# =====================================================
class DataPreprocessed(db.Model):
    __tablename__ = "data_preprocessed"

    id = db.Column(db.Integer, primary_key=True)
    raw_id = db.Column(db.Integer, db.ForeignKey("data_raw.id"), nullable=False)

    row_json = db.Column(db.JSON, nullable=False)
    any_outlier = db.Column(db.String(20))

    processed_at = db.Column(db.DateTime, default=datetime.utcnow)
