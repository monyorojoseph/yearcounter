from datetime import datetime, date
from typing import Annotated, Union

from fastapi import Depends, FastAPI, Request, Header, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder

from sqlmodel import Session, SQLModel, select

from databse import engine
from models import Track


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def startup():
    create_db_and_tables()

def initialize_year(session: Session, year: str):
    """Initialize records for a new year if they don't exist."""
    for type_code in ["ld", "rd"]:
        statement = select(Track).where(
            Track.year == year,
            Track.type == type_code
        )
        existing = session.exec(statement).first()
        
        if not existing:
            new_track = Track(
                year=year,
                updated=date(int(year), 1, 1),  # Set to January 1st of the year
                current_count=0,
                type=type_code
            )
            session.add(new_track)
    session.commit()

def get_year_counts(session: Session, year: str) -> dict:
    """Get learning and routine days counts for a specific year."""
    # Initialize year if it doesn't exist
    initialize_year(session, year)
    
    counts = {"learning_days": 0, "routine_days": 0}
    
    # Get latest counts for the year
    for type_code in ["ld", "rd"]:
        statement = select(Track).where(
            Track.year == year,
            Track.type == type_code
        ).order_by(Track.updated.desc())
        result = session.exec(statement).first()
        
        if result:
            if type_code == "ld":
                counts["learning_days"] = result.current_count
            else:
                counts["routine_days"] = result.current_count
    
    return counts

def check_daily_update(session: Session, year: str, type_code: str, current_date: date) -> bool:
    """Check if an update has already been made today."""
    statement = select(Track).where(
        Track.year == year,
        Track.type == type_code,
        Track.updated == current_date
    )
    today_update = session.exec(statement).first()
    return today_update is not None

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/index_data", response_class=HTMLResponse)
def index_data(
    request: Request,
    session: SessionDep,
    hx_request: Annotated[Union[str, None], Header()] = None
):
    td = datetime.now()
    current_year = str(td.year)
    
    counts = get_year_counts(session, current_year)
    data = {
        "learning_days": counts["learning_days"],
        "routine_days": counts["routine_days"],
        "day_number": td.timetuple().tm_mday,
        "year": td.year
    }
    
    if hx_request:
        return templates.TemplateResponse(
            request=request,
            name="index_data.html",
            context={"data": data}
        )
    return JSONResponse(content=jsonable_encoder(data))

@app.put("/update_days/{value}", response_class=HTMLResponse)
def update_days(request: Request, session: SessionDep, value: str):
    if value not in ["ld", "rd"]:
        raise HTTPException(status_code=400, detail="Invalid value type. Must be 'ld' or 'rd'")
    
    td = datetime.now()
    current_year = str(td.year)
    current_date = td.date()
    
    # Initialize year if needed
    initialize_year(session, current_year)
    
    # Check if already updated today
    if check_daily_update(session, current_year, value, current_date):
        raise HTTPException(
            status_code=400,
            detail=f"Already updated {value} today. Only one update per day is allowed."
        )
    
    # Get current count
    statement = select(Track).where(
        Track.year == current_year,
        Track.type == value
    ).order_by(Track.updated.desc())
    current_record = session.exec(statement).first()
    
    # Create new record with incremented count
    new_track = Track(
        year=current_year,
        updated=current_date,
        current_count=current_record.current_count + 1,
        type=value
    )
    session.add(new_track)
    session.commit()
    
    # Get updated counts for response
    counts = get_year_counts(session, current_year)
    data = {
        "learning_days": counts["learning_days"],
        "routine_days": counts["routine_days"],
        "day_number": td.timetuple().tm_mday,
        "year": td.year
    }
    
    return templates.TemplateResponse(
        request=request,
        name="index_data.html",
        context={"data": data}
    )