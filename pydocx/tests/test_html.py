# coding: utf-8

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
)

from pydocx.tests import (
    DocumentGeneratorTestCase,
    WordprocessingDocumentFactory,
)
from pydocx.wordml import (
    FootnotesPart,
    ImagePart,
    MainDocumentPart,
    StyleDefinitionsPart,
)


class FootnoteTestCase(DocumentGeneratorTestCase):
    def test_footnote_without_definition_is_ignored(self):
        document_xml = '''
            <p>
              <r>
                <t>Foo</t>
              </r>
              <r>
                <footnoteReference id="abc"/>
              </r>
            </p>
        '''
        document = WordprocessingDocumentFactory()
        document.add(MainDocumentPart, document_xml)

        expected_html = '<p>Foo</p>'
        self.assert_document_generates_html(document, expected_html)

    def test_basic_footnote_with_styling(self):
        document_xml = '''
            <p>
              <r>
                <t>Foo</t>
              </r>
              <r>
                <rPr>
                  <vertAlign val="superscript"/>
                </rPr>
                <footnoteReference id="abc"/>
              </r>
            </p>
            <p>
              <r>
                <t>Footnotes should appear below this</t>
              </r>
            </p>
        '''

        footnotes_xml = '''
            <footnote id="abc">
              <p>
                <r>
                  <rPr>
                    <b val="on"/>
                  </rPr>
                  <footnoteRef/>
                  <t>Bar</t>
                </r>
              </p>
            </footnote>
        '''

        document = WordprocessingDocumentFactory()
        document.add(FootnotesPart, footnotes_xml)
        document.add(MainDocumentPart, document_xml)

        expected_html = '''
            <p>
                Foo
                <sup>
                    <a href="#footnote-abc" name="footnote-ref-abc">1</a>
                </sup>
            </p>
            <p>Footnotes should appear below this</p>
            <hr />
            <ol list-style-type="decimal">
                <li><p><strong>
                    <a href="#footnote-ref-abc" name="footnote-abc">^</a>
                    Bar
                </strong></p></li>
            </ol>
        '''
        self.assert_document_generates_html(document, expected_html)

    def test_footnote_with_hyperlink(self):
        document_xml = '''
            <p>
              <r>
                <t>Foo</t>
              </r>
              <r>
                <rPr>
                  <vertAlign val="superscript"/>
                </rPr>
                <footnoteReference id="abc"/>
              </r>
            </p>
            <p>
              <r>
                <t>Footnotes should appear below this</t>
              </r>
            </p>
        '''

        footnotes_xml = '''
            <footnote id="abc">
              <p>
                <r>
                  <footnoteRef/>
                </r>
                <hyperlink id="foobar">
                  <r>
                    <t>Bar</t>
                  </r>
                </hyperlink>
              </p>
            </footnote>
        '''

        document = WordprocessingDocumentFactory()

        footnotes_rels = document.relationship_format.format(
            id='foobar',
            type='foo/hyperlink',
            target='http://google.com',
            target_mode='External',
        )

        document.add(FootnotesPart, footnotes_xml, footnotes_rels)
        document.add(MainDocumentPart, document_xml)

        expected_html = '''
            <p>
                Foo
                <sup>
                    <a href="#footnote-abc" name="footnote-ref-abc">1</a>
                </sup>
            </p>
            <p>Footnotes should appear below this</p>
            <hr />
            <ol list-style-type="decimal">
                <li>
                    <p>
                        <a href="#footnote-ref-abc" name="footnote-abc">^</a>
                        <a href="http://google.com">Bar</a>
                    </p>
                </li>
            </ol>
        '''
        self.assert_document_generates_html(document, expected_html)

    def test_multiple_footnotes_defined_in_a_order_different_from_usage(self):
        document_xml = '''
            <p>
              <r>
                <t>Foo</t>
              </r>
              <r>
                <rPr>
                  <vertAlign val="superscript"/>
                </rPr>
                <footnoteReference id="one"/>
              </r>
              <r>
                <t>Bar</t>
              </r>
              <r>
                <rPr>
                  <vertAlign val="superscript"/>
                </rPr>
                <footnoteReference id="two"/>
              </r>
              <r>
                <t>Baz</t>
              </r>
              <r>
                <rPr>
                  <vertAlign val="superscript"/>
                </rPr>
                <footnoteReference id="three"/>
              </r>
            </p>
            <p>
              <r>
                <t>Footnotes should appear below this</t>
              </r>
            </p>
        '''

        footnotes_xml = '''
            <footnote id="two">
              <p>
                <r>
                  <footnoteRef/>
                  <t>Beta</t>
                </r>
              </p>
            </footnote>
            <footnote id="three">
              <p>
                <r>
                  <footnoteRef/>
                  <t>Gamma</t>
                </r>
              </p>
            </footnote>
            <footnote id="one">
              <p>
                <r>
                  <footnoteRef/>
                  <t>Alpha</t>
                </r>
              </p>
            </footnote>
        '''

        document = WordprocessingDocumentFactory()
        document.add(FootnotesPart, footnotes_xml)
        document.add(MainDocumentPart, document_xml)

        expected_html = '''
            <p>
                Foo
                <sup>
                    <a href="#footnote-one" name="footnote-ref-one">1</a>
                </sup>
                Bar
                <sup>
                    <a href="#footnote-two" name="footnote-ref-two">2</a>
                </sup>
                Baz
                <sup>
                    <a href="#footnote-three" name="footnote-ref-three">3</a>
                </sup>
            </p>
            <p>Footnotes should appear below this</p>
            <hr />
            <ol list-style-type="decimal">
                <li><p>
                    <a href="#footnote-ref-one" name="footnote-one">^</a>
                    Alpha
                </p></li>
                <li><p>
                    <a href="#footnote-ref-two" name="footnote-two">^</a>
                    Beta
                </p></li>
                <li><p>
                    <a href="#footnote-ref-three" name="footnote-three">^</a>
                    Gamma
                </p></li>
            </ol>
        '''
        self.assert_document_generates_html(document, expected_html)


