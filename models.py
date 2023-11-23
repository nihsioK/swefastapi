from sqlalchemy import Column, Integer, LargeBinary, String, Float, ForeignKey, DECIMAL, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

# Base class
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    address = Column(String)
    driving_license_number = Column(String)
    email = Column(String)
    first_name = Column(String)
    government_id = Column(String)
    last_name = Column(String)
    middle_name = Column(String)
    phone_number = Column(String)
    role = Column(String)
    username = Column(String)
    password = Column(String)

class MaintenanceRequest(Base):
    __tablename__ = "maintenancerequests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    maintenance_date = Column(String)
    maintenance_person_id = Column(Integer, ForeignKey('users.id'))
    mileage_at_service = Column(Integer)
    notes = Column(Text)
    service_type = Column(String)
    status = Column(String)
    total_cost = Column(DECIMAL)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id'))

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    driver_id = Column(Integer, ForeignKey('users.id'))
    end_latitude = Column(Float)
    end_longitude = Column(Float)
    end_time = Column(String)
    notes = Column(Text)
    start_latitude = Column(Float)
    start_longitude = Column(Float)
    start_time = Column(String)
    status = Column(String)

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    assigned_driver = Column(Integer, ForeignKey('users.id'), unique=True)
    car_model = Column(String)
    color = Column(String)
    current_mileage = Column(Integer)
    last_maintenance = Column(String)
    license_plate = Column(String)
    make = Column(String)
    next_maintenance = Column(String)
    notes = Column(Text)
    sitting_capacity = Column(Integer)
    status = Column(String)
    type = Column(String)
    vin = Column(String)
    year = Column(Integer)

class FuelingRequest(Base):
    __tablename__ = "fuelingrequests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    after_fueling_image = Column(String)
    amount = Column(DECIMAL)
    before_fueling_image = Column(String)
    created_at = Column(String)
    fueling_person_id = Column(Integer, ForeignKey('users.id'))
    gas_station = Column(String)
    notes = Column(Text)
    total_cost = Column(DECIMAL)
    updated_at = Column(String)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id'))
    status = Column(String)


class Driver(Base):
    __tablename__ = "drivers"
    
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id'), primary_key=True)
    user = relationship("User")
    vehicle = relationship("Vehicle")


class AuctionVehicle(Base):
    __tablename__ = "auction_vehicle"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    status = Column(String)
    description = Column(String)
    starting_bid = Column(DECIMAL)
    image = Column(String)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id'), primary_key=True)
    bought_user = Column(Integer, ForeignKey('users.id'), nullable=True)
    final_price = Column(DECIMAL)