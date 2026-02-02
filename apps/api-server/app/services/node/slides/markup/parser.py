"""
Markup parser for Gamma-like slide markup language (SML - Slide Markup Language).

Supports XML-style tags or JSON format for slide definition.
"""

import xml.etree.ElementTree as ET
import json
from typing import Dict, List, Any, Union


class SlideMarkupParser:
    """Parser for Slide Markup Language (SML) - inspired by Gamma's GML."""

    def parse(self, markup: Union[str, dict]) -> Dict[str, Any]:
        """
        Parse markup into structured slide data.

        Args:
            markup: Either XML string, JSON string, or dict

        Returns:
            Structured slide data with sections and blocks
        """
        if isinstance(markup, dict):
            return self._parse_dict(markup)

        # Try parsing as JSON first
        try:
            data = json.loads(markup)
            return self._parse_dict(data)
        except (json.JSONDecodeError, TypeError):
            pass

        # Parse as XML
        return self._parse_xml(markup)

    def _parse_xml(self, xml_string: str) -> Dict[str, Any]:
        """Parse XML markup string."""
        try:
            root = ET.fromstring(xml_string)
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML markup: {e}")

        if root.tag != "slide":
            raise ValueError("Root element must be <slide>")

        slide_data = {"id": root.get("id", "slide_1"), "sections": []}

        for section in root.findall("section"):
            section_data = self._parse_section_xml(section)
            slide_data["sections"].append(section_data)

        return slide_data

    def _parse_section_xml(self, element: ET.Element) -> Dict[str, Any]:
        """Parse a <section> element."""
        section_data = {"purpose": element.get("purpose", "content"), "blocks": []}

        for child in element:
            block = self._parse_block_xml(child)
            if block:
                section_data["blocks"].append(block)

        return section_data

    def _parse_block_xml(self, element: ET.Element) -> Dict[str, Any]:
        """Parse individual block elements."""
        tag = element.tag

        # Basic text blocks
        if tag == "heading":
            return {
                "type": "heading",
                "level": int(element.get("level", "2")),
                "text": element.text or "",
            }

        elif tag == "paragraph":
            return {"type": "paragraph", "text": element.text or ""}

        # Timeline block
        elif tag == "timeline":
            events = []
            for event in element.findall("event"):
                events.append(
                    {"year": event.get("year", ""), "description": event.text or ""}
                )
            return {"type": "timeline", "events": events}

        # Smart layouts
        elif tag == "smart-layout":
            layout_type = element.get("type", "bigBullets")
            return self._parse_smart_layout_xml(element, layout_type)

        # Diagrams
        elif tag == "diagram":
            diagram_type = element.get("type", "venn")
            return self._parse_diagram_xml(element, diagram_type)

        # Columns
        elif tag == "columns":
            colwidths_str = element.get("colwidths", "[50,50]")
            colwidths = json.loads(colwidths_str)
            columns = []
            for col in element.findall("div"):
                col_blocks = []
                for child in col:
                    block = self._parse_block_xml(child)
                    if block:
                        col_blocks.append(block)
                columns.append(col_blocks)

            return {"type": "columns", "widths": colwidths, "columns": columns}

        # Image
        elif tag == "img":
            return {
                "type": "image",
                "url": element.get("data-id", ""),
                "fullwidth": element.get("fullwidthblock", "false") == "true",
                "caption": element.get("alt", ""),
            }

        # Divider
        elif tag == "divider":
            return {"type": "divider"}

        # Callout/Alert
        elif tag == "callout" or tag == "alert":
            return {
                "type": "takeaway",
                "text": element.text or "",
                "label": element.get("label", "Key Takeaway"),
                "variant": element.get("type", "info"),
            }

        # Table
        elif tag == "table":
            return self._parse_table_xml(element)

        return None

    def _parse_smart_layout_xml(
        self, element: ET.Element, layout_type: str
    ) -> Dict[str, Any]:
        """Parse smart layout elements."""
        if layout_type == "bigBullets":
            items = []
            for item in element.findall("item"):
                items.append(
                    {"text": item.text or "", "icon": item.get("icon", "ri-check-line")}
                )
            return {"type": "smart_layout_bullets", "items": items}

        elif layout_type == "processSteps":
            steps = []
            for i, item in enumerate(element.findall("item")):
                steps.append({"number": f"{i+1:02d}", "text": item.text or ""})
            return {"type": "step_list", "steps": steps}

        elif layout_type == "timeline":
            events = []
            for item in element.findall("item"):
                events.append(
                    {"year": item.get("year", ""), "description": item.text or ""}
                )
            return {"type": "timeline", "events": events}

        elif layout_type == "stats":
            stats = []
            for stat in element.findall("stat"):
                stats.append(
                    {"value": stat.get("value", ""), "label": stat.get("label", "")}
                )
            return {"type": "stats_grid", "stats": stats}

        return None

    def _parse_diagram_xml(
        self, element: ET.Element, diagram_type: str
    ) -> Dict[str, Any]:
        """Parse diagram elements."""
        if diagram_type == "venn":
            circles = []
            for circle in element.findall("circle"):
                circles.append(
                    {"label": circle.get("label", ""), "text": circle.text or ""}
                )
            return {"type": "diagram_venn", "circles": circles}

        elif diagram_type == "funnel":
            stages = []
            for stage in element.findall("stage"):
                stages.append(stage.text or "")
            return {"type": "diagram_funnel", "stages": stages}

        elif diagram_type == "flowchart":
            nodes = []
            edges = []
            for node in element.findall("node"):
                nodes.append(
                    {
                        "id": node.get("id", ""),
                        "type": node.get("type", "process"),
                        "text": node.text or "",
                    }
                )
            for edge in element.findall("edge"):
                edges.append(
                    {
                        "from": edge.get("from", ""),
                        "to": edge.get("to", ""),
                        "label": edge.get("label", ""),
                    }
                )
            return {"type": "diagram_flowchart", "nodes": nodes, "edges": edges}

        return None

    def _parse_table_xml(self, element: ET.Element) -> Dict[str, Any]:
        """Parse table element."""
        rows = []
        for tr in element.findall("tr"):
            cells = []
            for td in tr.findall("td"):
                cells.append(td.text or "")
            for th in tr.findall("th"):
                cells.append(th.text or "")
            if cells:
                rows.append(cells)

        return {"type": "table", "rows": rows}

    def _parse_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse dictionary/JSON format."""
        # If already in correct format, return as-is
        if "sections" in data:
            return data

        # Otherwise structure it
        return {"id": data.get("id", "slide_1"), "sections": data.get("sections", [])}