class ParagraphTestCase(DocumentGeneratorTestCase):
    def test_multiple_text_tags_in_a_single_run_tag_create_single_paragraph(
        self,
    ):
        document_xml = '''
            <p>
              <r>
                <t>A</t>
                <t>B</t>
                <t>C</t>
              </r>
            </p>
        '''
        document = WordprocessingDocumentFactory()
        document.add(MainDocumentPart, document_xml)

        expected_html = '<p>ABC</p>'
        self.assert_document_generates_html(document, expected_html)

    def test_empty_text_tag_does_not_create_paragraph(self):
        document_xml = '''
            <p>
              <r>
                <t></t>
              </r>
            </p>
        '''
        document = WordprocessingDocumentFactory()
        document.add(MainDocumentPart, document_xml)

        expected_html = ''
        self.assert_document_generates_html(document, expected_html)

    def test_unicode_character_from_xml_entity(self):
        document_xml = '''
            <p>
              <r>
                <t>&#x10001F;</t>
              </r>
            </p>
        '''
        document = WordprocessingDocumentFactory()
        document.add(MainDocumentPart, document_xml)

        expected_html = '<p>\U0010001f</p>'
        self.assert_document_generates_html(document, expected_html)

    def test_non_entity_unicode_character(self):
        document_xml = '''
            <p>
              <r>
                <t>capacités</t>
              </r>
            </p>
        '''

        document = WordprocessingDocumentFactory()
        document.add(MainDocumentPart, document_xml)

        expected_html = '<p>capacités</p>'
        self.assert_document_generates_html(document, expected_html)


