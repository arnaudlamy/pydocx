from abc import abstractmethod, ABCMeta
import zipfile
import logging
from contextlib import contextmanager
import xml.etree.ElementTree as ElementTree
from xml.etree.ElementTree import _ElementInterface
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("NewParser")


# http://openxmldeveloper.org/discussions/formats/f/15/p/396/933.aspx
EMUS_PER_PIXEL = 9525


def remove_namespaces(document):  # remove namespaces
    root = ElementTree.fromstring(document)
    for child in el_iter(root):
        child.tag = child.tag.split("}")[1]
        child.attrib = dict(
            (k.split("}")[-1], v)
            for k, v in child.attrib.items()
        )
    return ElementTree.tostring(root)

# Add some helper functions to Element to make it slightly more readable


# determine if current element has a child. stop at first child.
def has_child(self, tag):
    return True if self.find(tag) is not None else False


# determine if there is a child ahead in the element tree.
def has_child_deep(self, tag):
# get child. stop at first child.
    return True if self.find('.//' + tag) is not None else False


# find the first occurrence of a tag beneath the current element
def find_first(self, tag):
    return self.find('.//' + tag)


def find_all(self, tag):  # find all occurrences of a tag
    return self.findall('.//' + tag)


def find_next(self, tag, count):
    if self.find_all(tag)[-1] == self.find_all(tag)[count]:
        return None
    else:
        return self.find_all(tag)[count + 1]


def el_iter(el):  # go through all elements
    try:
        return el.iter()
    except AttributeError:
        return el.findall('.//*')


def find_parent_by_tag(self, tag):
    el = self
    while el.parent:
        el = el.parent
        if el.tag == tag:
            return el
    return None


#make all of these attributes of _ElementInterface
setattr(_ElementInterface, 'has_child', has_child)
setattr(_ElementInterface, 'has_child_deep', has_child_deep)
setattr(_ElementInterface, 'find_first', find_first)
setattr(_ElementInterface, 'find_all', find_all)
setattr(_ElementInterface, 'find_parent_by_tag', find_parent_by_tag)
setattr(_ElementInterface, 'parent', None)
setattr(_ElementInterface, 'is_first_list_item', False)
setattr(_ElementInterface, 'is_last_list_item', False)
setattr(_ElementInterface, 'is_list_item', False)
setattr(_ElementInterface, 'ilvl', None)
setattr(_ElementInterface, 'num_id', None)
setattr(_ElementInterface, 'next', None)
setattr(_ElementInterface, 'find_next', find_next)


# End helpers

@contextmanager
def ZipFile(path):  # This is not needed in python 3.2+
    f = zipfile.ZipFile(path)
    yield f
    f.close()


