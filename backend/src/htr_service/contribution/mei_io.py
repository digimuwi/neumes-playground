"""MEI 5.0 reader/writer for contribution annotations.

See spec/mei-profile.md for the format definition. This module is the only
place in the backend that knows about MEI XML; storage.py and the training
pipelines consume the in-memory ContributionDocument model.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Optional

from pydantic import BaseModel

from ..models.types import (
    BBox,
    ImageMetadata,
    LineInput,
    NeumeInput,
    SyllableInput,
)

MEI_NS = "http://www.music-encoding.org/ns/mei"
XML_NS = "http://www.w3.org/XML/1998/namespace"
_MEI = "{%s}" % MEI_NS
_XML_ID = "{%s}id" % XML_NS


class ContributionDocument(BaseModel):
    """Full contribution: image metadata + lines + flat neumes.

    Mirrors the on-disk shape; matches what the API and training pipelines
    consume. The MEI nesting (neumes under syllables) is the on-disk
    representation; in memory we keep neumes flat and let consumers
    re-derive assignments when needed.
    """

    image: ImageMetadata
    lines: list[LineInput]
    neumes: list[NeumeInput]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def read_contribution(xml_bytes: bytes) -> ContributionDocument:
    """Parse MEI bytes into a ContributionDocument.

    Synthetic empty-syllable carriers (orphan neume convention) are
    flattened: their neume children become flat NeumeInput entries with
    no syllable association.
    """
    root = ET.fromstring(xml_bytes)
    return _read_root(root)


def write_contribution(doc: ContributionDocument) -> bytes:
    """Serialize a ContributionDocument as canonical MEI bytes.

    Computes neume↔syllable assignments using the same algorithm as the
    frontend's computeNeumeAssignments. Orphans are wrapped in synthetic
    empty-syllable carriers per the spec.
    """
    return _serialize_canonical(_build_root(doc))


def canonicalize_mei(xml_bytes: bytes) -> bytes:
    """Round-trip MEI through the parser+writer to produce canonical bytes.

    Used by the API to ensure stored bytes have a stable ETag regardless
    of how the client formatted its upload.
    """
    return write_contribution(read_contribution(xml_bytes))


def relabel_neume_in_mei(
    xml_bytes: bytes, bbox: dict, new_type: str
) -> bytes:
    """Find a neume by its zone bbox match and update its @type.

    Returns canonical bytes after the mutation. Raises ValueError if no
    matching neume is found.
    """
    doc = read_contribution(xml_bytes)
    target = (
        int(bbox["x"]),
        int(bbox["y"]),
        int(bbox["width"]),
        int(bbox["height"]),
    )
    found = False
    for neume in doc.neumes:
        b = neume.bbox
        if (b.x, b.y, b.width, b.height) == target:
            neume.type = new_type
            found = True
            break
    if not found:
        raise ValueError("No neume found with the given bounding box")
    return write_contribution(doc)


# ---------------------------------------------------------------------------
# Reader
# ---------------------------------------------------------------------------


def _read_root(root: ET.Element) -> ContributionDocument:
    surface = root.find(f"{_MEI}music/{_MEI}facsimile/{_MEI}surface")
    if surface is None:
        raise ValueError("MEI document missing <surface>")

    image_meta = _read_image_meta(surface)
    zones = _read_zones(surface)

    layer = root.find(
        f"{_MEI}music/{_MEI}body/{_MEI}mdiv/{_MEI}score/"
        f"{_MEI}section/{_MEI}staff/{_MEI}layer"
    )
    if layer is None:
        return ContributionDocument(image=image_meta, lines=[], neumes=[])

    runs = _split_layer_into_line_runs(layer)
    lines: list[LineInput] = []
    flat_neumes: list[NeumeInput] = []

    for line_zone_id, syllable_elements in runs:
        line_polygon = zones.get(line_zone_id)
        if line_polygon is None:
            continue

        # Detect "synthetic global line" case: every syllable on this line
        # is an orphan carrier — the line itself is synthetic, drop it.
        all_orphan = syllable_elements and all(
            _is_orphan_carrier(syl, line_zone_id)
            for syl in syllable_elements
        )

        if all_orphan:
            for syl in syllable_elements:
                for neume_el in syl.findall(f"{_MEI}neume"):
                    flat_neumes.append(_read_neume(neume_el, zones))
            continue

        real_syllables: list[SyllableInput] = []
        for syl in syllable_elements:
            if _is_orphan_carrier(syl, line_zone_id):
                for neume_el in syl.findall(f"{_MEI}neume"):
                    flat_neumes.append(_read_neume(neume_el, zones))
            else:
                real_syllables.append(_read_syllable(syl, zones))
                for neume_el in syl.findall(f"{_MEI}neume"):
                    flat_neumes.append(_read_neume(neume_el, zones))

        lines.append(LineInput(boundary=line_polygon, syllables=real_syllables))

    return ContributionDocument(image=image_meta, lines=lines, neumes=flat_neumes)


def _read_image_meta(surface: ET.Element) -> ImageMetadata:
    graphic = surface.find(f"{_MEI}graphic")
    filename = (
        graphic.get("target", "image.jpg") if graphic is not None else "image.jpg"
    )
    width = int(surface.get("lrx", "0"))
    height = int(surface.get("lry", "0"))
    return ImageMetadata(filename=filename, width=width, height=height)


def _read_zones(surface: ET.Element) -> dict[str, list[list[int]]]:
    zones: dict[str, list[list[int]]] = {}
    for zone in surface.findall(f"{_MEI}zone"):
        zid = zone.get(_XML_ID)
        if not zid:
            continue
        points = zone.get("points")
        if points:
            zones[zid] = _parse_points(points)
        else:
            ulx = int(zone.get("ulx", "0"))
            uly = int(zone.get("uly", "0"))
            lrx = int(zone.get("lrx", "0"))
            lry = int(zone.get("lry", "0"))
            zones[zid] = [[ulx, uly], [lrx, uly], [lrx, lry], [ulx, lry]]
    return zones


def _parse_points(points: str) -> list[list[int]]:
    out: list[list[int]] = []
    for token in points.split():
        x_str, y_str = token.split(",")
        out.append([int(x_str), int(y_str)])
    return out


def _split_layer_into_line_runs(
    layer: ET.Element,
) -> list[tuple[str, list[ET.Element]]]:
    runs: list[tuple[str, list[ET.Element]]] = []
    current_zone_id: Optional[str] = None
    current_syllables: list[ET.Element] = []

    for child in layer:
        tag = _local(child.tag)
        if tag == "lb":
            if current_zone_id is not None:
                runs.append((current_zone_id, current_syllables))
            facs = (child.get("facs") or "").lstrip("#")
            current_zone_id = facs or None
            current_syllables = []
        elif tag == "syllable":
            current_syllables.append(child)

    if current_zone_id is not None:
        runs.append((current_zone_id, current_syllables))

    return runs


def _is_orphan_carrier(syl: ET.Element, line_zone_id: str) -> bool:
    """A synthetic empty-syllable carrier per the spec: empty <syl> AND
    @facs points at the same zone-line-* as the parent <lb>."""
    syl_elem = syl.find(f"{_MEI}syl")
    has_text = syl_elem is not None and (syl_elem.text or "").strip() != ""
    if has_text:
        return False
    facs = (syl.get("facs") or "").lstrip("#")
    return facs == line_zone_id


def _read_syllable(syl_el: ET.Element, zones: dict) -> SyllableInput:
    facs = (syl_el.get("facs") or "").lstrip("#")
    polygon = zones.get(facs, [])

    syl_text_el = syl_el.find(f"{_MEI}syl")
    raw_text = ""
    wordpos = ""
    if syl_text_el is not None:
        raw_text = syl_text_el.text or ""
        wordpos = syl_text_el.get("wordpos") or ""

    text = raw_text
    # Reconstruct trailing hyphen from wordpos
    if wordpos in ("i", "m") and text != "" and not text.endswith("-"):
        text = text + "-"

    return SyllableInput(text=text, boundary=polygon)


def _read_neume(neume_el: ET.Element, zones: dict) -> NeumeInput:
    facs = (neume_el.get("facs") or "").lstrip("#")
    polygon = zones.get(facs, [])
    if polygon:
        xs = [pt[0] for pt in polygon]
        ys = [pt[1] for pt in polygon]
        x = min(xs)
        y = min(ys)
        width = max(1, max(xs) - x)
        height = max(1, max(ys) - y)
    else:
        x = y = 0
        width = height = 1
    return NeumeInput(
        type=neume_el.get("type") or "unknown",
        bbox=BBox(x=x, y=y, width=width, height=height),
    )


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


# ---------------------------------------------------------------------------
# Writer
# ---------------------------------------------------------------------------


def _build_root(doc: ContributionDocument) -> ET.Element:
    """Build an MEI ElementTree root for the document."""
    syl_uuids: list[list[str]] = [
        [
            f"{i:08d}-{j:04d}-0000-0000-000000000000"
            for j, _ in enumerate(line.syllables, 1)
        ]
        for i, line in enumerate(doc.lines, 1)
    ]
    neume_uuids: list[str] = [
        f"n{i:07d}-0000-0000-0000-000000000000"
        for i, _ in enumerate(doc.neumes, 1)
    ]

    per_syl, per_line_orphan, global_orphan = _assign_neumes(
        doc.lines, doc.neumes
    )
    has_synthetic_line = bool(global_orphan) and not doc.lines

    root = ET.Element(f"{_MEI}mei", {"meiversion": "5.0"})

    head = ET.SubElement(root, f"{_MEI}meiHead")
    file_desc = ET.SubElement(head, f"{_MEI}fileDesc")
    title_stmt = ET.SubElement(file_desc, f"{_MEI}titleStmt")
    title = ET.SubElement(title_stmt, f"{_MEI}title")
    title.text = "Neumes Playground contribution"
    ET.SubElement(file_desc, f"{_MEI}pubStmt")

    music = ET.SubElement(root, f"{_MEI}music")
    facsimile = ET.SubElement(music, f"{_MEI}facsimile")
    surface = ET.SubElement(
        facsimile,
        f"{_MEI}surface",
        {
            "lrx": str(doc.image.width),
            "lry": str(doc.image.height),
            "ulx": "0",
            "uly": "0",
            _XML_ID: "surface-1",
        },
    )
    ET.SubElement(
        surface,
        f"{_MEI}graphic",
        {
            "height": f"{doc.image.height}px",
            "target": doc.image.filename,
            "width": f"{doc.image.width}px",
        },
    )

    # Zones — order matters for canonical output: line zones, syllable zones, neume zones
    for i, line in enumerate(doc.lines, 1):
        _add_zone(surface, f"zone-line-{i}", line.boundary)

    if has_synthetic_line:
        full_polygon = [
            [0, 0],
            [doc.image.width, 0],
            [doc.image.width, doc.image.height],
            [0, doc.image.height],
        ]
        _add_zone(surface, "zone-line-1", full_polygon)

    for line_idx, line in enumerate(doc.lines):
        for syl_idx, syl in enumerate(line.syllables):
            zid = f"zone-syl-{syl_uuids[line_idx][syl_idx]}"
            _add_zone(surface, zid, syl.boundary)

    for n_idx, neume in enumerate(doc.neumes):
        zid = f"zone-n-{neume_uuids[n_idx]}"
        _add_zone(surface, zid, _bbox_polygon(neume.bbox))

    body = ET.SubElement(music, f"{_MEI}body")
    mdiv = ET.SubElement(body, f"{_MEI}mdiv")
    score = ET.SubElement(mdiv, f"{_MEI}score")
    section = ET.SubElement(score, f"{_MEI}section")
    staff = ET.SubElement(section, f"{_MEI}staff")
    layer = ET.SubElement(staff, f"{_MEI}layer")

    if doc.lines:
        for line_idx, line in enumerate(doc.lines):
            ET.SubElement(
                layer,
                f"{_MEI}lb",
                {
                    "facs": f"#zone-line-{line_idx + 1}",
                    "n": str(line_idx + 1),
                },
            )
            wordpos_chain = _compute_wordpos_chain(line.syllables)
            for syl_idx, syl in enumerate(line.syllables):
                _add_syllable(
                    layer,
                    syl,
                    syl_uuids[line_idx][syl_idx],
                    wordpos_chain[syl_idx],
                    [
                        (doc.neumes[ni], neume_uuids[ni])
                        for ni in per_syl[line_idx][syl_idx]
                    ],
                )
            if per_line_orphan[line_idx]:
                _add_orphan_carrier(
                    layer,
                    f"zone-line-{line_idx + 1}",
                    line_idx + 1,
                    [
                        (doc.neumes[ni], neume_uuids[ni])
                        for ni in per_line_orphan[line_idx]
                    ],
                )
    elif has_synthetic_line:
        ET.SubElement(
            layer, f"{_MEI}lb", {"facs": "#zone-line-1", "n": "1"}
        )
        _add_orphan_carrier(
            layer,
            "zone-line-1",
            1,
            [(doc.neumes[ni], neume_uuids[ni]) for ni in global_orphan],
        )

    return root


def _add_zone(
    surface: ET.Element, zone_id: str, polygon: list[list[int]]
) -> None:
    if not polygon:
        return
    xs = [pt[0] for pt in polygon]
    ys = [pt[1] for pt in polygon]
    ulx, uly = min(xs), min(ys)
    lrx, lry = max(xs), max(ys)
    points_str = " ".join(f"{int(x)},{int(y)}" for x, y in polygon)
    ET.SubElement(
        surface,
        f"{_MEI}zone",
        {
            "lrx": str(lrx),
            "lry": str(lry),
            "points": points_str,
            "ulx": str(ulx),
            "uly": str(uly),
            _XML_ID: zone_id,
        },
    )


def _add_syllable(
    layer: ET.Element,
    syl: SyllableInput,
    syl_uuid: str,
    wordpos: str,
    neumes: list[tuple[NeumeInput, str]],
) -> None:
    syl_el = ET.SubElement(
        layer,
        f"{_MEI}syllable",
        {
            "facs": f"#zone-syl-{syl_uuid}",
            _XML_ID: f"syl-{syl_uuid}",
        },
    )
    text = syl.text or ""
    if text == "":
        ET.SubElement(syl_el, f"{_MEI}syl")
    else:
        attrs = {"wordpos": wordpos} if wordpos else {}
        syl_text_el = ET.SubElement(syl_el, f"{_MEI}syl", attrs)
        syl_text_el.text = text.rstrip("-") if text.endswith("-") else text

    for neume, neume_uuid in neumes:
        ET.SubElement(
            syl_el,
            f"{_MEI}neume",
            {
                "facs": f"#zone-n-{neume_uuid}",
                "type": neume.type,
                _XML_ID: f"n-{neume_uuid}",
            },
        )


def _add_orphan_carrier(
    layer: ET.Element,
    line_zone_id: str,
    line_n: int,
    neumes: list[tuple[NeumeInput, str]],
) -> None:
    syl_el = ET.SubElement(
        layer,
        f"{_MEI}syllable",
        {
            "facs": f"#{line_zone_id}",
            _XML_ID: f"syl-orphan-{line_n}",
        },
    )
    ET.SubElement(syl_el, f"{_MEI}syl")
    for neume, neume_uuid in neumes:
        ET.SubElement(
            syl_el,
            f"{_MEI}neume",
            {
                "facs": f"#zone-n-{neume_uuid}",
                "type": neume.type,
                _XML_ID: f"n-{neume_uuid}",
            },
        )


def _bbox_polygon(bbox: BBox) -> list[list[int]]:
    return [
        [bbox.x, bbox.y],
        [bbox.x + bbox.width, bbox.y],
        [bbox.x + bbox.width, bbox.y + bbox.height],
        [bbox.x, bbox.y + bbox.height],
    ]


# ---------------------------------------------------------------------------
# Wordpos chain
# ---------------------------------------------------------------------------


def _compute_wordpos_chain(syllables: list[SyllableInput]) -> list[str]:
    """Mirror src/utils/meiExport.ts computeWordpos."""
    out = [""] * len(syllables)
    prev_ended_with_hyphen = False
    for i, syl in enumerate(syllables):
        text = syl.text or ""
        if text == "":
            continue
        ends_with_hyphen = text.endswith("-")
        if prev_ended_with_hyphen:
            out[i] = "m" if ends_with_hyphen else "t"
        else:
            out[i] = "i" if ends_with_hyphen else "s"
        prev_ended_with_hyphen = ends_with_hyphen
    return out


# ---------------------------------------------------------------------------
# Neume → syllable assignment (port of frontend computeNeumeAssignments)
# ---------------------------------------------------------------------------


def _assign_neumes(
    lines: list[LineInput], neumes: list[NeumeInput]
) -> tuple[list[list[list[int]]], list[list[int]], list[int]]:
    """Returns:
        per_syl[line_idx][syl_idx] = list of neume indices
        per_line_orphan[line_idx] = list of neume indices (line has no syllables)
        global_orphan = list of neume indices (no lines exist)
    """
    if not lines:
        return [], [], list(range(len(neumes)))

    line_metrics = _compute_line_metrics(lines)

    per_syl: list[list[list[int]]] = [
        [[] for _ in line.syllables] for line in lines
    ]
    per_line_orphan: list[list[int]] = [[] for _ in lines]

    order = sorted(range(len(lines)), key=lambda i: line_metrics[i][1])

    for n_idx, neume in enumerate(neumes):
        bbox = neume.bbox
        neume_x = bbox.x
        neume_y = bbox.y + bbox.height

        owning_idx = _find_owning_line(neume_x, neume_y, line_metrics, order)
        line = lines[owning_idx]

        if not line.syllables:
            per_line_orphan[owning_idx].append(n_idx)
            continue

        syl_idx = _find_closest_syllable(neume_x, line.syllables)
        per_syl[owning_idx][syl_idx].append(n_idx)

    for line_idx, line in enumerate(lines):
        for syl_idx in range(len(line.syllables)):
            per_syl[line_idx][syl_idx].sort(key=lambda ni: neumes[ni].bbox.x)
        per_line_orphan[line_idx].sort(key=lambda ni: neumes[ni].bbox.x)

    return per_syl, per_line_orphan, []


def _compute_line_metrics(
    lines: list[LineInput],
) -> list[tuple[float, float]]:
    metrics: list[tuple[float, float]] = []
    multi_indices: list[int] = []

    for i, line in enumerate(lines):
        sylls = line.syllables
        if len(sylls) >= 2:
            pts = [(_center_x(s.boundary), _bottom_y(s.boundary)) for s in sylls]
            metrics.append(_fit_line(pts))
            multi_indices.append(i)
        elif len(sylls) == 1:
            cx = _center_x(sylls[0].boundary)
            by = _bottom_y(sylls[0].boundary)
            metrics.append((0.0, by - 0.0 * cx))
        else:
            ys = [pt[1] for pt in line.boundary] if line.boundary else [0]
            mid_y = (min(ys) + max(ys)) / 2 if ys else 0
            metrics.append((0.0, float(mid_y)))

    if multi_indices:
        for i, line in enumerate(lines):
            if 0 < len(line.syllables) < 2:
                nearest_i = min(
                    multi_indices,
                    key=lambda mi: abs(metrics[i][1] - metrics[mi][1]),
                )
                inherited_slope = metrics[nearest_i][0]
                cx = _center_x(line.syllables[0].boundary)
                by = _bottom_y(line.syllables[0].boundary)
                metrics[i] = (inherited_slope, by - inherited_slope * cx)

    return metrics


def _find_owning_line(
    neume_x: float,
    neume_y: float,
    line_metrics: list[tuple[float, float]],
    order_top_to_bottom: list[int],
) -> int:
    for idx in order_top_to_bottom:
        slope, intercept = line_metrics[idx]
        line_y_at_neume = slope * neume_x + intercept
        if neume_y <= line_y_at_neume:
            return idx
    return order_top_to_bottom[-1]


def _find_closest_syllable(
    neume_x: float, syllables: list[SyllableInput]
) -> int:
    sorted_with_idx = sorted(
        range(len(syllables)),
        key=lambda i: _center_x(syllables[i].boundary),
    )
    left_of_neume = [
        i for i in sorted_with_idx if _min_x(syllables[i].boundary) <= neume_x
    ]
    if left_of_neume:
        return left_of_neume[-1]
    return sorted_with_idx[0]


def _fit_line(points: list[tuple[float, float]]) -> tuple[float, float]:
    n = len(points)
    sum_x = sum(p[0] for p in points)
    sum_y = sum(p[1] for p in points)
    sum_xy = sum(p[0] * p[1] for p in points)
    sum_x2 = sum(p[0] * p[0] for p in points)
    denom = n * sum_x2 - sum_x * sum_x
    if abs(denom) < 1e-10:
        return (0.0, sum_y / n)
    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    return (slope, intercept)


def _min_x(polygon: list[list[int]]) -> float:
    return min(pt[0] for pt in polygon) if polygon else 0.0


def _center_x(polygon: list[list[int]]) -> float:
    if not polygon:
        return 0.0
    xs = [pt[0] for pt in polygon]
    return (min(xs) + max(xs)) / 2


def _bottom_y(polygon: list[list[int]]) -> float:
    return max(pt[1] for pt in polygon) if polygon else 0.0


# ---------------------------------------------------------------------------
# Canonical serializer
# ---------------------------------------------------------------------------


def _serialize_canonical(root: ET.Element) -> bytes:
    """Serialize an ElementTree to canonical pretty-printed UTF-8 MEI bytes.

    Format:
      - <?xml version='1.0' encoding='UTF-8'?> declaration
      - 2-space indentation, LF line endings
      - Single xmlns on root
      - Attributes sorted alphabetically by qualified name
      - Self-closing for empty elements
      - Trailing newline
    """
    parts = ["<?xml version='1.0' encoding='UTF-8'?>"]
    _emit_element(root, indent=0, out=parts, default_ns_declared=False)
    return ("\n".join(parts) + "\n").encode("utf-8")


def _emit_element(
    el: ET.Element,
    indent: int,
    out: list[str],
    default_ns_declared: bool,
) -> None:
    pad = "  " * indent
    tag = _local(el.tag)

    attrs: list[tuple[str, str]] = []
    if not default_ns_declared and el.tag.startswith(_MEI):
        attrs.append(("xmlns", MEI_NS))
        default_ns_declared = True

    for raw_name, raw_val in el.attrib.items():
        name = _attr_display_name(raw_name)
        attrs.append((name, raw_val))

    attrs.sort(key=lambda kv: kv[0])
    attr_str = "".join(f' {k}="{_escape_attr(v)}"' for k, v in attrs)

    children = list(el)
    text = (el.text or "").strip()

    if not children and not text:
        out.append(f"{pad}<{tag}{attr_str}/>")
        return

    if children:
        out.append(f"{pad}<{tag}{attr_str}>")
        for child in children:
            _emit_element(child, indent + 1, out, default_ns_declared)
        out.append(f"{pad}</{tag}>")
    else:
        out.append(f"{pad}<{tag}{attr_str}>{_escape_text(text)}</{tag}>")


def _attr_display_name(raw: str) -> str:
    if raw.startswith(f"{{{XML_NS}}}"):
        return "xml:" + raw[len(f"{{{XML_NS}}}") :]
    if raw.startswith("{"):
        return raw.rsplit("}", 1)[-1]
    return raw


def _escape_attr(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _escape_text(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