class HeadingTestCase(DocumentGeneratorTestCase):
    def test_character_stylings_are_ignored(self):
        # Even though the heading1 style has bold enabled, it's being ignored
        # because the style is for a header
        style_xml = '''
            <style styleId="heading1" type="paragraph">
              <name val="Heading 1"/>
              <rPr>
                <b val="on"/>
              </rPr>
            </style>
        '''

        document_xml = '''
            <p>
              <pPr>
                <pStyle val="heading1"/>
              </pPr>
              <r>
                <t>aaa</t>
              </r>
            </p>
        '''

        document = WordprocessingDocumentFactory()
        document.add(StyleDefinitionsPart, style_xml)
        document.add(MainDocumentPart, document_xml)

        expected_html = '''
            <h1>aaa</h1>
        '''
        self.assert_document_generates_html(document, expected_html)

    def test_each_heading_level(self):
        style_template = '''
            <style styleId="heading%s" type="paragraph">
              <name val="Heading %s"/>
            </style>
        '''

        style_xml = ''.join(
            style_template % (i, i)
            for i in range(1, 11)
        )

        paragraph_template = '''
            <p>
              <pPr>
                <pStyle val="%s"/>
              </pPr>
              <r>
                <t>%s</t>
              </r>
            </p>
        '''

        style_to_text = [
            ('heading1', 'aaa'),
            ('heading2', 'bbb'),
            ('heading3', 'ccc'),
            ('heading4', 'ddd'),
            ('heading5', 'eee'),
            ('heading6', 'fff'),
            ('heading7', 'ggg'),
            ('heading8', 'hhh'),
            ('heading9', 'iii'),
            ('heading10', 'jjj'),
        ]

        document_xml = ''.join(
            paragraph_template % entry
            for entry in style_to_text
        )

        document = WordprocessingDocumentFactory()
        document.add(StyleDefinitionsPart, style_xml)
        document.add(MainDocumentPart, document_xml)

        expected_html = '''
            <h1>aaa</h1>
            <h2>bbb</h2>
            <h3>ccc</h3>
            <h4>ddd</h4>
            <h5>eee</h5>
            <h6>fff</h6>
            <h6>ggg</h6>
            <h6>hhh</h6>
            <h6>iii</h6>
            <h6>jjj</h6>
        '''
        self.assert_document_generates_html(document, expected_html)


class PageBreakTestCase(DocumentGeneratorTestCase):
    def test_before_text_run(self):
        document_xml = '''
            <p>
              <r>
                <t>aaa</t>
              </r>
            </p>
            <p>
              <r>
                <br type="page"/>
                <t>bbb</t>
              </r>
            </p>
        '''

        document = WordprocessingDocumentFactory()
        document.add(MainDocumentPart, document_xml)

        expected_html = '<p>aaa</p><p><hr />bbb</p>'
        self.assert_document_generates_html(document, expected_html)

    def test_between_paragraphs(self):
        document_xml = '''
            <p>
              <r>
                <t>aaa</t>
              </r>
            </p>
            <p>
              <r>
                <br type="page"/>
              </r>
            </p>
            <p>
              <r>
                <t>bbb</t>
              </r>
            </p>
        '''

        document = WordprocessingDocumentFactory()
        document.add(MainDocumentPart, document_xml)

        expected_html = '<p>aaa</p><p><hr /></p><p>bbb</p>'
        self.assert_document_generates_html(document, expected_html)

    def test_after_text_run(self):
        document_xml = '''
            <p>
              <r>
                <t>aaa</t>
                <br type="page"/>
              </r>
            </p>
            <p>
              <r>
                <t>bbb</t>
              </r>
            </p>
        '''

        document = WordprocessingDocumentFactory()
        document.add(MainDocumentPart, document_xml)

        expected_html = '<p>aaa<hr /></p><p>bbb</p>'
        self.assert_document_generates_html(document, expected_html)


