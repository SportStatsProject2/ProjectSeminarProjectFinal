from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "docs" / "SportStats_Demo_Presentation.pptx"

SLIDE_CX = 12_192_000
SLIDE_CY = 6_858_000
EMU_PER_UNIT = SLIDE_CX / 28_000

COLORS = {
    "bg": "F4F7F3",
    "surface": "FFFFFF",
    "ink": "16221B",
    "muted": "5C6A63",
    "line": "D8E0DA",
    "green": "176B4D",
    "blue": "1D5F8F",
    "gold": "BD8A1B",
    "dark": "102016",
    "soft_green": "EAF5EE",
}

SLIDES = [
    {
        "title": "SportStats",
        "subtitle": "Football analytics platform for prediction, tactical structure, and video analysis",
        "authors": ["Daniel Emeka-Ilozor", "Assylkhan Balmukhanov"],
        "kind": "title",
    },
    {
        "title": "Project Overview",
        "bullets": [
            "A Flask web app for football analytics workflows in one place.",
            "Combines statistical forecasting, tournament simulation, event-network graphics, and YOLO/OpenCV video analysis.",
            "Designed for an interactive course demo: upload data or video, run the model, inspect the result immediately.",
        ],
        "callout": "Goal: turn raw match inputs into readable football insights.",
    },
    {
        "title": "Technology Stack",
        "columns": [
            ("Web", ["Flask app factory", "Jinja templates", "HTML/CSS/SVG UI"]),
            ("Data + Stats", ["NumPy", "pandas", "Poisson models", "Elo ratings"]),
            ("Vision", ["OpenCV", "Ultralytics YOLO", "ByteTrack tracking", "k-means shirt colors"]),
            ("Delivery", ["Docker", "GitHub Actions CI", "Ruff + Pytest", "release-hosted model file"]),
        ],
    },
    {
        "title": "System Architecture",
        "flow": ["Browser UI", "Flask routes", "Analytics services", "Data/model assets", "Rendered results"],
        "bullets": [
            "Routes validate inputs and dispatch to focused service modules.",
            "Statistical services return plain dictionaries for templates and tests.",
            "The vision pipeline writes generated videos to static outputs for browser playback.",
        ],
    },
    {
        "title": "Implemented: Statistical Analytics",
        "columns": [
            ("Match Predictor", ["Elo/team-strength inputs", "Poisson score simulation", "Win/draw/loss probabilities"]),
            ("xG Calculator", ["Distance and goal angle", "Body-part adjustment", "Shot-map visualization"]),
            ("Elo Ratings", ["International result history", "Top-team ranking table", "Home/neutral handling"]),
            ("World Cup Predictor", ["2026 group structure", "Elo-driven match xG", "Round-of-32 knockout path"]),
        ],
    },
    {
        "title": "Implemented: Tactical and Vision Analytics",
        "columns": [
            ("Passing Network", ["JSON pass-event editor", "Average player positions", "Weighted links and central player"]),
            ("YOLO Vision", ["Players, referees, and ball tracking", "Team color assignment", "Possession, speed, distance"]),
            ("Model Handling", ["Public best.pt release asset", "Automatic model download path", "Full-video processing"]),
        ],
    },
    {
        "title": "Implemented: Engineering Quality",
        "bullets": [
            "Application factory structure with route and service separation.",
            "Focused tests for prediction, xG, Elo, passing networks, model assets, vision helpers, and World Cup simulation.",
            "GitHub pull-request workflow with CI checks.",
            "Docker support and environment-based configuration.",
            "README, training notes, architecture documentation, and demo instructions.",
        ],
        "callout": "Current local suite: 43 passing tests.",
    },
    {
        "title": "Planned Feature Not Implemented",
        "bullets": [
            "Automated pass extraction from video into the passing-network page.",
            "The passing-network page accepts structured pass-event JSON today.",
            "The YOLO pipeline tracks players and ball control, but does not yet convert those tracks into pass events.",
            "This is the main next step because it would connect the video-analysis workflow directly to tactical network analysis.",
        ],
        "callout": "Everything else shown in the demo is implemented in the app.",
    },
    {
        "title": "Demo Flow",
        "steps": [
            "Open the dashboard and show the feature navigation.",
            "Run the Match Predictor with two teams and explain Elo/xG inputs.",
            "Open the World Cup Predictor and run a scenario; point out Elo and xG in bracket cards.",
            "Open Passing Network, edit/remove JSON events, and show event/player counts changing.",
            "Upload a football clip in YOLO Vision and play the processed output.",
            "Finish on Architecture to summarize how the pieces connect.",
        ],
    },
    {
        "title": "Local Demo Commands",
        "code": [
            "git pull --ff-only origin main",
            "source yolo_env/bin/activate",
            "python scripts/download_model.py",
            "flask --app app run --debug",
        ],
        "bullets": [
            "Open http://127.0.0.1:5000",
            "Use a short clip first if the machine is slow.",
            "Keep models/best.pt available for the custom detector.",
        ],
    },
    {
        "title": "Closing",
        "bullets": [
            "The project demonstrates statistical football analysis, tactical event visualization, and computer vision in one workflow.",
            "The implemented parts are demo-ready and covered by automated checks.",
            "The only planned feature outside the demo is automatic conversion from video tracks to pass-event JSON.",
        ],
        "callout": "Questions and live demo",
    },
]


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(OUTPUT_PATH, "w", ZIP_DEFLATED) as package:
        _write_static_parts(package)
        for index, slide in enumerate(SLIDES, start=1):
            package.writestr(f"ppt/slides/slide{index}.xml", _slide_xml(index, slide))
            package.writestr(f"ppt/slides/_rels/slide{index}.xml.rels", _slide_rels())
    print(OUTPUT_PATH)