class DocxParser:
    __metaclass__ = ABCMeta

    def _build_data(self, path, *args, **kwargs):
        with ZipFile(path) as f:
            self.document_text = f.read('word/document.xml')
            try:  # Only present if there are lists
                self.numbering_text = f.read('word/numbering.xml')
            except KeyError:
                self.numbering_text = None
            try:  # Only present if there are comments
                self.comment_text = f.read('word/comments.xml')
            except KeyError:
                self.comment_text = None
            self.relationship_text = f.read('word/_rels/document.xml.rels')

        self.root = ElementTree.fromstring(
            remove_namespaces(self.document_text),  # remove the namespaces
        )
        self.numbering_root = None
        if self.numbering_text:
            self.numbering_root = ElementTree.fromstring(
                remove_namespaces(self.numbering_text),
            )
        self.comment_root = None
        if self.comment_text:
            self.comment_root = ElementTree.fromstring(
                remove_namespaces(self.comment_text),
            )

    def _parse_rels_root(self):
        tree = ElementTree.fromstring(self.relationship_text)
        rels_dict = {}
        for el in tree:
            rId = el.get('Id')
            target = el.get('Target')
            rels_dict[rId] = target
        return rels_dict

    def __init__(self, *args, **kwargs):
        self._parsed = ''

        self._build_data(*args, **kwargs)

        def add_parent(el):  # if a parent, make that an attribute
            for child in el.getchildren():
                setattr(child, 'parent', el)
                add_parent(child)

        add_parent(self.root)  # create the parent attributes

        #all blank when we init
        self.comment_store = None
        self.visited = []
        self.visited_els = []
        self.count = 0
        self.list_depth = 0
        self.rels_dict = self._parse_rels_root()
        self.parse_begin(self.root)  # begin to parse

    def _set_list_attributes(self, el):
        list_elements = el.find_all('numId')
        for li in list_elements:
            parent = li.find_parent_by_tag('p')
            parent.is_list_item = True
            parent.num_id = parent.find_first('numId').attrib['val']
            parent.ilvl = parent.find_first('ilvl').attrib['val']

    def parse_begin(self, el):
        self._set_list_attributes(el)

        # Find the first and last li elements
        body = el.find_first('body')
        list_elements = [
            child for child in body.getchildren()
            if child.tag == 'p' and child.is_list_item
        ]
        num_ids = set([i.num_id for i in list_elements])
        ilvls = set([i.ilvl for i in list_elements])

        # Find first list elements. Mark all first list elements regardless of
        # where they occur at.
        for num_id in num_ids:
            for ilvl in ilvls:
                filtered_list_elements = [
                    i for i in list_elements
                    if (
                        i.num_id == num_id and
                        i.ilvl == ilvl)
                ]
                if not filtered_list_elements:
                    continue
                first_el = filtered_list_elements[0]
                first_el.is_first_list_item = True
        # Find last list elements. Only mark list tags as the last list tag if
        # it is in the root of the document.
        for num_id in num_ids:
            filtered_list_elements = [
                i for i in list_elements
                if i.num_id == num_id
            ]
            if not filtered_list_elements:
                continue
            last_el = filtered_list_elements[-1]
            last_el.is_last_list_item = True

        # We only care about children if they have text in them.
        children = [
            child for child in body.getchildren()
            if child.tag in ['p', 'tbl'] and
            child.has_child_deep('t')
        ]
        for i in range(len(children)):
            try:
                if children[i + 1]:
                    children[i].next = children[i + 1]
            except IndexError:
                pass

        self._parsed += self.parse(el)

    def parse(self, el):
        if el in self.visited:
            return ''
        self.visited.append(el)
        parsed = ''
        for child in el:
            # recursive. So you can get all the way to the bottom
            parsed += self.parse(child)

        if el.is_first_list_item:
            return self.parse_list(el, parsed)
        if el.tag == 'br' and el.attrib.get('type') == 'page':
            #TODO figure out what parsed is getting overwritten
            return self.page_break()
        # Do not do the tr or tc a second time
        if el.tag == 'tbl':
            return self.table(parsed)
        elif el.tag == 'tr':  # table rows
            return self.table_row(parsed)
        elif el.tag == 'tc':  # table cells
            return self.table_cell(parsed)
        if el.tag == 'r' and el:
            return self.parse_r(el)  # parse the run
        elif el.tag == 'p':
            if el.parent.tag == 'tc':
                if (
                        el.parent.find_next('p', self.count) is not None and
                        not len(el.parent.find_all('tc')) > 0):
                    parsed += self.break_tag()
                    self.count += 1
                    self.visited_els.append(el)
                else:
                    self.count = 0
                return parsed  # return text in the table cell
                # parse p. parse p will return a list element or a paragraph
            return self.parse_p(el, parsed)
        elif el.tag == 'ins':
            return self.insertion(parsed, '', '')
        elif el.tag == 'hyperlink':
            return self.parse_hyperlink(el, parsed)
        else:
            return parsed

    def parse_list(self, el, text):
        self.list_depth += 1
        parsed = self.parse_p(el, text)
        num_id = el.num_id
        ilvl = el.ilvl
        next_el = el.next

        def continue_loop(next_el, num_id, ilvl):
            # Bail if next_el is not an element
            if next_el is None:
                return False
            if next_el.is_last_list_item:
                return False
            # If next_el is not a list item then roll it into the list by
            # returning True.
            if not next_el.is_list_item:
                return True
            # If the num ids are the same and the new ilvl is the same or
            # larger than the previous return True, else False.
            return next_el.num_id == num_id and next_el.ilvl >= ilvl

        while continue_loop(next_el, num_id, ilvl):
            if next_el in self.visited:
                # Early continue for elements we have already visited.
                next_el = next_el.next
                continue

            current_num_id = None
            if next_el.is_list_item:
                # Reset the num_id and the ilvl
                current_num_id = next_el.num_id
                ilvl = next_el.ilvl

            # Check to see if we need to break out of this loop.
            if current_num_id != num_id:
                break
            parsed += self.parse(next_el)
            next_el = next_el.next

        def _parse_last_el(last_el, first_el):
            if last_el is None:
                return False
            if last_el.num_id != first_el.num_id:
                return False
            if last_el.ilvl != first_el.ilvl:
                return False
            return not last_el.is_first_list_item and last_el.is_last_list_item
        if _parse_last_el(next_el, el):
            parsed += self.parse(next_el)

        # Get the list style for the pending list.
        lst_style = self.get_list_style(
            el.num_id,
            el.ilvl,
        )

        self.list_depth -= 1
        # Create the actual list and return it.
        if lst_style == 'bullet' and parsed != '':
            return self.unordered_list(parsed)
        elif lst_style and parsed != '':
            return self.ordered_list(
                parsed,
                lst_style,
            )

    def parse_p(self, el, text):
        if text == '':
            return ''
        parsed = text
        if not el.is_list_item:
            # No p tags in li tags
            if self.list_depth == 0:
                parsed = self.paragraph(parsed)
            else:
                # Instead break separate
                parsed = self.break_tag() + parsed
            return parsed

        # If for whatever reason we are not currently in a list, then start
        # a list here.
        if self.list_depth == 0:
            return self.parse_list(el, parsed)
        next_el_parsed = ''
        if el.next is not None:
            def _parse_next_element_first(el):
                next_el = el.next
                if not next_el.is_list_item and not el.is_last_list_item:
                    return True
                if next_el.is_first_list_item:
                    if next_el.num_id == el.num_id:
                        return True
                return False

            if _parse_next_element_first(el):
                # Get the contents of the next el and append it to the
                # contents of the current el (that way things like tables
                # are actually in the li tag instead of in the ol/ul tag).
                next_el_parsed = self.parse(el.next)
        # Create the actual li element
        parsed = self.list_element(
            parsed + next_el_parsed,
        )
        return parsed

    def parse_hyperlink(self, el, text):
        rId = el.get('id')
        href = self.rels_dict.get(rId)
        if not href:
            return text
        href = self.escape(href)
        return self.hyperlink(text, href)

    def _get_image_id(self, el):
        # Drawings
        blip = el.find_first('blip')
        if blip is not None:
            # On drawing tags the id is actually whatever is returned from the
            # embed attribute on the blip tag. Thanks a lot Microsoft.
            return blip.get('embed')
        # Picts
        imagedata = el.find_first('imagedata')
        if imagedata is not None:
            return imagedata.get('id')

    def _convert_image_size(self, size):
        return size / EMUS_PER_PIXEL

    def _get_image_size(self, el):
        """
        If we can't find a height or width, return 0 for whichever is not
        found, then rely on the `image` handler to strip those attributes. This
        functionality can change once we integrate PIL.
        """
        sizes = el.find_first('ext')
        if sizes is not None:
            x = self._convert_image_size(int(sizes.get('cx')))
            y = self._convert_image_size(int(sizes.get('cy')))
            return (
                '%dpx' % x,
                '%dpx' % y,
            )
        shape = el.find_first('shape')
        if shape is not None:
            # If either of these are not set, rely on the method `image` to not
            # use either of them.
            x = 0
            y = 0
            styles = shape.get('style').split(';')
            for s in styles:
                if s.startswith('height:'):
                    y = s.split(':')[1]
                if s.startswith('width:'):
                    x = s.split(':')[1]
            return x, y
        return 0, 0

    def parse_image(self, el):
        x, y = self._get_image_size(el)
        rId = self._get_image_id(el)
        src = self.rels_dict.get(rId)
        if not src:
            return ''
        src = self.escape(src)
        return self.image(src, x, y)

    def _is_style_on(self, el):
        """
        For b, i, u (bold, italics, and underline) merely having the tag is not
        sufficient. You need to check to make sure it is not set to "false" as
        well.
        """
        return el.get('val') != 'false'

    def parse_r(self, el):  # parse the running text
        is_deleted = False
        text = ''
        count = 0
        for element in el:
            if element.tag == 't' and el not in self.visited_els:
                text += self.escape(el.find('t').text)
                self.visited_els.append(el)
            elif element.tag == 'delText':  # get the deleted text
                text += self.escape(el.find('delText').text)
                is_deleted = True
            elif element.tag in ('pict', 'drawing'):
                text += self.parse_image(element)
            elif element.tag == 'br':
                text += self.break_tag()
                if len(el.parent.find_all('t')) > 0:
                    text += self.escape(el.parent.find_next('t', count).text)
                count += 1
        if text:
            rpr = el.find('rPr')
            if rpr is not None:
                fns = []
                if rpr.has_child('b'):  # text styling
                    if self._is_style_on(rpr.find('b')):
                        fns.append(self.bold)
                if rpr.has_child('i'):
                    if self._is_style_on(rpr.find('i')):
                        fns.append(self.italics)
                if rpr.has_child('u'):
                    if self._is_style_on(rpr.find('u')):
                        fns.append(self.underline)
                for fn in fns:
                    text = fn(text)
            ppr = el.parent.find('pPr')
            if ppr is not None:
                jc = ppr.find('jc')
                if jc is not None:  # text alignments
                    if jc.attrib['val'] == 'right':
                        text = self.right_justify(text)
                    if jc.attrib['val'] == 'center':
                        text = self.center_justify(text)
                ind = ppr.find('ind')
                if ind is not None:
                    right = None
                    left = None
                    firstLine = None
                    if 'right' in ind.attrib:
                        right = ind.attrib['right']
                        right = int(right)/20
                        right = str(right)
                    if 'left' in ind.attrib:
                        left = ind.attrib['left']
                        left = int(left)/20
                        left = str(left)
                    if 'firstLine' in ind.attrib:
                        firstLine = ind.attrib['firstLine']
                        firstLine = int(firstLine)/20
                        firstLine = str(firstLine)
                    text = self.indent(text, right, left, firstLine)
            if is_deleted:
                text = self.deletion(text, '', '')
            return text
        else:
            return ''

    def get_list_style(self, num_id, ilvl):
        ids = self.numbering_root.find_all('num')
        for _id in ids:
            if _id.attrib['numId'] != num_id:
                continue
            abstractid = _id.find('abstractNumId')
            abstractid = abstractid.attrib['val']
            style_information = self.numbering_root.find_all(
                'abstractNum',
            )
            for info in style_information:
                if info.attrib['abstractNumId'] == abstractid:
                    for i in el_iter(info):
                        if 'ilvl' in i.attrib and i.attrib['ilvl'] != ilvl:
                            continue
                        if i.find('numFmt') is not None:
                            return i.find('numFmt').attrib['val']

    def get_comments(self, doc_id):
        if self.comment_root is None:
            return ''
        if self.comment_store is not None:
            return self.comment_store[doc_id]
        ids_and_info = {}
        ids = self.comment_root.find_all('comment')
        for _id in ids:
            ids_and_info[_id.attrib['id']] = {
                "author": _id.attrib['author'],
                "date": _id.attrib['date'],
                "text": _id.find_all('t')[0].text,
            }
        self.comment_store = ids_and_info
        return self.comment_store[doc_id]

    @property
    def parsed(self):
        return self._parsed

    @property
    def escape(self, text):
        return text

    @abstractmethod
    def linebreak(self):
        return ''

    @abstractmethod
    def paragraph(self, text):
        return text

    @abstractmethod
    def insertion(self, text, author, date):
        return text

    @abstractmethod
    def hyperlink(self, text, href):
        return text

    @abstractmethod
    def image_handler(self, path):
        return path

    @abstractmethod
    def image(self, path, x, y):
        return self.image_handler(path)

    @abstractmethod
    def deletion(self, text, author, date):
        return text

    @abstractmethod
    def bold(self, text):
        return text

    @abstractmethod
    def italics(self, text):
        return text

    @abstractmethod
    def underline(self, text):
        return text

    @abstractmethod
    def tab(self):
        return True

    @abstractmethod
    def ordered_list(self, text):
        return text

    @abstractmethod
    def unordered_list(self, text):
        return text

    @abstractmethod
    def list_element(self, text):
        return text

    @abstractmethod
    def table(self, text):
        return text

    @abstractmethod
    def table_row(self, text):
        return text

    @abstractmethod
    def table_cell(self, text):
        return text

    @abstractmethod
    def page_break(self):
        return True

    @abstractmethod
    def right_justify(self, text):
        return text

    @abstractmethod
    def center_justify(self, text):
        return text

    @abstractmethod
    def indent(self, text, left=None, right=None, firstLine=None):
        return text        # TODO JUSTIFIED JUSTIFIED TEXT
