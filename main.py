from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI, HTTPException, Depends, Body, status
from sqlalchemy.orm import Session
from typing import List
from models import User as DBUser  # Import User model from models.py
from schemas import UserCreate, User  # Import User Pydantic models from pydantic.py
from models import Vehicle as DBVehicle
from schemas import Vehicle, VehicleCreate, Driver, DriverCreate
from schemas import MaintenanceRequest, MaintenanceRequestCreate
from models import MaintenanceRequest as DBMaintenanceRequest
from schemas import TaskCreate, Task
from models import Task as DBTask
from models import FuelingRequest as DBFuelingRequest
from schemas import FuelingRequest, FuelingRequestCreate, LoginCredentials
from passlib.context import CryptContext
from auth import authenticate_user, create_access_token, get_current_user, Token, ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi import APIRouter
from models import AuctionVehicle as AuctionVehicle
from schemas import AuctionVehicleResponse as AuctionVehicleResponse, AuctionVehicleCreate as AuctionVehicleCreate

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


SQLALCHEMY_DATABASE_URL = 'postgresql://postgres:admin@35.228.129.140/vms'

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

router = APIRouter()
users_router = APIRouter(tags=["Users"])
vehicles_router = APIRouter(tags=["Vehicles"])
maintenance_router = APIRouter(tags=["Maintenance Requests"])
tasks_router = APIRouter(tags=["Tasks"])
fueling_router = APIRouter(tags=["Fueling Requests"])
drivers_router = APIRouter(tags=["Drivers"])
authorization = APIRouter(tags=["Authorization"])
auction = APIRouter(tags=["Auction"])

app = FastAPI()

# Dependency for getting the DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#authorize
@app.post("/token", response_model=Token)
async def authorize(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}



#LOGIN
@authorization.post("/authorize", response_model=Token)
async def login_for_access_token(credentials: LoginCredentials = Body(...), db: Session = Depends(get_db)):
    user = authenticate_user(credentials.username, credentials.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}




