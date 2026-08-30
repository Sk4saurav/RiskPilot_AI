from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from .base import Base

class Organization(Base):
    __tablename__ = 'organizations'
    id = Column(String, primary_key=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    events_processed_count = Column(Integer, default=0)
    
    memberships = relationship("OrganizationMembership", back_populates="organization")
    policies = relationship("Policy", back_populates="organization")
    data_sources = relationship("DataSource", back_populates="organization")
    events = relationship("Event", back_populates="organization")

class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    memberships = relationship("OrganizationMembership", back_populates="user")

class OrganizationMembership(Base):
    __tablename__ = 'organization_memberships'
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'))
    organization_id = Column(String, ForeignKey('organizations.id'))
    role = Column(String) # OWNER, ADMIN, ANALYST, VIEWER
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="memberships")
    organization = relationship("Organization", back_populates="memberships")

class DataSource(Base):
    __tablename__ = 'data_sources'
    id = Column(String, primary_key=True)
    organization_id = Column(String, ForeignKey('organizations.id'))
    name = Column(String)
    source_type = Column(String) # api, webhook, batch
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="data_sources")

class ApiKey(Base):
    __tablename__ = 'api_keys'
    id = Column(String, primary_key=True)
    organization_id = Column(String, ForeignKey('organizations.id'))
    name = Column(String)
    key_hash = Column(String, unique=True, nullable=False)
    prefix = Column(String) # e.g. rp_live_
    scopes = Column(String) # JSON string or comma-separated, e.g., "events:write,cases:read"
    source = Column(String) # identifier of the system using it
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    
    organization = relationship("Organization")
