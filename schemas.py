from pydantic import BaseModel

class LoginCredentials(BaseModel):
    username: str
    password: str

# User Models
class UserBase(BaseModel):
    address: str
    driving_license_number: str
    email: str
    first_name: str
    government_id: str
    last_name: str
    middle_name: str
    phone_number: str
    role: str
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        orm_mode = True

# Maintenance Request Models
class MaintenanceRequestBase(BaseModel):
    maintenance_date: str
    mileage_at_service: int
    notes: str
    service_type: str
    status: str
    total_cost: float
    vehicle_id: int

class MaintenanceRequestCreate(MaintenanceRequestBase):
    maintenance_person_id: int

class MaintenanceRequest(MaintenanceRequestBase):
    maintenance_person_id: int

    class Config:
        orm_mode = True

# Task Models
class TaskBase(BaseModel):
    end_latitude: float
    end_longitude: float
    end_time: str
    notes: str
    start_latitude: float
    start_longitude: float
    start_time: str
    status: str

class TaskCreate(TaskBase):
    driver_id: int

class Task(TaskBase):
    id: int
    driver_id: int

    class Config:
        orm_mode = True

# Vehicle Models
class VehicleBase(BaseModel):
    car_model: str
    color: str
    current_mileage: int
    last_maintenance: str
    license_plate: str
    make: str
    next_maintenance: str
    notes: str
    sitting_capacity: int
    status: str
    type: str
    vin: str
    year: int

class VehicleCreate(VehicleBase):
    pass

class Vehicle(VehicleBase):
    id: int

    class Config:
        orm_mode = True

# Fueling Request Models
class FuelingRequestBase(BaseModel):
    after_fueling_image: str
    amount: float
    before_fueling_image: str
    created_at: str
    fueling_person_id: int
    gas_station: str
    notes: str
    total_cost: float
    updated_at: str
    vehicle_id: int
    status: str

class FuelingRequestCreate(FuelingRequestBase):
    pass

class FuelingRequest(FuelingRequestBase):
    id: int

    class Config:
        orm_mode = True


class DriverBase(BaseModel):
    user_id: int
    vehicle_id: int

class DriverCreate(DriverBase):
    pass

class Driver(DriverBase):
    class Config:
        orm_mode = True