def _write_static_parts(package: ZipFile) -> None:
    package.writestr("[Content_Types].xml", _content_types())
    package.writestr("_rels/.rels", _root_rels())
    package.writestr("docProps/core.xml", _core_props())
    package.writestr("docProps/app.xml", _app_props())
    package.writestr("ppt/presentation.xml", _presentation_xml())
    package.writestr("ppt/_rels/presentation.xml.rels", _presentation_rels())
    package.writestr("ppt/slideMasters/slideMaster1.xml", _slide_master())
    package.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", _slide_master_rels())
    package.writestr("ppt/slideLayouts/slideLayout1.xml", _slide_layout())
    package.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", _slide_layout_rels())
    package.writestr("ppt/theme/theme1.xml", _theme())


def _slide_xml(slide_number: int, slide: dict) -> str:
    shape_id = 1
    shapes = [_group_shape()]
    shape_id, background = _background(shape_id)
    shapes.extend(background)

    if slide.get("kind") == "title":
        shape_id, title_shapes = _title_slide(shape_id, slide)
        shapes.extend(title_shapes)
    else:
        shape_id, title = _text(shape_id, f"{slide_number - 1:02d}", 1530, 760, 900, 520, 1500, COLORS["gold"], True)
        shapes.append(title)
        shape_id, title = _text(shape_id, slide["title"], 1850, 1110, 17000, 900, 3400, COLORS["ink"], True)
        shapes.append(title)
        shape_id, body_shapes = _content_shapes(shape_id, slide)
        shapes.extend(body_shapes)

    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      {"".join(shapes)}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""


def _background(shape_id: int) -> tuple[int, list[str]]:
    shapes = [
        _rect(shape_id, 0, 0, 28_000, 15_750, COLORS["bg"], COLORS["bg"]),
        _rect(shape_id + 1, 0, 0, 760, 15_750, COLORS["green"], COLORS["green"]),
        _rect(shape_id + 2, 27_420, 0, 580, 15_750, COLORS["gold"], COLORS["gold"]),
    ]
    return shape_id + 3, shapes


def _title_slide(shape_id: int, slide: dict) -> tuple[int, list[str]]:
    shapes = []
    shape_id, item = _text(shape_id, "Football analytics platform", 1850, 2550, 11800, 780, 1700, COLORS["gold"], True)
    shapes.append(item)
    shape_id, item = _text(shape_id, slide["title"], 1800, 3400, 15000, 1700, 5200, COLORS["ink"], True)
    shapes.append(item)
    shape_id, item = _text(shape_id, slide["subtitle"], 1900, 5200, 16000, 1150, 2200, COLORS["muted"], False)
    shapes.append(item)
    shapes.append(_rect(shape_id, 1850, 7200, 10100, 1850, COLORS["surface"], COLORS["line"]))
    shape_id += 1
    shape_id, item = _text(shape_id, "Authors", 2300, 7550, 2500, 450, 1400, COLORS["gold"], True)
    shapes.append(item)
    shape_id, item = _text(shape_id, "\n".join(slide["authors"]), 2300, 8070, 7700, 900, 2200, COLORS["ink"], True)
    shapes.append(item)
    shape_id, item = _text(shape_id, "Demo presentation", 1900, 13100, 6000, 650, 1600, COLORS["muted"], False)
    shapes.append(item)
    return shape_id, shapes


