# tests/unit/test_doc_export.py
#
# Unit tests for the deterministic Google Docs request builder — the breakable
# index math and brand-font wiring for embedding real illustrations. No network.

from app.doc_export import (
    BODY_FONT,
    LABEL_FONT,
    DocPage,
    build_doc_requests,
    drive_image_uri,
)


def _pages() -> list[DocPage]:
    return [
        DocPage(text="Sam ran.", image_uri="https://img/1"),
        DocPage(text="Sam sat.", image_uri="https://img/2"),
    ]


def test_inserts_title_then_each_page_text_and_image() -> None:
    reqs = build_doc_requests("Sam Runs", _pages())
    inserts = [r["insertText"]["text"] for r in reqs if "insertText" in r]
    images = [r["insertInlineImage"]["uri"] for r in reqs if "insertInlineImage" in r]
    assert inserts[0] == "Sam Runs\n"
    assert "Sam ran.\n" in inserts
    assert "Sam sat.\n" in inserts
    assert images == ["https://img/1", "https://img/2"]


def test_indices_advance_consistently_with_application_order() -> None:
    # Simulate applying the requests to an empty doc and confirm every insert's
    # index equals the running length of everything inserted before it.
    reqs = build_doc_requests("Hi", _pages())
    cursor = 1
    for r in reqs:
        if "insertText" in r:
            assert r["insertText"]["location"]["index"] == cursor
            cursor += len(r["insertText"]["text"])
        elif "insertInlineImage" in r:
            assert r["insertInlineImage"]["location"]["index"] == cursor
            cursor += 1  # an inline image occupies exactly one index unit
        elif "insertPageBreak" in r:
            assert r["insertPageBreak"]["location"]["index"] == cursor
            cursor += 1  # a page break occupies exactly one index unit


def test_each_page_text_is_paired_with_its_own_image_on_its_own_page() -> None:
    # Regression for the off-by-one: ~360pt illustrations + no page break let
    # each image paginate onto the FOLLOWING page's text, so every picture showed
    # the wrong (prior) scene. A page break before each story page pins the
    # rendered pairing to text[i] <-> image[i]. Distinct text/uris per page so any
    # one-off shift is detectable. Fails before the page-break fix (no break ->
    # the body never partitions into per-page sections).
    pages = [
        DocPage(text=f"Page {i} text.", image_uri=f"https://img/{i}")
        for i in range(1, 5)
    ]
    reqs = build_doc_requests("The Title", pages)

    # Partition the request stream into the cover (before the first break) and one
    # section per page break — exactly how the paginated Doc lays out.
    cover: list[tuple[str, str]] = []
    sections: list[list[tuple[str, str]]] = []
    current = cover
    for r in reqs:
        if "insertPageBreak" in r:
            current = []
            sections.append(current)
        elif "insertText" in r:
            current.append(("text", r["insertText"]["text"]))
        elif "insertInlineImage" in r:
            current.append(("img", r["insertInlineImage"]["uri"]))

    # One page break (hence one section) per story page — nothing flows together.
    assert len(sections) == len(pages), "expected a page break before each page"
    # The title lives on its own cover page with no story illustration.
    assert ("text", "The Title\n") in cover
    assert not any(kind == "img" for kind, _ in cover)
    # Each page section holds its OWN text followed by its OWN image — no drift.
    for page, section in zip(pages, sections):
        kinds = [kind for kind, _ in section]
        texts = [val for kind, val in section if kind == "text"]
        imgs = [val for kind, val in section if kind == "img"]
        assert texts[0] == page.text + "\n"
        assert imgs == [page.image_uri]
        assert kinds.index("text") < kinds.index("img")  # text above its picture


def test_title_is_heading_in_label_font_pages_in_body_font() -> None:
    reqs = build_doc_requests("Title", _pages())
    para_styles = [r["updateParagraphStyle"] for r in reqs if "updateParagraphStyle" in r]
    assert para_styles[0]["paragraphStyle"]["namedStyleType"] == "HEADING_1"

    fonts = [
        r["updateTextStyle"]["textStyle"]["weightedFontFamily"]["fontFamily"]
        for r in reqs
        if "updateTextStyle" in r
    ]
    # Title uses the label font; story text uses the (OpenDyslexic) body font.
    assert fonts[0] == LABEL_FONT
    assert BODY_FONT in fonts
    assert all(f in {LABEL_FONT, BODY_FONT} for f in fonts)  # exactly two fonts


def test_text_style_ranges_stay_within_inserted_text() -> None:
    # Every styled range must be non-empty and not run past the doc length.
    reqs = build_doc_requests("Title", _pages())
    total = 1 + sum(
        len(r["insertText"]["text"]) for r in reqs if "insertText" in r
    ) + sum(1 for r in reqs if "insertInlineImage" in r)
    for r in reqs:
        rng = (
            r.get("updateTextStyle", {}).get("range")
            or r.get("updateParagraphStyle", {}).get("range")
        )
        if rng:
            assert 1 <= rng["startIndex"] < rng["endIndex"] <= total


def test_image_carries_brand_sized_object() -> None:
    reqs = build_doc_requests("T", [DocPage(text="x", image_uri="u", width_pt=300, height_pt=300)])
    img = next(r["insertInlineImage"] for r in reqs if "insertInlineImage" in r)
    assert img["objectSize"]["width"]["magnitude"] == 300
    assert img["objectSize"]["width"]["unit"] == "PT"


def test_page_with_empty_text_still_inserts_image() -> None:
    reqs = build_doc_requests("T", [DocPage(text="   ", image_uri="u")])
    assert any("insertInlineImage" in r for r in reqs)
    # No empty story paragraph is inserted for blank text.
    page_texts = [r["insertText"]["text"] for r in reqs if "insertText" in r]
    assert "   \n" not in page_texts


def test_is_deterministic() -> None:
    assert build_doc_requests("T", _pages()) == build_doc_requests("T", _pages())


def test_drive_image_uri_is_fetchable_form() -> None:
    assert drive_image_uri("ABC123") == "https://lh3.googleusercontent.com/d/ABC123"
