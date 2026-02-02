from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Date, DateTime, JSON
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String) # Admin, Accountant, Sales

class Party(Base):
    __tablename__ = "parties"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    address = Column(String)
    mobile_number = Column(String)
    gst_number = Column(String)
    default_margin = Column(Float, default=10.0)
    transport_rate_logic = Column(String, default="per_kg") # per_kg, per_trip, fixed
    is_active = Column(Boolean, default=True)

class PaperRate(Base):
    __tablename__ = "paper_rates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True) # Golden, Natural, Duplex, etc.
    rate = Column(Float) # Rate per KG
    bf = Column(Float, default=18.0) # Burst Factor
    unit = Column(String, default="KG")
    # Optional: Party specific override could be a separate table or JSON field, keeping simple for now

class OperationRate(Base):
    __tablename__ = "operation_rates"
    id = Column(Integer, primary_key=True, index=True)
    operation_name = Column(String, index=True) # Corrugation, Pasting, etc.
    rate = Column(Float)
    unit = Column(String) # per_kg, per_sq_meter, per_box, fixed
    is_active = Column(Boolean, default=True)

class Quotation(Base):
    __tablename__ = "quotations"
    id = Column(Integer, primary_key=True, index=True)
    quotation_number = Column(String, unique=True, index=True)
    party_id = Column(Integer, ForeignKey("parties.id"))
    created_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Draft") # Draft, Approved, Sent
    total_amount = Column(Float)
    
    party = relationship("Party")
    items = relationship("QuotationItem", back_populates="quotation")

class QuotationItem(Base):
    __tablename__ = "quotation_items"
    id = Column(Integer, primary_key=True, index=True)
    quotation_id = Column(Integer, ForeignKey("quotations.id"))
    
    # Box Specs
    box_type = Column(String)
    length = Column(Float)
    width = Column(Float)
    height = Column(Float)
    unit = Column(String) # mm, inch
    ply = Column(Integer)
    quantity = Column(Integer)
    layer_details = Column(JSON) # Stores list of {layer: name, gsm: val}
    
    # Calculated Fields (Stored for history)
    sheet_weight = Column(Float)
    box_weight = Column(Float)
    material_cost = Column(Float)
    conversion_cost = Column(Float)
    cost_per_box = Column(Float)
    margin_percent = Column(Float)
    selling_price = Column(Float)
    
    quotation = relationship("Quotation", back_populates="items")

class Terms(Base):
    __tablename__ = "terms"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, default="General Terms")
    content = Column(String)

class ReelSize(Base):
    __tablename__ = "reel_sizes"
    id = Column(Integer, primary_key=True, index=True)
    width = Column(Float, index=True) # Usually in Inches (e.g. 52.0)
    unit = Column(String, default="Inch") # Inch, cm, mm
    is_active = Column(Boolean, default=True)
