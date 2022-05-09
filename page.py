from bs4 import BeautifulSoup
from flask import Flask
from flask import Flask, jsonify
from flask_cors import CORS
import requests
import urllib.parse
import re

# app = Flask(__name__)
# cors = CORS(app)
# app.config['CORS_HEADERS'] = 'Content-Type'

def remove_refs(input):
  # removes references such as [1]
  input = re.sub('[\[0-9\]]', '', input)
  
  # removes the escape backslash before a single quote
  input = re.sub('[\\\']', '\'', input)
  
  return input

# @app.route('/page/', methods=['GET'])
def page():
  URL = "https://en.wikipedia.org/wiki/Ancient_Greek_philosophy"
  page = requests.get(URL)
  soup = BeautifulSoup(page.content, "lxml")

  page_tags = []

  title = soup.find(id="firstHeading").get_text()
  body_text = soup.find(id="mw-content-text")#.get_text()
  
  # toc is the table of contents, this finds the p tags before the toc in reverse order
  for sibling in soup.find(id="toc").previous_siblings:
    if sibling.name == "p":
      # remove all inner tags (eg. <p><a href="#">Link</a><p> becomes "Link")
      inner_text = remove_refs(sibling.text.strip())
      
      # add the tag plus its text in reverse order to page_tags
      page_tags.insert(0, [sibling.name, inner_text])

  
  print(page_tags)


if __name__ == '__main__':
  # app.run()
  page()