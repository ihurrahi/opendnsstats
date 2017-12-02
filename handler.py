import boto3
import csv
import datetime
import os
import re
import requests
import StringIO

CSVURL = 'https://dashboard.opendns.com/stats/{networkid}/topdomains/{date}/blocked/page{page}.csv'
LOGINURL = 'https://login.opendns.com/?source=dashboard'
NOTIFICATIONARN = 'arn:aws:sns:us-west-2:935037265101:openDNSSummary'

def handler(event, context):
  username = os.environ['USERNAME']
  password = os.environ['PASSWORD']
  networkid = os.environ['NETWORKID']
  date = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

  formtoken = None
  with requests.Session() as s:
    # Find formtoken on login page
    resp = s.get(LOGINURL)
    regex = r'^.*name="formtoken" value="([0-9a-f]*)".*$'
    for line in resp.text.split('\n'):
      if 'formtoken' in line:
        m = re.search(regex, line)
        formtoken = m.group(1)
    if not formtoken:
      raise Exception('No login form token found')
  
    # Use credentials to log in
    success = False
    login_resp = s.post(LOGINURL, data=dict(formtoken=formtoken, username=username, password=password, return_to='https://dashboard.opendns.com/'))
    for line in login_resp.text.split('\n'):
      if 'Logging you in' in line:
        success = True
    if not success:
      raise Exception('Login failed. Check username and password.')
  
    # Download results
    results = []
    page = 1
    while True:
      csv_resp = s.get(CSVURL.format(networkid=networkid, date=date, page=page))
      reader = csv.DictReader(StringIO.StringIO(csv_resp.text))
      for row in reader:
        results.append(row)

      page += 1
      if page == 3:
        break

  # Send notification
  if results:
    client = boto3.client('sns', region_name='us-west-2')
    message = 'Blocked domains for {date}:\nCount Domain\n'.format(date=date)
    for row in results:
      message += '%s %s\n' % (row['Total'], row['Domain'])
    subject = 'OpenDNS Blocked Domains Summary'
    aws_resp = client.publish(TopicArn=NOTIFICATIONARN, Message=message, Subject=subject)
    print aws_resp