class PropertyHierarchyTestCase(DocumentGeneratorTestCase):
    def test_local_character_style(self):
        document_xml = '''
            <p>
              <r>
                <rPr>
                  <b val="on"/>
                </rPr>
                <t>aaa</t>
              </r>
            </p>
        '''

        document = WordprocessingDocumentFactory()
        document.add(MainDocumentPart, document_xml)

        expected_html = '<p><strong>aaa</strong></p>'
        self.assert_document_generates_html(document, expected_html)

    def test_global_run_character_style(self):
        style_xml = '''
            <style styleId="foo" type="character">
              <rPr>
                <b val="on"/>
              </rPr>
            </style>
        '''

        document_xml = '''
            <p>
              <r>
                <rPr>
                  <rStyle val="foo"/>
                </rPr>
                <t>aaa</t>
              </r>
            </p>
        '''

        document = WordprocessingDocumentFactory()
        document.add(StyleDefinitionsPart, style_xml)
        document.add(MainDocumentPart, document_xml)

        expected_html = '<p><strong>aaa</strong></p>'
        self.assert_document_generates_html(document, expected_html)

    def test_global_run_paragraph_style(self):
        style_xml = '''
            <style styleId="foo" type="paragraph">
              <rPr>
                <b val="on"/>
              </rPr>
            </style>
        '''

        document_xml = '''
            <p>
              <pPr>
                <pStyle val="foo"/>
              </pPr>
              <r>
                <t>aaa</t>
              </r>
            </p>
        '''

        document = WordprocessingDocumentFactory()
        document.add(StyleDefinitionsPart, style_xml)
        document.add(MainDocumentPart, document_xml)

        expected_html = '<p><strong>aaa</strong></p>'
        self.assert_document_generates_html(document, expected_html)

    def test_global_run_paragraph_and_character_styles(self):
        style_xml = '''
            <style styleId="foo" type="paragraph">
              <rPr>
                <b val="on"/>
              </rPr>
            </style>
            <style styleId="bar" type="character">
              <rPr>
                <i val="on"/>
              </rPr>
            </style>
        '''

        document_xml = '''
            <p>
              <pPr>
                <pStyle val="foo"/>
              </pPr>
              <r>
                <rPr>
                  <rStyle val="bar"/>
                </rPr>
                <t>aaa</t>
              </r>
            </p>
        '''

        document = WordprocessingDocumentFactory()
        document.add(StyleDefinitionsPart, style_xml)
        document.add(MainDocumentPart, document_xml)

        expected_html = '<p><em><strong>aaa</strong></em></p>'
        self.assert_document_generates_html(document, expected_html)

    def test_local_styles_override_global_styles(self):
        style_xml = '''
            <style styleId="foo" type="paragraph">
              <rPr>
                <b val="on"/>
              </rPr>
            </style>
            <style styleId="bar" type="character">
              <rPr>
                <i val="on"/>
              </rPr>
            </style>
        '''

        document_xml = '''
            <p>
              <pPr>
                <pStyle val="foo"/>
              </pPr>
              <r>
                <rPr>
                  <rStyle val="bar"/>
                  <b val="off"/>
                  <i val="off"/>
                </rPr>
                <t>aaa</t>
              </r>
            </p>
        '''

        document = WordprocessingDocumentFactory()
        document.add(StyleDefinitionsPart, style_xml)
        document.add(MainDocumentPart, document_xml)

        expected_html = '<p>aaa</p>'
        self.assert_document_generates_html(document, expected_html)

    def test_paragraph_style_referenced_by_run_is_ignored(self):
        style_xml = '''
            <style styleId="foo" type="paragraph">
              <rPr>
                <b val="on"/>
              </rPr>
            </style>
        '''

        document_xml = '''
            <p>
              <r>
                <rPr>
                  <rStyle val="foo"/>
                </rPr>
                <t>aaa</t>
              </r>
            </p>
        '''

        document = WordprocessingDocumentFactory()
        document.add(StyleDefinitionsPart, style_xml)
        document.add(MainDocumentPart, document_xml)

        expected_html = '<p>aaa</p>'
        self.assert_document_generates_html(document, expected_html)

    def test_character_style_referenced_by_paragraph_is_ignored(self):
        style_xml = '''
            <style styleId="foo" type="character">
              <rPr>
                <b val="on"/>
              </rPr>
            </style>
        '''

        document_xml = '''
            <p>
              <pPr>
                <pStyle val="foo"/>
              </pPr>
              <r>
                <t>aaa</t>
              </r>
            </p>
        '''

        document = WordprocessingDocumentFactory()
        document.add(StyleDefinitionsPart, style_xml)
        document.add(MainDocumentPart, document_xml)

        expected_html = '<p>aaa</p>'
        self.assert_document_generates_html(document, expected_html)

    def test_run_paragraph_mark_style_is_not_used_as_run_style(self):
        style_xml = '''
            <style styleId="foo" type="paragraph">
              <pPr>
                <rPr>
                  <b val="on"/>
                </rPr>
              </pPr>
            </style>
        '''

        document_xml = '''
            <p>
              <pPr>
                <pStyle val="foo"/>
              </pPr>
              <r>
                <t>aaa</t>
              </r>
            </p>
        '''

        document = WordprocessingDocumentFactory()
        document.add(StyleDefinitionsPart, style_xml)
        document.add(MainDocumentPart, document_xml)

        expected_html = '<p>aaa</p>'
        self.assert_document_generates_html(document, expected_html)


