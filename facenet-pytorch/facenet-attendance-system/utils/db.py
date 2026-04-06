"""
数据库初始化和工具函数
"""
from models import db
from flask import Flask
from config import Config

def init_db(app: Flask):
    """初始化数据库"""
    db.init_app(app)
    with app.app_context():
        db.create_all()

def get_db():
    """获取数据库实例"""
    return db
