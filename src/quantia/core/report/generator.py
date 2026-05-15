"""Report generation logic using Jinja2."""

from __future__ import annotations

import base64
from io import BytesIO
from typing import Optional, Dict, Any, List

import matplotlib.pyplot as plt
import seaborn as sns
from jinja2 import Template

from quantia.core.report.document import Document, Block, BlockType, PageSize
from quantia.ui.central.plot_styles import generate_style_code


REPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ doc.title }}</title>
    <style>
        @page {
            size: {{ doc.page_size.width_pt }}pt {{ doc.page_size.height_pt }}pt {{ doc.default_orientation }};
            margin: 0;
        }
        
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #E0E3E5; /* Match Canvas Background */
        }
        
        .page {
            position: relative;
            width: {{ page_width }}px;
            height: {{ page_height }}px;
            margin: 0 auto 50px auto;
            background-color: white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15); /* DTP Shadow */
            overflow: hidden;
            page-break-after: always;
            box-sizing: border-box;
        }
        
        @media print {
            body { background-color: white; padding: 0; }
            .page { margin: 0; box-shadow: none; page-break-after: always; }
        }
        
        .block {
            position: absolute;
            overflow: hidden;
            box-sizing: border-box;
        }
        
        h2 { margin: 0 0 5px 0; font-size: 14pt; color: #2D3E50; font-weight: bold; }
        
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 9pt;
        }
        
        th { background-color: #F8F9F9; padding: 6px; border: 1px solid #D5DBDB; text-align: left; }
        td { padding: 4px 6px; border: 1px solid #D5DBDB; }
        
        .plot-img {
            width: 100%;
            height: 100%;
            object-fit: contain;
        }
    </style>
</head>
<body>
    {% for page in pages %}
    <div class="page">
        {% for block in page.blocks|sort(attribute='z_order') %}
            <div class="block" style="left: {{ block.position.x }}px; top: {{ block.position.y }}px; width: {{ block.size.width }}px; height: {{ block.size.height }}px; z-index: {{ block.z_order }};">
                {% if block.type == "text" %}
                    <div style="font-family: '{{ block.content.font_family | default('Segoe UI') }}'; font-size: {{ block.content.font_size | default(10) }}pt; text-align: {{ block.content.alignment | default('Left') | lower }}; white-space: pre-wrap; width: 100%; height: 100%;">
                        {% if block.content.title %}<h2>{{ block.content.title }}</h2>{% endif %}
                        {{ block.content.text }}
                    </div>
                {% elif block.type == "bound_plot" %}
                    <img class="plot-img" src="data:image/png;base64,{{ block.content.image_b64 }}">
                {% elif block.type == "bound_table" %}
                    {% if block.content.title %}<h2>{{ block.content.title }}</h2>{% endif %}
                    {{ block.content.html_table | safe }}
                {% endif %}
            </div>
        {% endfor %}
    </div>
    {% endfor %}
</body>
</html>
"""

class ReportGenerator:
    """Generates DTP-style HTML from a Report Studio Document."""

    def __init__(self, doc: Document, df: Any) -> None:
        self.doc = doc
        self.df = df

    def render_block_plot(self, block: Block) -> str:
        """Render a plot to base64."""
        style_code = generate_style_code("Nature")
        fw = max(1, block.size.width / 100)
        fh = max(1, block.size.height / 100)
        fig, ax = plt.subplots(figsize=(fw, fh))
        
        try:
            # Temporary mock rendering since plot type is generic here in v1
            plot_type = block.content.get("plot_type", "Scatter")
            x_var = block.content.get("x_var")
            y_var = block.content.get("y_var")
            hue = block.content.get("hue")
            title = block.content.get("title")

            if plot_type == "Scatter":
                sns.scatterplot(data=self.df, x=x_var, y=y_var, hue=hue, ax=ax)
            elif plot_type == "Bar":
                sns.barplot(data=self.df, x=x_var, y=y_var, hue=hue, ax=ax)
            elif plot_type == "Line":
                sns.lineplot(data=self.df, x=x_var, y=y_var, hue=hue, ax=ax)
            elif plot_type == "Histogram":
                sns.histplot(data=self.df, x=x_var or y_var, hue=hue, kde=True, ax=ax)
            elif plot_type == "Box Plot":
                sns.boxplot(data=self.df, x=x_var, y=y_var, hue=hue, ax=ax)
            elif plot_type == "Violin":
                sns.violinplot(data=self.df, x=x_var, y=y_var, hue=hue, ax=ax)
            
            if title:
                ax.set_title(title)
                
            fig.tight_layout()
            buf = BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            plt.close(fig)
            return base64.b64encode(buf.getvalue()).decode('utf-8')
        except Exception:
            plt.close(fig)
            return "" 

    def generate_html(self) -> str:
        # Page size logic
        pw = self.doc.page_size.width_pt
        ph = self.doc.page_size.height_pt
        if self.doc.default_orientation == "landscape": pw, ph = ph, pw
        
        # We must clone the document's pages to inject rendering data (b64 images, HTML tables)
        # without polluting the domain model permanently, but here we just mutate the dictionary representation.
        render_pages = []
        
        for page in self.doc.pages:
            blocks_data = []
            for block in page.blocks:
                b_data = {
                    "type": block.type.value,
                    "position": {"x": block.position.x, "y": block.position.y},
                    "size": {"width": block.size.width, "height": block.size.height},
                    "z_order": block.z_order,
                    "content": block.content.copy()
                }
                
                if block.type == BlockType.BOUND_PLOT:
                    b_data["content"]["image_b64"] = self.render_block_plot(block)
                elif block.type == BlockType.BOUND_TABLE:
                    b_data["content"]["html_table"] = self._render_table(block)
                
                blocks_data.append(b_data)
            
            render_pages.append({"blocks": blocks_data})
            
        template = Template(REPORT_TEMPLATE)
        return template.render(
            doc=self.doc, 
            pages=render_pages, 
            page_width=pw, 
            page_height=ph
        )

    def _render_table(self, block: Block) -> str:
        """Render a table to HTML."""
        try:
            limit = block.content.get("rows_limit", 20)
            sub_df = self.df.head(limit)
            return sub_df.to_html(index=False, border=0, classes="table")
        except Exception:
            return "<p>Error rendering table.</p>"
