from datetime import datetime
from typing import Annotated, Union

from fastapi import FastAPI, Request, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder

app = FastAPI()
templates = Jinja2Templates(directory="templates")

learning_days = 0
routine_days = 0

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/index_data", response_class=HTMLResponse)
def index_data(request: Request, hx_request: Annotated[Union[str, None], Header()] = None):
    data = { "learning_days": learning_days, "routine_days": routine_days }
    td = datetime.now()
    data['day_number']= datetime(td.year, td.month, td.day).timetuple().tm_mday
    data['year'] = td.year
    
    if hx_request:
        return templates.TemplateResponse(
            request=request, name="index_data.html", context={"data": data}
        )
    return JSONResponse(content=jsonable_encoder(data))

@app.put("/update_days/{value}", response_class=HTMLResponse)
def update_days(request: Request, value: str):
    global learning_days, routine_days 
    if value == "ld":
        learning_days = learning_days + 1
    if value == "rd":
        routine_days = routine_days + 1
    data = { "learning_days": learning_days, "routine_days": routine_days }
     
    return templates.TemplateResponse(
            request=request, name="index_data.html", context={"data": data}
        )