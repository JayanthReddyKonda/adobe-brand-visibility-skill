from html.parser import HTMLParser

class UnifiedDOMParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.json_ld_contents = []
        self.meta_robots = None
        self.canonical = None
        self.title = ""
        self.og_tags = {}
        self.headings = []
        self.visible_text = []
        self.script_srcs = []
        
        self.in_json_ld = False
        self.in_title = False
        self.current_heading = None
        
        # Track elements that block visible text
        self.ignore_tags = {'script', 'style', 'noscript', 'head', 'meta', 'link'}
        self.current_tag = None

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        attrs_dict = dict(attrs)
        
        if tag == "script":
            if attrs_dict.get("type") == "application/ld+json":
                self.in_json_ld = True
            elif "src" in attrs_dict:
                self.script_srcs.append(attrs_dict["src"])
        elif tag == "meta":
            name = attrs_dict.get("name", "").lower()
            prop = attrs_dict.get("property", "").lower()
            if name == "robots":
                self.meta_robots = attrs_dict.get("content", "")
            elif prop.startswith("og:"):
                self.og_tags[prop] = attrs_dict.get("content", "")
        elif tag == "link":
            if attrs_dict.get("rel") == "canonical":
                self.canonical = attrs_dict.get("href")
        elif tag == "title":
            self.in_title = True
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.current_heading = {"level": int(tag[1]), "text": ""}

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_json_ld = False
        elif tag == "title":
            self.in_title = False
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            if self.current_heading:
                self.current_heading["text"] = self.current_heading["text"].strip()
                self.headings.append(self.current_heading)
                self.current_heading = None
        self.current_tag = None

    def handle_data(self, data):
        if self.in_json_ld:
            self.json_ld_contents.append(data)
        elif self.in_title:
            self.title += data
        elif self.current_heading:
            self.current_heading["text"] += data
            
        if self.current_tag not in self.ignore_tags and data.strip():
            self.visible_text.append(data.strip())
            
    def get_visible_words_count(self) -> int:
        return sum(len(t.split()) for t in self.visible_text)

