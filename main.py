import os
import subprocess
import itsdangerous
import sys
import time
import urllib.request
import pandas as pd
import glob
import string
import json
from PIL import Image, ImageDraw, ImageFont
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import datetime


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(SessionMiddleware, secret_key="vfVtsDOq0OIW51B4rWv3")
@app.middleware("http")
async def some_middleware(request: Request, call_next):
    response = await call_next(request)
    session = request.cookies.get('session')
    if session:
        response.set_cookie(key='session', value=request.cookies.get('session'), httponly=True)
    return response

SECRET_TOKEN = "kshfuqwh323E34thisispasswordtosend"  # Replace with your own secret token



def make_certificates(name):
    SHEET_URL_PARAMS = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vStfiD-UlNpvWPKAboWqqa_0FR3HbffWDryPfkGZhkGqZ1klYfiIUj_ixhb-RYdy4fKgwS3qwAEbKG5/pub?gid=1419166889&single=true&output=csv'
    SHEET_URL_LIST = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vStfiD-UlNpvWPKAboWqqa_0FR3HbffWDryPfkGZhkGqZ1klYfiIUj_ixhb-RYdy4fKgwS3qwAEbKG5/pub?gid=0&single=true&output=csv'
    urllib.request.urlretrieve(
        SHEET_URL_PARAMS,
        "params/params.csv")
    params_col_list = ["Item", "URLofparam"]
    allparams = pd.read_csv("params/params.csv", usecols=params_col_list)
    itemparam = allparams["Item"]
    urlparam = allparams["URLofparam"]
    certtemplatelink = urlparam[0]
    fonttemplatelink = urlparam[1]
    bodytemplatelink = urlparam[2]
    textpos = float(urlparam[3])
    fontcolor = urlparam[4]
    fontSize = fontSize = int(float(urlparam[5]))
    urllib.request.urlretrieve(fonttemplatelink, "font.ttf")
    urllib.request.urlretrieve(SHEET_URL_LIST, "params/list2.csv")
    urllib.request.urlretrieve(certtemplatelink, "params/certtemp.png")
    urllib.request.urlretrieve(bodytemplatelink, "params/body.html")
    FONT_FILE = ImageFont.truetype(r'font.ttf', fontSize)
    FONT_COLOR = fontcolor  # You can use the same font color for both name and date

    # Load template and calculate its dimensions
    template = Image.open(r'params/certtemp.png')
    WIDTH, HEIGHT = template.size

    # Convert the template to RGB if necessary and prepare for drawing
    image_source_rgba = Image.open(r'params/certtemp.png')
    rgb = Image.new('RGB', image_source_rgba.size, (255, 255, 255))  # white background
    if image_source_rgba.mode != 'RGBA':
        image_source_rgba = image_source_rgba.convert('RGBA')
    rgb.paste(image_source_rgba, mask=image_source_rgba.split()[3])  # paste using alpha channel as mask

    # Prepare drawing context
    draw = ImageDraw.Draw(rgb)

    # Draw the name
    name_bbox = FONT_FILE.getbbox(name)
    name_width, name_height = name_bbox[2], name_bbox[3]
    draw.text(((WIDTH - name_width) / 2, (HEIGHT - name_height) / textpos - 31), name, fill=FONT_COLOR, font=FONT_FILE)

    # Decide on the date format and calculate its position
    date = datetime.datetime.now().strftime("%B %d, %Y")  # Format the date as "Month DD, YYYY"
    DATE_FONT_SIZE = int(fontSize * 0.5)  # Adjust the date font size as needed
    DATE_FONT_FILE = ImageFont.truetype(r'font.ttf', DATE_FONT_SIZE)
    date_margin_left = 320  # Margin from the left for the date
    date_margin_bottom = 300  # Margin from the bottom for the date
    date_x = date_margin_left
    date_y = HEIGHT - DATE_FONT_FILE.getsize(date)[1] - date_margin_bottom

    # Draw the date
    draw.text((date_x, date_y), date, fill=FONT_COLOR, font=DATE_FONT_FILE)

    # Save the image
    try:
        rgb.save('static/template.png', "PNG", resolution=100.0)
    except Exception as e:
        print("Error: ", e)

    return textpos, fontcolor, fontSize


@app.get("/template")
async def show_image(token: str = Query(None)):
    if token != SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    name = "Dr Taha Abdullah Mohammed Albalasmeh"
    

    textpos, fontcolor, fontSize = make_certificates(name)

    image_html = f"""
    <html>
        <body>
            <h2>Text Position: {textpos}</h2>
            <h2>Font Color: {fontcolor}</h2>
            <h2>Font Size: {fontSize}</h2>
            <h1>Here is the template:</h1>
            <img src="/static/template.png" alt="Certificate" />
        </body>
    </html>
    """
    return HTMLResponse(content=image_html)

@app.get("/run_script")
def run_script(request: Request, response: Response, token: str = Query(None)):
    # Check if the token is correct
    if token != SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Check if the script is already running
    if "script_running" in request.session:
        raise HTTPException(status_code=400, detail="Script is already running")

    # Set a flag in the session to indicate that the script is running
    request.session["script_running"] = True

    # Run the script and capture the output
    process = subprocess.Popen([sys.executable, "improvedcertmailer1.py"], stdout=subprocess.PIPE)

    # Display a progress bar while the script is running
    while process.poll() is None:
        time.sleep(0.5)
        print("|", end="")
        sys.stdout.flush()

    # Remove the flag from the session to indicate that the script has finished running
    del request.session["script_running"]

    # Return the output of the script as an HTML response
    return HTMLResponse(process.stdout.read())


@app.get("/togoogledrive")
async def upload_certificates_to_google_drive(token: str = Query(None)):
    if token != SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        process = subprocess.run(
            [sys.executable, "todrive.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )

        print(f"Script output: {process.stdout}")
        print(f"Script error output: {process.stderr}")

        result = json.loads(process.stdout)
        if "error" in result:
            return {"detail": "Failed to capture output from the script"}

        uploaded_count = result.get("uploaded_count")
        elapsed_time = result.get("elapsed_time")

        return {"detail": f"Uploaded {uploaded_count} certificates to Google Drive in {elapsed_time:.2f} seconds"}

    except Exception as e:
        return {"detail": f"Error occurred: {str(e)}"}
