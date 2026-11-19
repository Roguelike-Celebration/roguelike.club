# Loads all JSON files in the current directory and spits out HTML for the website
# 
# The intention is to just write raw HTML that is copy/pasted into the appropriate obelisk.year.html file.
# Note that any "special" inputs (like some lovely ASCII art) is easier (for me) to manage just by manually 
# adding <pre class="camo">...</pre> tags to it (the camo hids the pre block and preserves the ascii formatting)

import os, sys, json
import html, re
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--path', help="Path to JSON files", default=".")

# format links and fix up raw user-submitted text 
URL_PATTERN = re.compile(r"https?://[^\s<>\"]*[^\s<>\".,;:!?)\]'’”]")
def message_to_html(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    out, pos = [], 0
    for m in URL_PATTERN.finditer(text):
        out.append(html.escape(text[pos:m.start()]))
        url = html.escape(m.group(), quote=True)
        out.append(f'<a href="{url}">{url}</a>')
        pos = m.end()
    out.append(html.escape(text[pos:]))
    return "<div>" + "".join(out).replace("\n", "<br>\n") + "</div>"

if __name__ == "__main__":
    args = parser.parse_args()

    # iterate over ALL json files in directory
    for root, dirs, files in os.walk(args.path):
        for file in files:
            if file.endswith(".json"):
                p = os.path.join(root, file)
                with open(p) as f:
                    print(f"Parsing {p}")

                    # load json, order by upvotes, and write the output to an HTML file
                    js = json.load(f)
                    with open(os.path.join(root, file + ".html"), "w") as html_file:
                        obelisk_data = []
                        for post in js:
                            upvotes = 0
                            if 'likes' in post: upvotes = len(post['likes'])
                            obelisk_data.append({'upvotes': upvotes, 'id': post['id'], 'author': post['authorUsername'], 'msg': message_to_html(post['message'])})

                        sorted_data = sorted(obelisk_data, key=lambda d: d['upvotes'], reverse=True)

                        for post in sorted_data:
                            html_out = f"<article><p>{post['msg']}<p><span>&raquo; {post['author']} [{post['upvotes']} upvotes]</span></article>"
                            html_file.write(f"{html_out}\n")


#      original obelisk HTML:
#      const article = document.createElement("article");
#      const contents = document.createElement("p");
#      const authorElement = document.createElement("span");
#      authorElement.innerHTML = author;
#      contents.innerHTML = parseLinks(message);
#      contents.appendChild(document.createElement("br"));
#      contents.appendChild(authorElement);
#      article.appendChild(contents);
#      document.getElementsByTagName("body")[0].appendChild(article);