class StyleBasedOnTestCase(DocumentGeneratorTestCase):
    def test_style_chain_ends_when_loop_is_detected(self):
        style_xml = '''
            <style styleId="one">
              <basedOn val="three"/>
              <rPr>
                <b val="on"/>
              </rPr>
            </style>
            <style styleId="two">
              <basedOn val="one"/>
            </style>
            <style styleId="three">
              <basedOn val="two"/>
            </style>
        '''

        document_xml = '''
            <p>
              <pPr>
                <pStyle val="three"/>
              </pPr>
              <r>
                <t>aaa</t>
              </r>
            </p>
        '''

        document = WordprocessingDocumentFactory()
        document.add(StyleDefinitionsPart, style_xml)
        document.add(MainDocumentPart, document_xml)

        expected_html = '<p><strong>aaa</strong></p>'
        self.assert_document_generates_html(document, expected_html)

    def test_styles_are_inherited(self):
        style_xml = '''
            <style styleId="one">
              <rPr>
                <b val="on"/>
              </rPr>
            </style>
            <style styleId="two">
              <basedOn val="one"/>
              <rPr>
                <i val="on"/>
              </rPr>
            </style>
            <style styleId="three">
              <basedOn val="two"/>
              <rPr>
                <u val="single"/>
              </rPr>
            </style>
        '''

        document_xml = '''
            <p>
              <pPr>
                <pStyle val="three"/>
              </pPr>
              <r>
                <t>aaa</t>
              </r>
            </p>
        '''

        document = WordprocessingDocumentFactory()
        document.add(StyleDefinitionsPart, style_xml)
        document.add(MainDocumentPart, document_xml)

        expected_html = '''
            <p>
              <span class="pydocx-underline">
                <em>
                  <strong>aaa</strong>
                </em>
              </span>
            </p>
        '''
        self.assert_document_generates_html(document, expected_html)

    def test_basedon_ignored_for_character_based_on_paragraph(self):
        # character styles may only be based on other character styles
        # otherwise, the based on specification should be ignored
        style_xml = '''
            <style styleId="one" type="paragraph">
              <rPr>
                <b val="on"/>
              </rPr>
            </style>
            <style styleId="two" type="character">
              <basedOn val="one"/>
              <rPr>
                <i val="on"/>
              </rPr>
            </style>
        '''

        document_xml = '''
            <p>
              <r>
                <rPr>
                  <rStyle val="two"/>
                </rPr>
                <t>aaa</t>
              </r>
            </p>
        '''

        document = WordprocessingDocumentFactory()
        document.add(StyleDefinitionsPart, style_xml)
        document.add(MainDocumentPart, document_xml)

        expected_html = '<p><em>aaa</em></p>'
        self.assert_document_generates_html(document, expected_html)

    def test_basedon_ignored_for_paragraph_based_on_character(self):
        # paragraph styles may only be based on other paragraph styles
        # otherwise, the based on specification should be ignored
        style_xml = '''
            <style styleId="one" type="character">
              <rPr>
                <b val="on"/>
              </rPr>
            </style>
            <style styleId="two" type="paragraph">
              <basedOn val="one"/>
              <rPr>
                <i val="on"/>
              </rPr>
            </style>
        '''

        document_xml = '''
            <p>
              <pPr>
                <pStyle val="two"/>
              </pPr>
              <r>
                <t>aaa</t>
              </r>
            </p>
        '''

        document = WordprocessingDocumentFactory()
        document.add(StyleDefinitionsPart, style_xml)
        document.add(MainDocumentPart, document_xml)

        expected_html = '<p><em>aaa</em></p>'
        self.assert_document_generates_html(document, expected_html)


class DirectFormattingBoldPropertyTestCase(DocumentGeneratorTestCase):
    def test_default_no_val_set(self):
        document_xml = '''
            <p>
              <r>
                <rPr>
                  <b />
                </rPr>
                <t>foo</t>
              </r>
            </p>
        '''

        document = WordprocessingDocumentFactory()
        document.add(MainDocumentPart, document_xml)

        expected_html = '<p><strong>foo</strong></p>'
        self.assert_document_generates_html(document, expected_html)

    def test_valid_enable_vals_create_strong(self):
        vals = [
            'true',
            'on',
            '1',
            '',
        ]
        paragraph_template = '''
            <p>
              <r>
                <rPr>
                  <b val="%s" />
                </rPr>
                <t>foo</t>
              </r>
            </p>
        '''
        document_xml = ''.join(
            paragraph_template % val
            for val in vals
        )

        document = WordprocessingDocumentFactory()
        document.add(MainDocumentPart, document_xml)

        expected_html = '''
            <p><strong>foo</strong></p>
            <p><strong>foo</strong></p>
            <p><strong>foo</strong></p>
            <p><strong>foo</strong></p>
        '''
        self.assert_document_generates_html(document, expected_html)

    def test_valid_disabled_vals_do_not_create_strong(self):
        vals = [
            'off',
            'false',
            'none',
            '0',
        ]
        paragraph_template = '''
            <p>
              <r>
                <rPr>
                  <b val="%s" />
                </rPr>
                <t>foo</t>
              </r>
            </p>
        '''
        document_xml = ''.join(
            paragraph_template % val
            for val in vals
        )

        document = WordprocessingDocumentFactory()
        document.add(MainDocumentPart, document_xml)

        expected_html = '''
            <p>foo</p>
            <p>foo</p>
            <p>foo</p>
            <p>foo</p>
        '''
        self.assert_document_generates_html(document, expected_html)

    def test_invalid_vals_do_not_create_strong(self):
        vals = [
            'foo',
            'bar',
        ]
        paragraph_template = '''
            <p>
              <r>
                <rPr>
                  <b val="%s" />
                </rPr>
                <t>foo</t>
              </r>
            </p>
        '''
        document_xml = ''.join(
            paragraph_template % val
            for val in vals
        )

        document = WordprocessingDocumentFactory()
        document.add(MainDocumentPart, document_xml)

        expected_html = '''
            <p>foo</p>
            <p>foo</p>
        '''
        self.assert_document_generates_html(document, expected_html)


