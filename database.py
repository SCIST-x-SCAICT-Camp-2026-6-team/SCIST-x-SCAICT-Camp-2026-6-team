from sqlalchemy import create_engine, Column, String, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 1. 取得環境變數 (由 docker-compose 提供)
# 如果在本機跑，預設連到 localhost
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://hackathon_user:password123@db:5432/travel_db"
)

# 2. 建立資料庫引擎
# pool_pre_ping=True 能在黑客松環境中有效避免資料庫斷線重連的問題
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# 3. 建立 Session 工廠
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. 宣告 ORM 基類
Base = declarative_base()

# 5. 定義 Model (SOLID: SRP 原則)
class UserData(Base):
    __tablename__ = "user_plans"
    
    # 這裡 user_id 是 Primary Key，對應你上傳 JSON 時的 ID
    user_id = Column(String, primary_key=True, index=True)
    # 使用 JSON 欄位儲存整份旅遊偏好
    json_content = Column(JSON)

# 💡 提示：
# 在 main.py 中我們會呼叫 Base.metadata.create_all(bind=engine) 
# 這會自動幫你在 PostgreSQL 裡面建立 user_plans 資料表