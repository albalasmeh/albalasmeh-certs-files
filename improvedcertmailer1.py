
from threading import Thread
from time import perf_counter
from PIL import Image, ImageFont, ImageDraw
import glob
import pandas as pd
import requests
from io import BytesIO
import urllib.request
from urllib.request import urlretrieve
import xlrd
import smtplib
import os
import sys
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
import boto3
import string
import re
import datetime

def is_valid_email(email):
    email_regex = re.compile(r"[^@]+@[^@]+\.[^@]+")
    return email_regex.match(email)


ses_client = boto3.client('ses', region_name='us-east-1')

# Global Variables
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
fontSize = int(float(urlparam[5]))
harddate = urlparam[6]
datemargin_bottom = int(float(urlparam[7]))
print("text position in certificate: ",textpos)   
urllib.request.urlretrieve(
  
   fonttemplatelink,"font.ttf")
urllib.request.urlretrieve(
  SHEET_URL_LIST,
   "params/list2.csv")
urllib.request.urlretrieve(
  
   certtemplatelink,"params/certtemp.png")
urllib.request.urlretrieve(
  
  bodytemplatelink,"params/body.html")
FONT_FILE = ImageFont.truetype(r'font.ttf', fontSize)
FONT_COLOR = fontcolor


template = Image.open(r'params/certtemp.png')
WIDTH, HEIGHT = template.size

def remove_dir_content():
    files = glob.glob('out/*')
    for f in files:
        os.remove(f)
def make_certificates(name):
    try:
        '''Function to save certificates as a .png file'''


        image_sourcergba = Image.open(r'params/certtemp.png')

        
        rgb = Image.new('RGB', image_sourcergba.size, (255, 255, 255))  # white background
                # Check if the image does not have an alpha channel
        if image_sourcergba.mode != 'RGBA':
            # Convert the image to 'RGBA' to add an alpha channel
            image_sourcergba = image_sourcergba.convert('RGBA')
        
        rgb.paste(image_sourcergba, mask=image_sourcergba.split()[3])  # paste using alpha channel as mask
       

        #rgb.paste(image_sourcergba, mask=image_sourcergba.split()[3])               # paste using alpha channel as mask
    
        newname = name.translate(str.maketrans('', '', string.punctuation))

        draw = ImageDraw.Draw(rgb)
        try:
            # Finding the width and height of the text. 
            name_bbox = FONT_FILE.getbbox(name)
            name_width, name_height = name_bbox[2], name_bbox[3]

            # Placing it in the center, then making some adjustments.
            draw.text(((WIDTH - name_width) / 2, (HEIGHT - name_height) / textpos - 31), name, fill=FONT_COLOR, font=FONT_FILE)
            
            # Decide on the date format and calculate its position
            #date = datetime.datetime.now().strftime("%B %d, %Y")  # Format the date as "Month DD, YYYY"
                #date = datetime.datetime.now().strftime("%B %d, %Y")  # Format the date as "Month DD, YYYY"
            date = harddate
            DATE_FONT_SIZE = int(fontSize * 0.5)  # Adjust the date font size as needed
            DATE_FONT_FILE = ImageFont.truetype(r'font.ttf', DATE_FONT_SIZE)
            date_margin_left = 320  # Margin from the left for the date
            #date_margin_bottom = 300  # Margin from the bottom for the date

            date_x = date_margin_left
            # #date_y = HEIGHT - DATE_FONT_FILE.getsize(date)[1] - date_margin_bottom
            # date_y = HEIGHT - draw.textsize(date, font=DATE_FONT_FILE)[1] - date_margin_bottom
               # Adjusted part for calculating the date's y position
            date_bbox = DATE_FONT_FILE.getbbox(date)
            date_height = date_bbox[3] - date_bbox[1]  # Bottom - Top
            date_y = HEIGHT - date_height - datemargin_bottom

            # Draw the date using the calculated x and y positions
            draw.text((date_x, date_y), date, fill=FONT_COLOR, font=DATE_FONT_FILE)

                
            rgb.save( 'out/'+newname.replace(" ", "_")+'.pdf', "PDF", resolution=100.0)

        except Exception as e:
            print("Error: ", e)
    except Exception as e:
        print(f"Error creating certificate for '{name}': {e}")
  