class DrawingGraphicBlipTestCase(DocumentGeneratorTestCase):
    def test_inline_image_with_multiple_ext_definitions(self):
        # Ensure that the image size can be calculated correctly even if the
        # image size ext isn't the first ext in the drawing node
        document_xml = '''
            <p>
            <r>
              <t>Foo</t>
              <drawing>
                <inline>
                  <graphic>
                    <graphicData>
                      <pic>
                        <blipFill>
                          <blip embed="foobar">
                            <extLst>
                              <ext/>
                            </extLst>
                          </blip>
                        </blipFill>
                        <spPr>
                          <xfrm>
                            <ext cx="1600200" cy="2324100"/>
                          </xfrm>
                        </spPr>
                      </pic>
                    </graphicData>
                  </graphic>
                </inline>
              </drawing>
              <t>Bar</t>
            </r>
            </p>
        '''

        document = WordprocessingDocumentFactory()
        image_url = 'http://google.com/image1.gif'
        document_rels = document.relationship_format.format(
            id='foobar',
            type=ImagePart.relationship_type,
            target=image_url,
            target_mode='External',
        )

        document.add(MainDocumentPart, document_xml, document_rels)

        expected_html = '''
            <p>
              Foo
              <img src="http://google.com/image1.gif"
                height="244px" width="168px" />
              Bar
            </p>
        '''

        self.assert_document_generates_html(document, expected_html)

    def test_anchor_with_multiple_ext_definitions(self):
        # Ensure that the image size can be calculated correctly even if the
        # image size ext isn't the first ext in the drawing node
        document_xml = '''
            <p>
            <r>
              <t>Foo</t>
              <drawing>
                <anchor>
                  <graphic>
                    <graphicData>
                      <pic>
                        <blipFill>
                          <blip embed="foobar">
                            <extLst>
                              <ext/>
                            </extLst>
                          </blip>
                        </blipFill>
                        <spPr>
                          <xfrm>
                            <ext cx="1600200" cy="2324100"/>
                          </xfrm>
                        </spPr>
                      </pic>
                    </graphicData>
                  </graphic>
                </anchor>
              </drawing>
              <t>Bar</t>
            </r>
            </p>
        '''

        document = WordprocessingDocumentFactory()
        image_url = 'http://google.com/image1.gif'
        document_rels = document.relationship_format.format(
            id='foobar',
            type=ImagePart.relationship_type,
            target=image_url,
            target_mode='External',
        )

        document.add(MainDocumentPart, document_xml, document_rels)

        expected_html = '''
            <p>
              Foo
              <img src="http://google.com/image1.gif"
                height="244px" width="168px" />
              Bar
            </p>
        '''

        self.assert_document_generates_html(document, expected_html)

    def test_anchor_with_no_size_ext(self):
        # Ensure the image html is still rendered even if the size cannot be
        # calculated
        document_xml = '''
            <p>
            <r>
              <t>Foo</t>
              <drawing>
                <anchor>
                  <graphic>
                    <graphicData>
                      <pic>
                        <blipFill>
                          <blip embed="foobar"/>
                        </blipFill>
                        <spPr>
                          <xfrm/>
                        </spPr>
                      </pic>
                    </graphicData>
                  </graphic>
                </anchor>
              </drawing>
              <t>Bar</t>
            </r>
            </p>
        '''

        document = WordprocessingDocumentFactory()
        image_url = 'http://google.com/image1.gif'
        document_rels = document.relationship_format.format(
            id='foobar',
            type=ImagePart.relationship_type,
            target=image_url,
            target_mode='External',
        )

        document.add(MainDocumentPart, document_xml, document_rels)

        expected_html = '''
            <p>
              Foo
              <img src="http://google.com/image1.gif" />
              Bar
            </p>
        '''

        self.assert_document_generates_html(document, expected_html)

    def test_blip_embed_refers_to_undefined_image_relationship(self):
        # Ensure that if a blip embed refers to an undefined image
        # relationshipp, the image rendering is skipped
        document_xml = '''
            <p>
            <r>
              <t>Foo</t>
              <drawing>
                <anchor>
                  <graphic>
                    <graphicData>
                      <pic>
                        <blipFill>
                          <blip embed="foobar" />
                        </blipFill>
                      </pic>
                    </graphicData>
                  </graphic>
                </anchor>
              </drawing>
              <t>Bar</t>
            </r>
            </p>
        '''

        document = WordprocessingDocumentFactory()
        document.add(MainDocumentPart, document_xml)

        expected_html = '<p>FooBar</p>'

        self.assert_document_generates_html(document, expected_html)


