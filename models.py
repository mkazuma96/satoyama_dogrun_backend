from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional

Base = declarative_base()

# SQLAlchemy Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    address = Column(String)
    phone_number = Column(String)
    imabari_residency = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    dogs = relationship("Dog", back_populates="owner")
    posts = relationship("Post", back_populates="user")
    comments = relationship("Comment", back_populates="user")

class Dog(Base):
    __tablename__ = "dogs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    breed = Column(String)
    weight = Column(String)
    personality = Column(JSON)  # List of strings
    last_vaccination_date = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="dogs")

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    tag = Column(String)
    hashtags = Column(String, nullable=True)
    likes = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post")

class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text)
    post_id = Column(Integer, ForeignKey("posts.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    post = relationship("Post", back_populates="comments")
    user = relationship("User", back_populates="comments")

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    date = Column(String)
    time = Column(String)
    participants = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Notice(Base):
    __tablename__ = "notices"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(Text)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(String, primary_key=True)
    label = Column(String)

# Pydantic Models for API
class UserBase(BaseModel):
    email: str
    full_name: str
    address: str
    phone_number: str
    imabari_residency: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class DogBase(BaseModel):
    name: str
    breed: str
    weight: str
    personality: List[str]
    last_vaccination_date: str

class DogCreate(DogBase):
    pass

class DogResponse(DogBase):
    id: int
    owner_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class PostBase(BaseModel):
    content: str
    tag: str
    hashtags: Optional[str] = None

class PostCreate(PostBase):
    pass

class PostResponse(PostBase):
    id: int
    likes: int
    user_id: int
    created_at: datetime
    user_name: str
    comments_count: int
    
    class Config:
        from_attributes = True

class CommentBase(BaseModel):
    text: str

class CommentCreate(CommentBase):
    pass

class CommentResponse(CommentBase):
    id: int
    post_id: int
    user_id: int
    created_at: datetime
    user_name: str
    
    class Config:
        from_attributes = True

class EventResponse(BaseModel):
    id: int
    title: str
    date: str
    time: str
    participants: int
    
    class Config:
        from_attributes = True

class NoticeResponse(BaseModel):
    id: int
    title: str
    content: str
    read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class TagResponse(BaseModel):
    id: str
    label: str
    
    class Config:
        from_attributes = True 