def send_cert_email(reciveremail,name):
    try:
        if not is_valid_email(reciveremail):
            print(f"Skipping invalid email: {reciveremail}")
            return
        SENDER = "Dr Taha Alblasmeh <certificates@drtahaalblasmeh.com>"
        RECEIVER = reciveremail
        CHARSET = "utf-8"
        msg = MIMEMultipart('mixed')
        msg['Subject'] = "Certificate of Attendance - Dr Taha Alblasmeh"
        msg['From'] = SENDER
        msg['To'] = RECEIVER
        msg['Reply-To'] = "albalasmehcert@gmail.com"
        newname = name.translate(str.maketrans('', '', string.punctuation))
        msg_body = MIMEMultipart('alternative')
        # text based email body
        BODY_TEXT = "Dear,\n\rPlease using the given link to register today."

        # Opening and reading the HTML email template
        with open('params/body.html', 'r', encoding='utf-8') as HtmlFile:
            BODY_HTML = HtmlFile.read()
        
        # Replacing {{name}} in the HTML content with the actual name
        BODY_HTML = BODY_HTML.replace('{{name}}', newname)
        textpart = MIMEText(BODY_TEXT.encode(CHARSET), 'plain', CHARSET)
        htmlpart = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)

        msg_body.attach(textpart)
        msg_body.attach(htmlpart)

        # Full path to the file that will be attached to the email.
        ATTACHMENT1 = 'out/'+newname.replace(" ", "_")+'.pdf'
        ATTACHMENT2 = 'out/'+newname.replace(" ", "_")+'.pdf'

        # Adding attachments
        att1 = MIMEApplication(open(ATTACHMENT1, 'rb').read())
        att1.add_header('Content-Disposition', 'attachment',
                        filename=os.path.basename(ATTACHMENT1))
        att2 = MIMEApplication(open(ATTACHMENT1, 'rb').read())
        att2.add_header('Content-Disposition', 'attachment',
                        filename=os.path.basename(ATTACHMENT2))

        msg.attach(msg_body)
        msg.attach(att1)
        msg.attach(att2)

        try:
            response = ses_client.send_raw_email(
                Source=SENDER,
                Destinations=[
                    RECEIVER
                ],
                RawMessage={
                    'Data': msg.as_string(),
                },
                #ConfigurationSetName="ConfigSet"
            )

        except Exception as e:
            print("Error: ", e)
    except Exception as e:
        print(f"Error sending email to '{reciveremail}' for '{name}': {e}")  
        
def main():
    col_list = ["Name", "Emailsofparticipant"]
    names = pd.read_csv("params/list2.csv", usecols=col_list,na_filter= False)
    namesofpart = names["Name"]
    reciveremail = names["Emailsofparticipant"]

    
    remove_dir_content()

    # create threads
    threads = [Thread(target=make_certificates, args=(name,))
            for name in namesofpart]

    # start the threads
    for thread in threads:
        thread.start()

    # wait for the threads to complete
    for thread in threads:
        thread.join()

    #for name in namesofpart:
       # make_certificates(name)
    print("#############",len(names), " certificates done.\n#########")

    #for partiemail, partiname in zip(reciveremail, namesofpart):
    #    send_cert_email(partiemail,partiname)
    threads = [Thread(target=send_cert_email, args=(partiemail,partiname))
            for partiemail, partiname in zip(reciveremail, namesofpart)]

    # start the threads
    for thread in threads:
        thread.start()

    # wait for the threads to complete
    for thread in threads:
        thread.join()
    print("#############",len(names), "  emails sent\n########")

if __name__ == "__main__":

    start_time = perf_counter()

    main()

    end_time = perf_counter()
    print(f'It took {end_time- start_time :0.2f} second(s) to complete.')


