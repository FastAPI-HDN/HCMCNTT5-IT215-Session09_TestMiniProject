from fastapi import FastAPI, HTTPException, status, Request
from pydantic import BaseModel, field_validator, Field
from typing import Any, List, Optional
from datetime import datetime, timezone
from fastapi.responses import JSONResponse


flights_db = [
    {"id": 1, "flight_number": "VN-213", "destination": "Da Nang", "available_seats": 45, "status": "scheduled", "created_at": "2026-07-01T06:00:00Z"},
    {"id": 2, "flight_number": "VJ-122", "destination": "Phu Quoc", "available_seats": 12, "status": "scheduled", "created_at": "2026-07-01T07:30:00Z"}
]

app = FastAPI(title=" hệ thống Quản lý sân bay - Chuyến bay (Flight manager API)")

class APIResponse(BaseModel):
    status: str
    message: str
    data: Any | None
    error: str | None
    timestamp: str
    path: str
    

current_id = 2

class FlightCreateRequest (BaseModel):
    flight_number: str = Field (..., min_length=5, max_length = 10, description="Ma chuyen bay")
    destination: str = Field (..., description="Diem den")
    available_seats: int = Field (..., ge = 1, description="So ghe trong")
    @field_validator ("flight_number", "destination")
    @classmethod
    def prevent_empty(cls, value:str) -> str:
        stripped_value =value.strip()
        if not stripped_value:
            raise ValueError ("Du lieu khong duoc de trong")
        return stripped_value
    
def create_unified_envelope (status_code: int, message: str, path: str, data: any = None, error: Optional[str] = None) -> dict:
    return {
        "statusCode": status_code,
        "message": message,
        "data": data,
        "error": error,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "path": path
    }
    
@app.get("/flights")
def get_all_flist(request: Request, status: Optional[str] = None):
    if status:
        filtered_flights = [f for f in flights_db if f["status"].lower() == status.lower()]
    else:
        filtered_flights = flights_db
        
    envelop = create_unified_envelope (
        status_code= 200,
        message="Lay danh sach thanh cong",
        data = filtered_flights,
        path=str(request.url.path)
    )
    return JSONResponse(status_code=200, content=envelop)

@app.post("/flights")
def create_flight(request: Request, payload: FlightCreateRequest):
    global current_id
    flight_exists = any(f["flight_number"].upper() == payload.flight_number.upper() for f in flights_db)
    if flight_exists:
        evelope_error = create_unified_envelope(
            status_code = 400,
            message="Lỗi: Số hiệu chuyến bay này đã tồn tại trên hệ thống điều hành!",
            data = None,
            error = "ERR-AIR-01: Flight number conflict in current active schedule database.",
            path = str(request.url.path)
        )
        return JSONResponse (status_code =400, content = evelope_error)
    
    current_id += 1 
    
    new_flight = {
        "id": current_id,
        "flight_number": payload.flight_number.strip().upper(),
        "destination": payload.destination.strip(),
        "available_seats": payload.available_seats(),
        "status": "scheduled",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    flights_db.append(new_flight)
    envelope_success = create_unified_envelope(
        status_code = 201,
        message ="Khởi tạo chuyến bay mới thành công!",
        data=new_flight,
        path=str(request.url.path)
    )
    return JSONResponse(status_code=201, content = envelope_success)

@app.delete("/flights/{flight_id}")
def delete_flight (request: Request, flight_id: int):
    target_flight = None
    for f in flights_db:
        if f["id"] == flight_id:
            target_flight = f
            break
        
    if target_flight is None:
        envelope_not_found = create_unified_envelope(
            status_code=404,
            message= "Lỗi: Không tìm thấy mã chuyến bay yêu cầu để hủy!",
            error = "ERR-AIR-02: Target flight ID is missing from system scope.",
            path=str(request.url.path)
        )
        return JSONResponse (status_code=404, content=envelope_not_found)
    
    flights_db.remove(target_flight)
    
    envelop_delete = create_unified_envelope(
        status_code=200,
        message="huy chuyen bay",
        data = None,
        path = str(request.url.path)
        
    )
    return JSONResponse(status_code=200, content = envelop_delete)