class HyperlinkTestCase(DocumentGeneratorTestCase):
    def test_single_run(self):
        document_xml = '''
            <p>
              <hyperlink id="foobar">
                <r>
                  <t>link</t>
                </r>
              </hyperlink>
              <r>
                <t>.</t>
              </r>
            </p>
        '''

        document = WordprocessingDocumentFactory()
        document_rels = document.relationship_format.format(
            id='foobar',
            type='foo/hyperlink',
            target='http://google.com',
            target_mode='External',
        )

        document.add(MainDocumentPart, document_xml, document_rels)

        expected_html = '<p><a href="http://google.com">link</a>.</p>'
        self.assert_document_generates_html(document, expected_html)

    def test_multiple_runs(self):
        document_xml = '''
            <p>
              <hyperlink id="foobar">
                <r>
                  <t>l</t>
                  <t>i</t>
                  <t>n</t>
                  <t>k</t>
                </r>
              </hyperlink>
              <r>
                <t>.</t>
              </r>
            </p>
        '''

        document = WordprocessingDocumentFactory()
        document_rels = document.relationship_format.format(
            id='foobar',
            type='foo/hyperlink',
            target='http://google.com',
            target_mode='External',
        )

        document.add(MainDocumentPart, document_xml, document_rels)

        expected_html = '<p><a href="http://google.com">link</a>.</p>'
        self.assert_document_generates_html(document, expected_html)

    def test_no_link_text(self):
        document_xml = '''
            <p>
              <hyperlink id="foobar" />
            </p>
        '''

        document = WordprocessingDocumentFactory()
        document_rels = document.relationship_format.format(
            id='foobar',
            type='foo/hyperlink',
            target='http://google.com',
            target_mode='External',
        )

        document.add(MainDocumentPart, document_xml, document_rels)

        expected_html = ''
        self.assert_document_generates_html(document, expected_html)

    def test_undefined_relationship(self):
        document_xml = '''
            <p>
              <hyperlink id="foobar">
                <r>
                  <t>link</t>
                </r>
              </hyperlink>
              <r>
                <t>.</t>
              </r>
            </p>
        '''

        document = WordprocessingDocumentFactory()
        document.add(MainDocumentPart, document_xml)

        expected_html = '<p>link.</p>'
        self.assert_document_generates_html(document, expected_html)

    def test_with_line_break(self):
        document_xml = '''
            <p>
              <hyperlink id="foobar">
                <r>
                  <t>li</t>
                  <br />
                  <t>nk</t>
                </r>
              </hyperlink>
              <r>
                <t>.</t>
              </r>
            </p>
        '''

        document = WordprocessingDocumentFactory()
        document_rels = document.relationship_format.format(
            id='foobar',
            type='foo/hyperlink',
            target='http://google.com',
            target_mode='External',
        )

        document.add(MainDocumentPart, document_xml, document_rels)

        expected_html = '<p><a href="http://google.com">li<br />nk</a>.</p>'
        self.assert_document_generates_html(document, expected_html)