def _content_shapes(shape_id: int, slide: dict) -> tuple[int, list[str]]:
    shapes: list[str] = []
    if "columns" in slide:
        shape_id, items = _columns(shape_id, slide["columns"])
        shapes.extend(items)
    if "flow" in slide:
        shape_id, items = _flow(shape_id, slide["flow"])
        shapes.extend(items)
    if "bullets" in slide:
        y = 6900 if "flow" in slide else 3100
        shape_id, item = _text(shape_id, _bullet_text(slide["bullets"]), 2150, y, 16400, 5600, 2000, COLORS["ink"], False)
        shapes.append(item)
    if "steps" in slide:
        shape_id, items = _steps(shape_id, slide["steps"])
        shapes.extend(items)
    if "code" in slide:
        shape_id, items = _code(shape_id, slide["code"], slide["bullets"])
        shapes.extend(items)
    if "callout" in slide:
        shapes.append(_rect(shape_id, 1900, 11600, 11800, 1350, COLORS["soft_green"], "C8D8CE"))
        shape_id += 1
        shape_id, item = _text(shape_id, slide["callout"], 2350, 12000, 11000, 520, 2000, COLORS["green"], True)
        shapes.append(item)
    return shape_id, shapes


def _columns(shape_id: int, columns: list[tuple[str, list[str]]]) -> tuple[int, list[str]]:
    shapes = []
    count = len(columns)
    gap = 500
    width = int((28_000 - 3600 - gap * (count - 1)) / count)
    x = 1800
    for title, items in columns:
        shapes.append(_rect(shape_id, x, 3300, width, 6800, COLORS["surface"], COLORS["line"]))
        shape_id += 1
        shape_id, item = _text(shape_id, title, x + 420, 3720, width - 840, 620, 1800, COLORS["green"], True)
        shapes.append(item)
        shape_id, item = _text(shape_id, _bullet_text(items), x + 540, 4620, width - 980, 4800, 1600, COLORS["ink"], False)
        shapes.append(item)
        x += width + gap
    return shape_id, shapes


def _flow(shape_id: int, flow_items: list[str]) -> tuple[int, list[str]]:
    shapes = []
    width = 4100
    height = 1250
    gap = 430
    x = 1900
    y = 3150
    for index, item in enumerate(flow_items):
        shapes.append(_rect(shape_id, x, y, width, height, COLORS["surface"], COLORS["line"]))
        shape_id += 1
        shape_id, text = _text(shape_id, item, x + 320, y + 345, width - 640, 560, 1700, COLORS["ink"], True)
        shapes.append(text)
        x += width
        if index < len(flow_items) - 1:
            shapes.append(_rect(shape_id, x + 80, y + 600, gap - 160, 70, COLORS["green"], COLORS["green"]))
            shape_id += 1
            x += gap
    return shape_id, shapes


def _steps(shape_id: int, steps: list[str]) -> tuple[int, list[str]]:
    shapes = []
    y = 3000
    for index, step in enumerate(steps, start=1):
        shapes.append(_rect(shape_id, 2000, y, 1200, 860, COLORS["green"], COLORS["green"]))
        shape_id += 1
        shape_id, number = _text(shape_id, str(index), 2380, y + 210, 450, 360, 2200, "FFFFFF", True)
        shapes.append(number)
        shape_id, text = _text(shape_id, step, 3550, y + 150, 16500, 520, 1800, COLORS["ink"], False)
        shapes.append(text)
        y += 1200
    return shape_id, shapes


def _code(shape_id: int, lines: list[str], bullets: list[str]) -> tuple[int, list[str]]:
    shapes = [_rect(shape_id, 1900, 3200, 16800, 4100, COLORS["dark"], COLORS["dark"])]
    shape_id += 1
    shape_id, code = _text(shape_id, "\n".join(lines), 2400, 3650, 15800, 3200, 1800, "FFFFFF", False, font="Consolas")
    shapes.append(code)
    shape_id, bullet_box = _text(shape_id, _bullet_text(bullets), 2150, 8000, 16000, 3200, 1800, COLORS["ink"], False)
    shapes.append(bullet_box)
    return shape_id, shapes


def _group_shape() -> str:
    return """<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>"""


