from app.database import Base, engine, SessionLocal, get_db

ChargingStationsBase = Base
get_charging_stations_db = get_db
