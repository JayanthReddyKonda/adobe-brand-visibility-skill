"""
vdom.py - Zero-Dependency Virtual DOM Engine
Builds a headless-browser equivalent AST (Abstract Syntax Tree) from raw HTML.
Allows advanced semantic querying (e.g., node.find_all("article")) without Regex or streaming state machines.
"""
from html.parser import HTMLParser

class VNode:
    def __init__(self, tag, attrs=None, parent=None):
        self.tag = tag
        self.attrs = attrs or {}
        self.children = []
        self.text = []
        self.parent = parent
        
    def get_text(self):
        t = " ".join(self.text)
        for c in self.children:
            t += " " + c.get_text()
        return " ".join(t.split())
        
    def find_all(self, tag):
        results = []
        if self.tag == tag:
            results.append(self)
        for c in self.children:
            results.extend(c.find_all(tag))
        return results

    def find_by_class(self, class_name):
        results = []
        classes = self.attrs.get("class", "").split()
        if class_name in classes:
            results.append(self)
        for c in self.children:
            results.extend(c.find_by_class(class_name))
        return results

class VirtualDOMParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = VNode("document")
        self.stack = [self.root]
        self.void_elements = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
        
    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        node = VNode(tag_lower, dict(attrs), parent=self.stack[-1])
        self.stack[-1].children.append(node)
        if tag_lower not in self.void_elements:
            self.stack.append(node)
            
    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower not in self.void_elements:
            # Pop until we find the matching tag (handles unclosed tags gracefully)
            for i in range(len(self.stack)-1, 0, -1):
                if self.stack[i].tag == tag_lower:
                    self.stack = self.stack[:i]
                    break
                    
    def handle_data(self, data):
        text = data.strip()
        if text and len(self.stack) > 0:
            self.stack[-1].text.append(text)

def parse_to_vdom(html):
    parser = VirtualDOMParser()
    try:
        parser.feed(html)
    except Exception:
        pass
    return parser.root