def _rect(shape_id: int, x: int, y: int, width: int, height: int, fill: str, line: str) -> str:
    return f"""<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="Rectangle {shape_id}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="{_u(x)}" y="{_u(y)}"/><a:ext cx="{_u(width)}" cy="{_u(height)}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:solidFill><a:srgbClr val="{fill}"/></a:solidFill><a:ln><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln></p:spPr></p:sp>"""


def _text(
    shape_id: int,
    value: str,
    x: int,
    y: int,
    width: int,
    height: int,
    size: int,
    color: str,
    bold: bool,
    *,
    font: str = "Aptos",
) -> tuple[int, str]:
    paragraphs = "".join(_paragraph(line, size, color, bold, font) for line in value.split("\n"))
    xml = f"""<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="Text {shape_id}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="{_u(x)}" y="{_u(y)}"/><a:ext cx="{_u(width)}" cy="{_u(height)}"/></a:xfrm><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr wrap="square"/><a:lstStyle/>{paragraphs}</p:txBody></p:sp>"""
    return shape_id + 1, xml


def _paragraph(value: str, size: int, color: str, bold: bool, font: str) -> str:
    bold_attr = ' b="1"' if bold else ""
    return f"""<a:p><a:r><a:rPr lang="en-US" sz="{size}"{bold_attr}><a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:latin typeface="{escape(font)}"/></a:rPr><a:t>{escape(value)}</a:t></a:r></a:p>"""


def _bullet_text(items: list[str]) -> str:
    return "\n".join(f"• {item}" for item in items)


def _u(value: int) -> int:
    return round(value * EMU_PER_UNIT)


def _content_types() -> str:
    slide_overrides = "\n".join(
        f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(1, len(SLIDES) + 1)
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
  {slide_overrides}
</Types>"""


def _root_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""


def _presentation_xml() -> str:
    slide_ids = "\n".join(
        f'<p:sldId id="{255 + i}" r:id="rId{i + 1}"/>' for i in range(1, len(SLIDES) + 1)
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>
  <p:sldIdLst>{slide_ids}</p:sldIdLst>
  <p:sldSz cx="{SLIDE_CX}" cy="{SLIDE_CY}" type="wide"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>"""


def _presentation_rels() -> str:
    rels = ['<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>']
    for i in range(1, len(SLIDES) + 1):
        rels.append(
            f'<Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>'
        )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  {"".join(rels)}
</Relationships>"""


def _slide_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>"""


def _slide_master() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
  <p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles>
</p:sldMaster>"""


def _slide_master_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>"""


def _slide_layout() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1">
  <p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>"""


def _slide_layout_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>"""


def _core_props() -> str:
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>SportStats Demo Presentation</dc:title>
  <dc:creator>Daniel Emeka-Ilozor; Assylkhan Balmukhanov</dc:creator>
  <cp:lastModifiedBy>SportStatsProject</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{timestamp}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{timestamp}</dcterms:modified>
</cp:coreProperties>"""


def _app_props() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>SportStatsProject</Application>
  <PresentationFormat>On-screen Show (16:9)</PresentationFormat>
  <Slides>{len(SLIDES)}</Slides>
  <Company>SportStatsProject</Company>
</Properties>"""


def _theme() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="SportStats">
  <a:themeElements>
    <a:clrScheme name="SportStats"><a:dk1><a:srgbClr val="16221B"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="176B4D"/></a:dk2><a:lt2><a:srgbClr val="F4F7F3"/></a:lt2><a:accent1><a:srgbClr val="176B4D"/></a:accent1><a:accent2><a:srgbClr val="1D5F8F"/></a:accent2><a:accent3><a:srgbClr val="BD8A1B"/></a:accent3><a:accent4><a:srgbClr val="5C6A63"/></a:accent4><a:accent5><a:srgbClr val="D8E0DA"/></a:accent5><a:accent6><a:srgbClr val="A83232"/></a:accent6><a:hlink><a:srgbClr val="1D5F8F"/></a:hlink><a:folHlink><a:srgbClr val="5C6A63"/></a:folHlink></a:clrScheme>
    <a:fontScheme name="Aptos"><a:majorFont><a:latin typeface="Aptos Display"/></a:majorFont><a:minorFont><a:latin typeface="Aptos"/></a:minorFont></a:fontScheme>
    <a:fmtScheme name="SportStats"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme>
  </a:themeElements>
</a:theme>"""


if __name__ == "__main__":
    main()
