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
  input = re.sub('\[[0-9]+\]', '', input)
  
  # remove single characters in square brackets such as [b]
  input = re.sub('\[[a-z]\]', '', input)
  
  # remove the escape backslash before a single quote
  input = re.sub('[\\\']', '\'', input)

  return input

@app.route('/page/<title>', methods=['GET'])
def page(title):
  URL = "https://en.wikipedia.org/wiki/%s" % title
  page = requests.get(URL)
  soup = BeautifulSoup(page.content, "lxml")

  # page_tags will hold all tags and their text content
  page_tags = []

  title = soup.find(id="firstHeading").get_text()
  body_text = soup.find(id="mw-content-text")
  
  # toc is the table of contents, this finds the p tags before the toc in reverse order
  for sibling in soup.find(id="toc").previous_siblings:
    if sibling.name == "p":

      inner_text = sibling.text.strip()

      # strip out all inner tags except italic tags
      for inner_tag in sibling:
        if inner_tag.name == "i":
          inner_tag_text = inner_tag.text.strip()
          # only replace the inner text within the i tags if it has not already been replaced
          if "<i>%s" % inner_tag_text not in inner_text:
            inner_text = inner_text.replace(inner_tag_text, "<i>%s</i>" % inner_tag_text)

      # remove all inner tags (eg. <p><a href="#">Link</a><p> becomes "Link")
      inner_text = remove_refs(sibling.text.strip())
      
      # add the tag plus its text in reverse order to page_tags
      if len(inner_text) != 0:    
        page_tags.insert(0, [sibling.name, inner_text])

  # for all remaining p, h2, h3, h4 and ul tags after the table of contents
  for tag in soup.find(id="toc").next_siblings:
    if tag.name == "p" or tag.name == "h2" or tag.name == "h3" or tag.name == "h4":

      inner_text = tag.text.strip()

      # strip out all inner tags except italic tags
      for inner_tag in tag:
        if inner_tag.name == "i":
          inner_tag_text = inner_tag.text.strip()
          # only replace the inner text within the i tags if it has not already been replaced
          if "<i>%s" % inner_tag_text not in inner_text:
            inner_text = inner_text.replace(inner_tag_text, "<i>%s</i>" % inner_tag_text)

      inner_text = remove_refs(inner_text)

      # the last 4 chars of h2, h3 and h4 tags are typically "edit"
      if inner_text[-4:] == "edit":
        inner_text = inner_text[:-4]

      # The article should end at either the "See also" or "Notes" headings, not all articles have both
      if inner_text == "See also" or inner_text == "Notes":
        break

      if inner_text != "":
        page_tags.append([tag.name, inner_text])

    if tag.name == "ul":
      ul_contents = []
      for li_tag in tag:
        li_tag = li_tag.text.strip()
        if len(li_tag) != 0:
          li_tag = remove_refs(li_tag)
          ul_contents.append(li_tag)

      # if a ul tag is immediate followed by another ul tag, the second ul is typically a visual object
      if len(page_tags) != 0 and page_tags[-1][0] != "ul":    
        page_tags.append([tag.name, ul_contents])

  body_as_words = []
  
  for tag in page_tags:
    txt = tag[1]
    
    # ul tags are of type "list" so need to be split into strings before they can be split into words
    if isinstance(txt, list):
      full_list = []
      for list_instance in txt:
        txt_as_words = re.split('(\W+)', list_instance)
        full_list.append(txt_as_words)
      body_as_words.append([tag[0], full_list])
        
    else:
      # split the text into words "word" "," "word2", ";" etc
      txt_as_words = re.split('(\W+)', txt)
      body_as_words.append([tag[0], txt_as_words])

  return jsonify({"title": title, "body": page_tags, "body_as_words": body_as_words})


if __name__ == '__main__':
  app.run()