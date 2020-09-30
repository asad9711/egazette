from xml.sax import saxutils

class Abby:
    def __init__(self, outhandle):
        self.outhandle = outhandle
        self.height    = 0
        self.width     = 0

    def write_header(self):
        self.outhandle.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
        self.outhandle.write('<document xmlns="http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml" version="1.0" producer="ABBYY FineReader Engine 11" languages="" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml">\n<documentData>\n<paragraphStyles>\n</paragraphStyles>\n</documentData>\n')

    def write_footer(self):
        self.outhandle.write('</document>\n')

    def write_page_header(self, height, width, dpi):
        if height == None:
            height = self.height
        
        if width == None:
            width = self.width

        self.outhandle.write('<page width="%d" height="%d" resolution="%d" originalCoords="1">\n' % (width, height, dpi))

    def write_page_footer(self):
        self.outhandle.write('</page>\n')

    def write_word(self, word):
        for symbol in word.symbols:
            self.write_symbol(symbol)


    def write_symbol(self, symbol): 
        box = symbol.bounding_box
        l = box.vertices[0].x
        t = box.vertices[0].y
        r = box.vertices[1].x
        b = box.vertices[2].y
        self.outhandle.write('<charParams l="%d" t="%d" r="%d" b="%d">%s</charParams>\n' % (l, t, r, b, saxutils.escape(symbol.text)))


    def stitch_words(self, words):
        lines    = []
        wordlist = []
        prevbox  = None

        for word in words:
            box = word.bounding_box
            if prevbox == None or not self.is_same_line(prevbox, box):
                if wordlist:
                    lines.append(wordlist)
                wordlist = []

            wordlist.append(word)

            prevbox = box

        if wordlist:
            lines.append(wordlist)

        return lines 

    def write_line_header(self, line):
        l = t = r = b  = None
        
        baselinedict = {}
        for word in line:
            box = word.bounding_box

            box_l = box.vertices[0].x
            box_r = box.vertices[1].x
            box_t = box.vertices[0].y
            box_b = box.vertices[3].y

            if l == None or l > box_l:
                l = box_l

            if r == None or r < box_r:
                r = box_r

            if t == None or t > box_t:
                t = box_t

            if b == None or b < box_b:
                b = box_b
            
            if box_b in baselinedict:
                baselinedict[box_b] += 1
            else:    
                baselinedict[box_b] = 1


        baselines = list(baselinedict.keys())
        baselines.sort( key = lambda x: baselinedict[x], reverse = True)
        baseline = baselines[0]
        self.outhandle.write('<line baseline="%d" l="%d" t="%d" r="%d" b="%d">\n<formatting>\n' % (baseline, l, t, r, b))    
       
    def handle_words(self, words):
        lines = self.stitch_words(words)

        for line in lines:
            self.write_line_header(line)

            prevbox = None
            for word in line:
                box = word.bounding_box

                if prevbox != None:
                    self.write_space(prevbox, box)
                self.write_word(word)

                prevbox = box
            self.outhandle.write('</formatting>\n</line>\n')

    def write_space(self, prevbox, box):
        l = prevbox.vertices[1].x + 1
        r = box.vertices[0].x - 1
        t = prevbox.vertices[0].y
        b = box.vertices[3].y

        if l >= r:
            return

        self.outhandle.write('<charParams l="%d" t="%d" r="%d" b="%d"> </charParams>\n' % (l, t, r, b))

    def write_block_header(self, box):
        l = box.vertices[0].x
        t = box.vertices[0].y
        r = box.vertices[1].x
        b = box.vertices[2].y
        self.outhandle.write('<block blockType="Text" blockName="" l="%d" t="%d" r="%d" b="%d">\n' % (l, t, r, b))
        self.outhandle.write('<region><rect l="%d" t="%d" r="%d" b="%d"/></region>\n<text>\n' % (l, t, r, b))

    def handle_google_response(self, response, ppi):
        for page in response.full_text_annotation.pages:
            self.write_page_header(page.height, page.width, ppi)
            if page.height > self.height:
                self.height = page.height

            if page.width > self.width:
                self.width = page.width

            for block in page.blocks:
                self.write_block_header(block.bounding_box)
                for paragraph in block.paragraphs:
                    self.outhandle.write('<par>\n')
                    self.handle_words(paragraph.words)
                    self.outhandle.write('</par>\n')

                self.outhandle.write('</text>\n</block>\n')
            self.write_page_footer()


    def is_same_line(self, box1, box2):
        ydiff = box2.vertices[3].y - box2.vertices[0].y
        if ydiff <= 0:
            return True

        numy  = round((box2.vertices[0].y - box1.vertices[0].y) * 1.0/ydiff)

        xdiff =  round(box2.vertices[0].x - box1.vertices[2].x)
        numy = int(numy)
        if numy >= 1 or xdiff <= -50:
            return False
        return True