#get by token
@authorization.get("/users/me/", response_model=User)
async def read_current_user(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Fetch the current user profile. The user is identified by the JWT token sent in the request's Authorization header.
    """
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return current_user


#USERS
@users_router.post("/users/", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    # Hash the password before storing it in the database
    hashed_password = pwd_context.hash(user.password)
    db_user = DBUser(**user.dict(exclude={"password"}), password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@users_router.get("/users/", response_model=List[User])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    # Password field is not included in the User schema, so it's not returned in the response
    users = db.query(DBUser).offset(skip).limit(limit).all()
    return users

@users_router.get("/users/{user_id}", response_model=User)
def read_user(user_id: int, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@users_router.put("/users/{user_id}", response_model=User)
def update_user(user_id: int, user: UserCreate, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user.dict(exclude_unset=True)
    if "password" in update_data:
        # Hash the new password before updating
        update_data["password"] = pwd_context.hash(update_data["password"])

    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user

@users_router.delete("/users/{user_id}", response_model=User)
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return user



# Vehicles
@vehicles_router.post("/vehicles/", response_model=Vehicle)
def create_vehicle(vehicle: VehicleCreate, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    db_vehicle = DBVehicle(**vehicle.dict())
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle

@vehicles_router.get("/vehicles/", response_model=List[Vehicle])
def read_vehicles(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    vehicles = db.query(DBVehicle).offset(skip).limit(limit).all()
    return vehicles

@vehicles_router.get("/vehicles/{vehicle_id}", response_model=Vehicle)
def read_vehicle(vehicle_id: int, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    vehicle = db.query(DBVehicle).filter(DBVehicle.id == vehicle_id).first()
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle

@vehicles_router.put("/vehicles/{vehicle_id}", response_model=Vehicle)
def update_vehicle(vehicle_id: int, vehicle: VehicleCreate, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    db_vehicle = db.query(DBVehicle).filter(DBVehicle.id == vehicle_id).first()
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    for var, value in vars(vehicle).items():
        setattr(db_vehicle, var, value) if value else None

    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle

@vehicles_router.delete("/vehicles/{vehicle_id}", response_model=Vehicle)
def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    vehicle = db.query(DBVehicle).filter(DBVehicle.id == vehicle_id).first()
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    db.delete(vehicle)
    db.commit()
    return vehicle

# Maintenance Requests
@maintenance_router.post("/maintenance_requests/", response_model=MaintenanceRequest)
def create_maintenance_request(maintenance_request: MaintenanceRequestCreate, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    db_maintenance_request = DBMaintenanceRequest(**maintenance_request.dict())
    db.add(db_maintenance_request)
    db.commit()
    db.refresh(db_maintenance_request)
    return db_maintenance_request

@maintenance_router.get("/maintenance_requests/", response_model=List[MaintenanceRequest])
def read_maintenance_requests(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    maintenance_requests = db.query(DBMaintenanceRequest).offset(skip).limit(limit).all()
    return maintenance_requests

@maintenance_router.get("/maintenance_requests/{maintenance_request_id}", response_model=MaintenanceRequest)
def read_maintenance_request(maintenance_request_id: int, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    maintenance_request = db.query(DBMaintenanceRequest).filter(DBMaintenanceRequest.id == maintenance_request_id).first()
    if maintenance_request is None:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    return maintenance_request

@maintenance_router.put("/maintenance_requests/{maintenance_request_id}", response_model=MaintenanceRequest)
def update_maintenance_request(maintenance_request_id: int, maintenance_request: MaintenanceRequestCreate, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    db_maintenance_request = db.query(DBMaintenanceRequest).filter(DBMaintenanceRequest.id == maintenance_request_id).first()
    if db_maintenance_request is None:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    
    update_data = maintenance_request.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_maintenance_request, key, value)
    
    db.commit()
    db.refresh(db_maintenance_request)
    return db_maintenance_request

@maintenance_router.delete("/maintenance_requests/{maintenance_request_id}", response_model=MaintenanceRequest)
def delete_maintenance_request(maintenance_request_id: int, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    maintenance_request = db.query(DBMaintenanceRequest).filter(DBMaintenanceRequest.id == maintenance_request_id).first()
    if maintenance_request is None:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    
    db.delete(maintenance_request)
    db.commit()
    return maintenance_request


#task
@tasks_router.post("/tasks/", response_model=Task)
def create_task(task: TaskCreate, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    db_task = DBTask(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@tasks_router.get("/tasks/", response_model=List[Task])
def read_tasks(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    tasks = db.query(DBTask).offset(skip).limit(limit).all()
    return tasks

@tasks_router.get("/tasks/{task_id}", response_model=Task)
def read_task(task_id: int, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    task = db.query(DBTask).filter(DBTask.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@tasks_router.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task: TaskCreate, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    db_task = db.query(DBTask).filter(DBTask.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    for var, value in vars(task).items():
        setattr(db_task, var, value) if value else None

    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@tasks_router.delete("/tasks/{task_id}", response_model=Task)
def delete_task(task_id: int, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    task = db.query(DBTask).filter(DBTask.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(task)
    db.commit()
    return task


# Fueling Requests
@fueling_router.get("/fueling_requests/", response_model=List[FuelingRequest])
def read_fueling_requests(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    fueling_requests = db.query(DBFuelingRequest).offset(skip).limit(limit).all()
    return fueling_requests

@fueling_router.get("/fueling_requests/{fueling_request_id}", response_model=FuelingRequest)
def read_fueling_request(fueling_request_id: int, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    fueling_request = db.query(DBFuelingRequest).filter(DBFuelingRequest.id == fueling_request_id).first()
    if fueling_request is None:
        raise HTTPException(status_code=404, detail="Fueling request not found")
    return fueling_request

@fueling_router.post("/fueling_requests/", response_model=FuelingRequest)
def create_fueling_request(fueling_request: FuelingRequestCreate, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    db_fueling_request = DBFuelingRequest(**fueling_request.dict())
    db.add(db_fueling_request)
    db.commit()
    db.refresh(db_fueling_request)
    return db_fueling_request

@fueling_router.put("/fueling_requests/{fueling_request_id}", response_model=FuelingRequest)
def update_fueling_request(fueling_request_id: int, fueling_request: FuelingRequestCreate, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    db_fueling_request = db.query(DBFuelingRequest).filter(DBFuelingRequest.id == fueling_request_id).first()
    if db_fueling_request is None:
        raise HTTPException(status_code=404, detail="Fueling request not found")
    
    update_data = fueling_request.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_fueling_request, key, value)
    
    db.commit()
    db.refresh(db_fueling_request)
    return db_fueling_request

@fueling_router.delete("/fueling_requests/{fueling_request_id}", response_model=FuelingRequest)
def delete_fueling_request(fueling_request_id: int, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    fueling_request = db.query(DBFuelingRequest).filter(DBFuelingRequest.id == fueling_request_id).first()
    if fueling_request is None:
        raise HTTPException(status_code=404, detail="Fueling request not found")
    
    db.delete(fueling_request)
    db.commit()
    return fueling_request

#driver:
@drivers_router.get("/drivers/", response_model=List[Driver])
def read_drivers(db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    drivers = db.query(Driver).all()
    return drivers

@drivers_router.get("/drivers/{user_id}", response_model=Driver)
def read_driver_by_user_id(user_id: int, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    driver = db.query(Driver).filter(Driver.user_id == user_id).first()
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver

@drivers_router.get("/drivers/{vehicle_id}", response_model=Driver)
def read_driver_by_vehicle_id(vehicle_id: int, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    driver = db.query(Driver).filter(Driver.vehicle_id == vehicle_id).first()
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver

@drivers_router.post("/drivers/", response_model=Driver)
def create_driver(driver: DriverCreate, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    db_driver = Driver(**driver.dict())
    db.add(db_driver)
    db.commit()
    db.refresh(db_driver)
    return db_driver

@drivers_router.put("/drivers/{user_id}", response_model=Driver)
def update_driver(user_id: int, vehicle_id: int, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    driver = db.query(Driver).filter(Driver.user_id == user_id).first()
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    driver.vehicle_id = vehicle_id
    db.commit()
    db.refresh(driver)
    return driver

@drivers_router.delete("/drivers/{user_id}", response_model=Driver)
def delete_driver(user_id: int, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    driver = db.query(Driver).filter(Driver.user_id == user_id).first()
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    db.delete(driver)
    db.commit()
    return driver



#auction
@auction.post("/auction-vehicles/", response_model=AuctionVehicleResponse)
def create_auction_vehicle(auction_vehicle: AuctionVehicleCreate, db: Session = Depends(get_db),):
    db_auction_vehicle = AuctionVehicle(**auction_vehicle.dict())
    db.add(db_auction_vehicle)
    db.commit()
    db.refresh(db_auction_vehicle)
    return db_auction_vehicle

# GET endpoint to read all auction vehicles
@auction.get("/auction-vehicles/", response_model=List[AuctionVehicleResponse])
def read_auction_vehicles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    auction_vehicles = db.query(AuctionVehicle).offset(skip).limit(limit).all()
    return auction_vehicles

# GET endpoint to read a single auction vehicle by ID
@auction.get("/auction-vehicles/{id}", response_model=AuctionVehicleResponse)
def read_auction_vehicle(id: int, db: Session = Depends(get_db)):
    auction_vehicle = db.query(AuctionVehicle).filter(AuctionVehicle.id == id).first()
    if auction_vehicle is None:
        raise HTTPException(status_code=404, detail="Auction vehicle not found")
    return auction_vehicle

# PUT endpoint to update an auction vehicle
@auction.put("/auction-vehicles/{id}", response_model=AuctionVehicleResponse)
def update_auction_vehicle(id: int, updated_vehicle: AuctionVehicleCreate, db: Session = Depends(get_db)):
    auction_vehicle = db.query(AuctionVehicle).filter(AuctionVehicle.id == id).first()
    if auction_vehicle is None:
        raise HTTPException(status_code=404, detail="Auction vehicle not found")
    for key, value in updated_vehicle.dict().items():
        setattr(auction_vehicle, key, value) if value is not None else None
    db.commit()
    return auction_vehicle

# DELETE endpoint to delete an auction vehicle
@auction.delete("/auction-vehicles/{id}", response_model=AuctionVehicleResponse)
def delete_auction_vehicle(id: int, db: Session = Depends(get_db)):
    auction_vehicle = db.query(AuctionVehicle).filter(AuctionVehicle.id == id).first()
    if auction_vehicle is None:
        raise HTTPException(status_code=404, detail="Auction vehicle not found")
    db.delete(auction_vehicle)
    db.commit()
    return auction_vehicle


app.include_router(users_router)
app.include_router(vehicles_router)
app.include_router(maintenance_router)
app.include_router(tasks_router)
app.include_router(fueling_router)
app.include_router(drivers_router)
app.include_router(authorization)
app.include_router(auction)