from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from database import Base
import uuid
from datetime import datetime

class User(SQLAlchemyBaseUserTableUUID, Base):
    formulaires = relationship("Formulaire", back_populates="owner")

class Formulaire(Base):
    __tablename__ = "formulaires"  # ← Ligne manquante ajoutée
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    titre = Column(String(200))
    structure = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("user.id"))

    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)

    owner = relationship("User", back_populates="formulaires")
    reponses = relationship("Reponse", back_populates="formulaire", cascade="all, delete-orphan")

class Reponse(Base):
    __tablename__ = "reponses"  # ← Ligne manquante ajoutée
    id = Column(Integer, primary_key=True)
    form_id = Column(UUID(as_uuid=True), ForeignKey("formulaires.id"))
    data = Column(JSONB)
    ip_hash = Column(String(64))
    submitted_at = Column(DateTime, default=datetime.utcnow)
    formulaire = relationship("Formulaire", back_populates="reponses")
