"""数据库模型定义"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class ProviderConfig(Base):
    """LLM 供应商配置"""
    __tablename__ = "provider_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), unique=True, nullable=False)       # 内部标识: "openai-gpt4o"
    provider_type = Column(String(32), nullable=False)           # "openai" / "anthropic" / "deepseek" / "ollama"
    display_name = Column(String(128), nullable=False)           # 供应商名称: "OpenAI"
    website = Column(String(256), nullable=True)                 # 官网链接: "https://openai.com"
    api_key = Column(String(512), nullable=True)                 # API Key
    api_base = Column(String(256), nullable=True)                # API 地址: "https://api.openai.com/v1"
    model = Column(String(64), nullable=False)                   # 模型型号: "gpt-4o"
    task_route = Column(String(64), default="all")               # "search" / "read" / "write" / "code" / "chat" / "all"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Paper(Base):
    """论文元数据"""
    __tablename__ = "papers"

    arxiv_id = Column(String(32), primary_key=True)
    title = Column(String(512), nullable=False)
    authors = Column(Text, nullable=True)                         # JSON array
    published = Column(DateTime, nullable=True)
    updated = Column(DateTime, nullable=True)
    categories = Column(Text, nullable=True)                      # JSON array
    summary = Column(Text, nullable=True)
    doi = Column(String(128), nullable=True)
    pdf_path = Column(String(512), nullable=True)
    local_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Note(Base):
    """笔记"""
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    arxiv_id = Column(String(32), ForeignKey("papers.arxiv_id"), nullable=True)
    title = Column(String(512), nullable=False)
    format = Column(String(16), default="markdown")              # "markdown" / "latex"
    content = Column(Text, nullable=True)
    tags = Column(String(256), nullable=True)                    # comma-separated
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Conversation(Base):
    """对话历史"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(256), default="新对话")
    messages = Column(Text, nullable=True)                       # JSON array
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
