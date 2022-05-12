from bs4 import BeautifulSoup
from flask import Flask
from flask import Flask, jsonify
from flask_cors import CORS
import requests
import urllib.parse
import re

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

def remove_refs(input):
  # remove references in square brackets such as [1]
  input = re.sub('[\[0-9\]]', '', input)
  
  # remove the escape backslash before a single quote
  input = re.sub('[\\\']', '\'', input)

  return input

@app.route('/page/<title>', methods=['GET'])
def page(title):
  URL = "https://en.wikipedia.org/wiki/%s" % title
  page = requests.get(URL)
  soup = BeautifulSoup(page.content, "lxml")

  page_tags = []

  title = soup.find(id="firstHeading").get_text()
  body_text = soup.find(id="mw-content-text")
  
  # toc is the table of contents, this finds the p tags before the toc in reverse order
  for sibling in soup.find(id="toc").previous_siblings:
    if sibling.name == "p":
      # remove all inner tags (eg. <p><a href="#">Link</a><p> becomes "Link")
      inner_text = remove_refs(sibling.text.strip())
      
      # add the tag plus its text in reverse order to page_tags
      page_tags.insert(0, [sibling.name, inner_text])

  # for all remaining p, h2, h3, h4 and ul tags after the table of contents
  for tag in soup.find(id="toc").next_siblings:
    if tag.name == "p" or tag.name == "h2" or tag.name == "h3" or tag.name == "h4":
      inner_text = remove_refs(tag.text.strip())

      # the last 4 chars of h2, h3 and h4 tags are typically "edit"
      if inner_text[-4:] == "edit":
        inner_text = inner_text[:-4]

      # The article should end at either the "See also" or "Notes" headings, not all articles have both
      if inner_text == "See also" or inner_text == "Notes":
        break

      page_tags.append([tag.name, inner_text])

    if tag.name == "ul":
      ul_contents = []
      for li_tag in tag:
        li_tag = li_tag.text.strip()
        if len(li_tag) != 0:
          ul_contents.append(li_tag)
      # if a ul tag is immediate followed by another ul tag, the second ul is typically a visual object
      if page_tags[-1][0] != "ul":    
        page_tags.append([tag.name, ul_contents])

  return jsonify({"title": title, "body": page_tags})



if __name__ == '__main__':
  app.run()