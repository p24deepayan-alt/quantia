# Quantia Report Studio — Feature & Architecture Specification

| | |
|---|---|
| **Document ID** | QNT-RSF-001 |
| **Version** | 1.0 (Draft) |
| **Date** | April 2026 |
| **Module** | Quantia Report Studio |
| **Status** | Design Specification |

---

## Table of Contents

1. [Vision and Positioning](#1-vision-and-positioning)
2. [Design Principles](#2-design-principles)
3. [Core Concepts and Mental Model](#3-core-concepts-and-mental-model)
4. [Feature Catalogue](#4-feature-catalogue)
5. [User Workflows](#5-user-workflows)
6. [Architecture Overview](#6-architecture-overview)
7. [Data Model](#7-data-model)
8. [Rendering Pipeline](#8-rendering-pipeline)
9. [File Format and Persistence](#9-file-format-and-persistence)
10. [Integration with the Rest of Quantia](#10-integration-with-the-rest-of-quantia)
11. [Technology Stack](#11-technology-stack)
12. [Module Layout](#12-module-layout)
13. [Performance Considerations](#13-performance-considerations)
14. [Edge Cases and Failure Modes](#14-edge-cases-and-failure-modes)
15. [Roadmap and Phasing](#15-roadmap-and-phasing)
16. [Open Questions](#16-open-questions)

---

## 1. Vision and Positioning

**Quantia Report Studio** is an integrated, page-based document composition environment that lives inside Quantia as a first-class tab alongside Data, Script, Results, Plots, and Dashboard. It lets users assemble publication-quality reports — research papers, lab reports, dissertation chapters, stakeholder briefs, conference posters — that combine free-form text with **live-bound** statistical results, tables, and plots produced elsewhere in the same project.

The reference point is Adobe PageMaker (and modern successors like InDesign, Affinity Publisher, Scribus), but with three critical differences that come from the statistical domain:

1. **Live data binding.** A table in the report can be bound to a regression result. Rerun the regression with new data, and the table updates everywhere it appears.
2. **Domain-aware blocks.** Native block types for things PageMaker never had — APA-formatted statistical results, citation references, equation rendering, auto-generated bibliography, footnotes with cross-references, captioned figures with auto-numbering.
3. **Reproducibility-first.** The report is part of the `.quantia` project file. Reopening the project a year later regenerates the report from the same data and the same script. Nothing is lost between machines or collaborators.

### 1.1 Why this matters for Quantia

Today, even with Quantia's PDF/HTML report generator, the typical workflow ends with the user copying outputs into Microsoft Word or LaTeX to assemble the final deliverable. That hand-off destroys reproducibility, introduces formatting errors, and forces users to leave Quantia. Report Studio closes that gap: the deliverable is produced inside Quantia, signed off inside Quantia, and reopened inside Quantia.

### 1.2 What Report Studio is *not*

- It is not a general-purpose page-layout tool. Marketing brochures, magazines, and book covers are out of scope.
- It is not a slide presentation tool. (That belongs in a separate Slide Studio module.)
- It is not an Office Word clone. It is a structured document composer aimed at reports that contain statistical content.
- It is not an academic typesetter — LaTeX-grade typography (kerning tables, microtypography, optical margin alignment) is explicitly deferred to LaTeX export.

---

## 2. Design Principles

Every feature decision is governed by these principles, in priority order:

1. **Bindings are sacred.** Once a result is bound to a block, the binding must survive every reasonable user action — edits, moves, renames, project re-opens, project sharing across machines. If a binding ever silently breaks, the user has lost trust in the tool.
2. **Default to publication-grade output.** Every block, every style, every template should look professional out of the box. Users should not need to learn typography to produce something they can submit.
3. **Two paths, never one.** Drag-and-drop is the primary path. A keyboard shortcut and menu equivalent exists for everything. Power users should never be forced to use the mouse.
4. **WYSIWYG, but not WYSIWYG-cosplay.** The canvas shows what will print. There is no "preview mode" toggle for layout — what you see is the actual page. (Distinct from "preview mode" which simply hides editing affordances like guides and handles.)
5. **Composable, not configurable.** Twenty well-designed block types beat a hundred poorly-designed ones with thirty options each. Users compose pages from a small, learnable vocabulary.
6. **Reproducible from source.** Any report should be regeneratable from data + script + report.json. No manual edits should be unreachable from the file.

---

## 3. Core Concepts and Mental Model

Users will interact with five concepts. Internalising these makes everything else explainable.

### 3.1 Document
A multi-page composition with metadata (title, author, citation style, page size). Persisted as part of the `.quantia` project. A project can contain multiple Documents (e.g., one for the paper, one for the supplementary materials).

### 3.2 Page
A single sheet of a Document, with size (A4, Letter, custom), orientation (portrait/landscape), margins, optional column grid, and a reference to a Master Page that supplies repeated elements (header, footer, page number).

### 3.3 Block
The atomic unit of content. A Block has a type (text, table, plot, image, equation, citation, etc.), position, size, type-specific content, and references to Styles. Some Blocks are **bound** — their content is linked to a workspace artefact and refreshes when that artefact changes.

### 3.4 Binding
A typed link from a Block to a Workspace artefact (a Result, a Plot, a derived table). Carries the artefact's identifier and a content hash. When the artefact changes, the Block becomes **stale** and offers a refresh.

### 3.5 Style
Named, reusable formatting recipes. Three families: **Paragraph styles** (e.g., "Body," "Heading 1," "Caption"), **Character styles** (e.g., "Emphasis," "Variable Name"), and **Table styles** (e.g., "APA Table," "Executive Summary"). Changing a style updates every Block that uses it.

```
┌─────────────────────────────────────────────────────────────┐
│                         DOCUMENT                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                       PAGES                           │  │
│  │  ┌──────────────────────────────────────────────────┐ │  │
│  │  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  │ │  │
│  │  │  │   BLOCK    │  │   BLOCK    │  │   BLOCK    │  │ │  │
│  │  │  │  (text)    │  │  (table)   │  │  (plot)    │  │ │  │
│  │  │  └────────────┘  └─────┬──────┘  └─────┬──────┘  │ │  │
│  │  │                        │                │         │ │  │
│  │  └────────────────────────┼────────────────┼────────┘ │  │
│  └───────────────────────────┼────────────────┼──────────┘  │
│                              │                │             │
│                       ┌──────▼────────────────▼─────┐       │
│                       │       BINDINGS              │       │
│                       │  (block ↔ workspace artefact)│      │
│                       └──────────────┬──────────────┘       │
│                                      │                      │
│  ┌───────────────────────────────────▼──────────────────┐   │
│  │              STYLES (paragraph, char, table)         │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
                ┌────────────────────┐
                │   WORKSPACE        │  ← rest of Quantia
                │   (results, plots) │
                └────────────────────┘
```

---

## 4. Feature Catalogue

### 4.1 Page and Layout Features

| Feature | Description |
|---|---|
| **Page sizes** | A0 through A6, US Letter, US Legal, Tabloid, custom width × height |
| **Orientation** | Portrait or landscape, per page |
| **Margins** | Top / bottom / left / right, with inside/outside for facing-page documents |
| **Columns** | 1–6 columns per page, with configurable gutter |
| **Master pages** | Reusable templates for headers, footers, page numbers, watermarks |
| **Facing pages** | Book-style two-page spreads with mirrored margins |
| **Section breaks** | Restart page numbering, change page size, switch master pages |
| **Bleed and slug areas** | For print-ready output |
| **Grid and guides** | Configurable baseline grid, document grid, user-drawn guides; snap-to with toggle |
| **Smart guides** | Alignment guides that appear while dragging |
| **Ruler units** | Inches, centimetres, millimetres, points, picas |
| **Page reordering** | Drag in the pages panel to reorder; auto-renumbering |
| **Page insertion** | Insert blank page, duplicate page, insert from template |

### 4.2 Block Types

Block types are organised into seven categories. Every block supports: drag-resize, alignment (left/right/centre/stretch), z-order, lock/unlock, hide/show, opacity, and rotation (for image and plot blocks only).

#### 4.2.1 Text Blocks
- **Paragraph text** — rich-text block with full character formatting
- **Heading** — H1 through H6, bound to a heading style; appears in outline and Table of Contents
- **Pull quote** — styled emphasised quotation
- **Callout / aside box** — coloured panel with optional icon
- **Code block** — monospace, syntax-highlighted (Python, R, SQL, plain)
- **Quote block** — indented blockquote with optional citation

#### 4.2.2 Data Blocks
- **Static table** — manually entered, fully editable cells
- **Bound table** — live-linked to a Workspace result (descriptive statistics, regression coefficients, ANOVA table, contingency table, etc.)
- **APA result line** — single-paragraph inline reporting of a test result (e.g., *"t(48) = 2.31, p = .025, d = 0.66"*) bound to a test
- **Statistical summary block** — auto-prose interpretation of a result, generated from the result metadata

#### 4.2.3 Figure Blocks
- **Bound plot** — links to a saved figure in the Plots tab; re-renders at export resolution
- **Image** — PNG, JPG, SVG inserted from file
- **Vector shape** — rectangle, ellipse, line, arrow, polygon for diagrams and annotations

#### 4.2.4 Structural Blocks
- **Caption** — auto-numbered ("Figure 1.", "Table 3.") and linked to the preceding figure or table
- **Cross-reference** — inline reference that updates if the target moves ("as shown in Figure 3" → renumbers if figures are reordered)
- **Page break** — forces a new page
- **Column break** — forces a new column
- **Section break** — see Page Features
- **Spacer** — explicit empty vertical or horizontal space

#### 4.2.5 Reference Blocks
- **Inline citation** — `(Smith, 2024)` or `[1]` depending on style; reflows automatically
- **Bibliography** — auto-generated reference list from all citations in the Document
- **Footnote** — anchored to text; renders at page bottom (numeric or symbolic)
- **Endnote** — anchored to text; renders in an endnotes section
- **Table of contents** — auto-generated from heading blocks
- **List of figures** — auto-generated from figure captions
- **List of tables** — auto-generated from table captions
- **Index** — auto-generated from indexed terms

#### 4.2.6 Math Blocks
- **Inline equation** — LaTeX-rendered math in a text flow
- **Display equation** — centred, optionally numbered ("(3.4)")
- **Equation reference** — cross-reference to a numbered equation

#### 4.2.7 Dynamic Blocks
- **Page number** — current page in numbering scheme
- **Total pages** — page count
- **Document variable** — `{{title}}`, `{{author}}`, `{{date}}`, `{{citation_style}}`, custom variables
- **Date/time stamp** — render date (configurable format)
- **Project metadata** — bind to project name, project version, last-modified date

### 4.3 Typography System

| Feature | Description |
|---|---|
| **Font selection** | Bundled fonts (Inter, Source Serif Pro, Source Sans Pro, Fira Code, Lora) plus system fonts |
| **Size and weight** | Full numeric size, 9 weights from Thin to Black |
| **Style** | Bold, italic, underline, strikethrough, overline |
| **Case transforms** | UPPERCASE, lowercase, Capitalise Each Word, Small Caps |
| **Spacing** | Letter-spacing (tracking), kerning toggle, line-height, paragraph spacing before/after |
| **Indentation** | First-line indent, hanging indent, left/right paragraph indent |
| **Alignment** | Left, right, centre, justify, full-justify-with-last-line-options |
| **Hyphenation** | Auto-hyphenation per language with override |
| **Drop caps** | Configurable line span and offset |
| **Lists** | Ordered (1., a., i., I.) and unordered with custom bullets |
| **Tab stops** | Custom positions with left/right/centre/decimal alignment |
| **Superscript / subscript** | One-click, with proper Unicode where available |

### 4.4 Style System

Three style families, each defined once and applied many times:

**Paragraph styles** define block-level formatting (font family, size, weight, alignment, spacing, indents, line height). Examples: Body, Heading 1, Heading 2, Caption, Code, Block Quote.

**Character styles** define inline formatting (e.g., italic variable names, emphasised keywords, hyperlinks). Applied to selections within a paragraph.

**Table styles** define table-level formatting (borders, header shading, alternating rows, cell padding, header row repeat). Examples: APA Table, Executive Brief, Minimal, Grid.

Style features:
- **Inheritance** — styles can be based on another style; changes to the parent propagate.
- **Override badges** — local overrides on a Block are flagged so users know when content drifts from its style.
- **Style import/export** — share style sheets across Documents and projects.
- **Find by style** — locate every Block using a given style.
- **Replace style** — bulk swap one style for another.

### 4.5 Data Binding Features

This is Report Studio's central differentiator.

| Feature | Description |
|---|---|
| **Drag-to-bind** | Drag a result row, plot, or table from the Results/Plots tab onto the canvas to create a bound block |
| **Right-click insertion** | "Insert into Report → at cursor / new page / append" from Results / Plots context menu |
| **Binding indicators** | Small badge on every bound block: synced / stale / orphaned / locked |
| **Refresh on demand** | Per-block "Refresh from source" button; document-wide "Refresh all" |
| **Auto-refresh** | Optional setting: bindings refresh whenever the linked artefact changes |
| **Filter before display** | A bound table can declare a filter (e.g., show only rows where `p < 0.05`) |
| **Format overrides** | Visual styling on a bound block does not break the binding |
| **Convert to static** | Explicitly break a binding to "freeze" content |
| **Re-bind** | Replace a binding's target (useful when an analysis is rerun under a new name) |
| **Orphan recovery** | If a target is deleted, the block displays a placeholder with the last-known content and the original target name |
| **Binding inspector** | Right panel lists every bound block in the document, its source, sync state, and last refresh timestamp |

### 4.6 Template System

Templates are starter Documents shipped with the application or saved by users. Each template defines page sizes, master pages, styles, and a sample block arrangement.

**Built-in templates** at v1.0:
- APA 7 Research Paper
- APA 7 Short Report
- Lab / Experiment Report
- Executive Summary (one-pager)
- Statistical Brief (two-pager)
- Dissertation Chapter
- Conference Poster (A0 landscape)
- Survey Analysis Report
- Quarterly Insights Memo
- Generic Blank Document (no styles imposed)

Template features:
- **Save current as template** — turn any Document into a reusable template
- **Template gallery** — browseable thumbnails, preview before applying
- **Apply template to existing Document** — adopts styles and master pages while preserving content
- **Template import/export** — `.qntpl` files for sharing

### 4.7 Citations and Bibliography

| Feature | Description |
|---|---|
| **Citation styles** | APA 7, MLA 9, Chicago (Author-Date & Notes), Vancouver, Harvard, IEEE |
| **Reference library** | Per-project bibliography stored in `references.json` |
| **Reference editor** | Form-based entry for books, journal articles, conference papers, web sources, datasets |
| **BibTeX import** | Paste BibTeX or import `.bib` files |
| **CSL JSON support** | Use Citation Style Language for custom styles |
| **Inline citation insertion** | Cite > select from library > formatted citation inserted |
| **Bibliography auto-update** | Bibliography block lists exactly the works cited, in style order |
| **DOI / URL validation** | Warn on malformed references |

### 4.8 Export Formats

| Format | Engine | Notes |
|---|---|---|
| **PDF** | Direct QPainter→QPdfWriter | Vector-perfect, embeds fonts, ICC colour profiles |
| **DOCX** | python-docx with style mapping | Round-trippable; styles preserved where possible |
| **HTML** | Jinja2 template + embedded assets | Standalone single-file or asset-folder mode |
| **LaTeX** | Jinja2 template → `.tex` + figures | Compile with any TeX distribution |
| **Markdown** | Custom serialiser | Lossy but useful for blog/wiki publication |
| **PNG / JPG** | Page-at-a-time QPainter rasterisation | At configurable DPI |
| **EPUB** | _Deferred to v1.2_ | |
| **Print** | Native Qt printing | OS print dialog; supports PostScript, CUPS, Windows printing |

Export options exposed in every format:
- DPI for raster outputs (72/150/300/600)
- Embed vs link images
- Include/exclude bibliography
- Include/exclude appendix
- Page range
- Bleed marks and crop marks
- Greyscale conversion

### 4.9 Collaboration and Versioning (v1.1+)

| Feature | Description |
|---|---|
| **Track changes** | Per-block change history; accept/reject diffs |
| **Comments** | Threaded comments anchored to blocks or text ranges |
| **Version snapshots** | Manual or automatic snapshots; restore any past version |
| **Diff view** | Side-by-side comparison of two report versions |
| **Real-time co-editing** | Multi-user cursor and selection (post-v1.0) |

### 4.10 Accessibility

- **Reading order** — explicit ordering for screen readers, independent of visual layout
- **Alt text** — required on every image and plot block (warning if missing)
- **Tagged PDF export** — produces PDFs that pass PDF/UA accessibility checks
- **High-contrast preview** — temporarily render the canvas in a high-contrast palette to verify legibility
- **Keyboard-only operation** — every block can be inserted, edited, moved, and styled without the mouse

### 4.11 Power-User Features

| Feature | Description |
|---|---|
| **Command palette** | `Ctrl+Shift+P` to fuzzy-find any action |
| **Find and replace** | Across the whole Document, with regex and per-style filters |
| **Outline view** | Navigable document tree by heading; drag to reorder sections |
| **Selection groups** | Multi-select with `Ctrl+Click`; align, distribute, group operations |
| **Custom snippets** | Save block patterns as snippets for reuse |
| **Script hooks** | Python pre/post-export hooks for advanced automation |
| **Document variables** | Define `{{study_name}}` once; replace everywhere in one edit |

---

## 5. User Workflows

### 5.1 The "Quick Report" workflow

1. User runs a t-test in the Statistics menu.
2. In the Results pane, the result appears with a small **"Insert into Report"** button.
3. Clicking it opens Report Studio in a new tab with a fresh Document seeded from a template.
4. The result is placed on page 1 as a bound APA table plus an APA result line.
5. The user adds a heading above and a caption below.
6. `Ctrl+E` → Export PDF.

Total elapsed time: under two minutes.

### 5.2 The "Dissertation Chapter" workflow

1. User opens an existing project that already contains 15 analyses and 8 plots.
2. Opens Report Studio; selects the **Dissertation Chapter** template.
3. Drags analyses from the Results pane and plots from the Plots pane onto pages — each becomes a bound block.
4. Writes prose around them, inserting cross-references as needed ("as shown in Figure 4").
5. Defines a custom paragraph style for advisor-required body formatting.
6. Inserts citations from the project's reference library; bibliography auto-builds.
7. Exports DOCX for the advisor's review.
8. After advisor feedback, returns to Quantia, edits the prose, exports again — bindings still live, no manual recopying.

### 5.3 The "Data refresh" workflow

1. Two weeks later, the user receives 50 additional survey responses.
2. Imports the updated dataset; reruns the data-cleaning workflow.
3. All analyses re-execute via the workflow engine.
4. In Report Studio, every bound block shows the **stale** badge.
5. User clicks "Refresh all bindings"; tables and plots update in place.
6. Caption numbers, cross-references, and bibliography are unaffected — the report is regenerated with the same structure but new numbers.
7. Re-exports the same PDF with new data, no manual edits required.

### 5.4 The "Collaboration" workflow (v1.1+)

1. Advisor opens the shared `.quantia` project.
2. Adds comments to specific blocks ("clarify this paragraph", "rerun with covariates added").
3. User addresses comments, marks them resolved.
4. Version snapshots let either side revert or compare against an earlier draft.

---

## 6. Architecture Overview

Report Studio is structured as five horizontal layers and one vertical concern (Bindings) that crosses all of them.

```
┌──────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                           │
│  ReportWindow │ Canvas (QGraphicsView/Scene) │ Panels │ Toolbar     │
└─────────────┬─────────────────────────────────────┬──────────────────┘
              │                                     │
┌─────────────▼─────────────────────────────────────▼──────────────────┐
│                        INTERACTION LAYER                             │
│  Selection │ Drag & Drop │ Resize Handles │ Inline Editing │ Undo   │
└─────────────┬─────────────────────────────────────┬──────────────────┘
              │                                     │
┌─────────────▼─────────────────────────────────────▼──────────────────┐
│                          DOMAIN LAYER                                │
│  Document │ Page │ Block │ Style │ MasterPage │ ReferenceLibrary    │
└─────────────┬─────────────────────────────────────┬──────────────────┘
              │                                     │
┌─────────────▼─────────────────────────────────────▼──────────────────┐
│                        SERVICES LAYER                                │
│  LayoutEngine │ TypographyEngine │ TableRenderer │ EquationRenderer │
│  CitationEngine │ ExportEngine │ TemplateManager │ StyleResolver    │
└─────────────┬─────────────────────────────────────┬──────────────────┘
              │                                     │
┌─────────────▼─────────────────────────────────────▼──────────────────┐
│                       PERSISTENCE LAYER                              │
│  ReportSerializer │ AssetStore │ WorkspaceBridge                    │
└──────────────────────────────────────────────────────────────────────┘

       ┌──────────────────────────────────────────────────────┐
       │            BINDING SUBSYSTEM (cross-cutting)         │
       │  BindingManager │ ResultResolver │ RefreshEngine     │
       │  StaleDetector │ OrphanHandler                       │
       └──────────────────────────────────────────────────────┘
```

### 6.1 Presentation Layer
The user-visible Qt widgets: the main `ReportWindow`, the editing `Canvas` (a `QGraphicsView` backed by a custom `QGraphicsScene`), the dockable side panels (Outline, Styles, Bindings, Block Library, Pages, Inspector), and a contextual top `Toolbar`.

### 6.2 Interaction Layer
Handles user input on the canvas — selection (single, marquee, modifier-key extension), drag-and-drop from panels and from external Quantia tabs, resize and rotate handles, inline text editing, and the undo/redo command stack.

### 6.3 Domain Layer
Pure-Python data classes that model the report structure. No Qt dependencies. This is what gets serialised to disk and what tests exercise. Every operation that modifies the domain goes through an undoable command, which keeps the undo stack consistent.

### 6.4 Services Layer
Stateless engines that compute things on top of the domain model:
- **LayoutEngine** computes positions for flowed content (text reflow across columns and pages, table row pagination).
- **TypographyEngine** wraps Qt's font metrics and text layout for precise positioning.
- **TableRenderer** produces visual table layouts from bound or static data with style application.
- **EquationRenderer** uses matplotlib's mathtext or an embedded MathJax/KaTeX bridge to render LaTeX.
- **CitationEngine** formats references via CSL.
- **ExportEngine** dispatches to per-format exporters.
- **TemplateManager** loads and applies templates.
- **StyleResolver** resolves a block's effective styling by walking inheritance.

### 6.5 Persistence Layer
- **ReportSerializer** writes/reads `report.json` and the styles file.
- **AssetStore** manages embedded images and fonts in the project ZIP.
- **WorkspaceBridge** is the thin API between Report Studio and the rest of Quantia (read-only access to results, plots, dataframes by identifier).

### 6.6 Binding Subsystem
Crosses every layer. Holds the binding registry (block_id → workspace artefact_id), computes content hashes to detect staleness, drives refreshes, and handles orphans gracefully.

---

## 7. Data Model

Domain classes in pure Python, serialised to JSON.

```python
@dataclass
class Document:
    document_id: UUID
    title: str
    authors: list[str]
    citation_style: str          # "apa7", "mla9", "chicago-author-date", ...
    created_at: datetime
    modified_at: datetime
    page_size: PageSize
    default_orientation: Orientation
    margins: Margins
    columns: ColumnConfig
    master_pages: list[MasterPage]
    pages: list[Page]
    style_sheet: StyleSheet
    reference_library: ReferenceLibrary
    document_variables: dict[str, str]    # {{author}} etc.

@dataclass
class Page:
    page_id: UUID
    index: int
    size: PageSize | None              # overrides Document default if set
    orientation: Orientation | None
    margins: Margins | None
    columns: ColumnConfig | None
    master_page_id: UUID | None
    blocks: list[Block]
    section_break: SectionBreak | None

@dataclass
class Block:
    block_id: UUID
    type: BlockType                     # Enum
    position: Point                     # (x, y) in document units
    size: Size                          # (width, height)
    rotation: float
    z_order: int
    locked: bool
    hidden: bool
    opacity: float
    paragraph_style_id: str | None
    character_style_overrides: list[CharacterStyleRun]
    content: BlockContent               # type-specific payload
    binding: Binding | None
    alt_text: str | None                # accessibility

@dataclass
class Binding:
    target_kind: BindingKind            # RESULT, PLOT, TABLE, DATAFRAME, VARIABLE
    target_id: str                      # workspace artefact identifier
    target_path: str | None             # for nested results (e.g., "regression.coefficients")
    content_hash: str                   # hash of last-known content
    last_refreshed_at: datetime
    auto_refresh: bool
    display_filter: dict | None         # e.g., {"where": "p_value < 0.05"}

@dataclass
class StyleSheet:
    paragraph_styles: dict[str, ParagraphStyle]
    character_styles: dict[str, CharacterStyle]
    table_styles: dict[str, TableStyle]

@dataclass
class ParagraphStyle:
    style_id: str
    name: str
    based_on: str | None
    font_family: str
    font_size_pt: float
    font_weight: int
    font_style: FontStyle               # NORMAL, ITALIC, OBLIQUE
    color: Color
    alignment: Alignment
    line_height_pt: float
    space_before_pt: float
    space_after_pt: float
    indent_first_line_pt: float
    indent_left_pt: float
    indent_right_pt: float
    keep_with_next: bool
    keep_together: bool
    hyphenation: bool
    list_format: ListFormat | None
    tab_stops: list[TabStop]
```

Block content payload varies by type. Examples:

```python
@dataclass
class TextBlockContent:
    text: str                           # plain text
    runs: list[FormattedRun]            # inline formatting overrides

@dataclass
class BoundTableBlockContent:
    # binding lives on the Block; this is layout/display info
    table_style_id: str
    column_widths: list[float]
    show_header: bool
    show_footer: bool
    decimal_places: int
    cell_overrides: list[CellOverride]  # local conditional formatting

@dataclass
class PlotBlockContent:
    fit_mode: PlotFitMode               # CONTAIN, COVER, STRETCH
    background: Color | None
    export_dpi: int
```

---

## 8. Rendering Pipeline

Two distinct render paths share a common foundation:

### 8.1 On-canvas rendering (interactive)
1. Each Block subclasses `QGraphicsItem` and implements `paint()`.
2. The `Canvas` is a `QGraphicsView` over a `QGraphicsScene` containing one `PageItem` per page, each of which contains its Block items as children.
3. Layout calculation happens lazily — when a Block is invalidated (content change, size change), its bounding rect is recomputed and the scene is partially repainted.
4. Off-viewport pages render at lower quality (or skip) for scroll performance.
5. Bound blocks cache their rendered content (e.g., a table's row layout) until the binding hash changes.

### 8.2 Export rendering (deterministic, high-fidelity)

**For PDF:**
1. Create a `QPdfWriter` set to the document's page size and DPI.
2. Create a `QPainter` on the writer.
3. For each page: replicate the rendering done on canvas, but with high-DPI raster targets and vector geometry preserved.
4. Plot blocks re-render their underlying matplotlib figure at export DPI rather than using the cached on-canvas pixmap.
5. Embed all used fonts (subset for size); apply ICC colour profile if specified.
6. Add tagged PDF structure for accessibility (headings, reading order, alt text).

**For DOCX:**
1. Translate the Document model into a `python-docx` Document.
2. Map paragraph styles to Word styles (preserved with `style.priority` and `style.unhide_when_used`).
3. Bound tables become native Word tables (not images), preserving copy-paste and edit-after-export.
4. Plot blocks export as PNG at 300 DPI and are inserted as inline images with alt text.
5. Captions and cross-references use Word's native field codes so Word's "Update Fields" command keeps them consistent.

**For HTML:**
1. Render via Jinja2 templates — one template per block type, composed into the page layout.
2. Bundle CSS that mirrors the style sheet.
3. Single-file mode inlines images as Base64; asset-folder mode emits a sibling folder.
4. Optional: emit as static-site Markdown→HTML for blog publication.

**For LaTeX:**
1. Emit a `.tex` file using a Jinja2 template that wraps the document class (`article`, `report`, or a journal-specific class).
2. Map paragraph styles to LaTeX environments / commands.
3. Plot blocks export as PDF or EPS and reference via `\includegraphics`.
4. Bibliography emitted as `.bib` and referenced with `\bibliography{}`.
5. Caveat documented to users: LaTeX export is one-way (changes after export don't sync back).

---

## 9. File Format and Persistence

### 9.1 Project File Structure

The `.quantia` ZIP project gains a top-level `report/` folder. Multiple Documents per project supported.

```
my_project.quantia          (ZIP archive)
├── manifest.json            # project metadata, format version
├── data/
│   └── dataset.parquet
├── script/
│   └── script.py
├── workflow/
│   └── workflow.json
├── results/
│   ├── <result_id>.json     # serialised analysis outputs
│   └── ...
├── plots/
│   ├── <plot_id>.png
│   └── <plot_id>.matplotlib.pkl  # for re-rendering at export DPI
├── report/
│   ├── manifest.json        # list of Documents
│   ├── documents/
│   │   ├── <document_id>.json
│   │   └── ...
│   ├── styles/
│   │   └── <document_id>.styles.json
│   ├── references/
│   │   └── <document_id>.references.json
│   └── assets/
│       ├── images/
│       └── fonts/           # only if non-bundled fonts used
└── history/
    └── snapshots/           # version snapshots
```

### 9.2 Schema Versioning
Every JSON payload carries `"schema_version": "1.0"`. Loaders implement progressive migration so a 0.9-era report opens in a 1.0+ application.

### 9.3 Auto-Save
- Domain mutations push commands onto an undo stack.
- A background timer flushes changed Documents to disk every 60 seconds.
- The most recent five auto-saves are retained as recovery checkpoints.

### 9.4 Asset Embedding
- Images dropped onto the canvas are copied into `report/assets/images/` with content-addressed filenames (`<sha256>.png`).
- Same hash → same file → de-duplicates automatically.
- Optional "linked, not embedded" mode for users with external asset pipelines.

---

## 10. Integration with the Rest of Quantia

### 10.1 The Workspace Bridge

Report Studio reads from the Workspace through a thin, read-only API:

```python
class WorkspaceBridge:
    def list_results(self) -> list[ResultDescriptor]: ...
    def get_result(self, result_id: str) -> ResultPayload: ...
    def get_result_hash(self, result_id: str) -> str: ...
    def list_plots(self) -> list[PlotDescriptor]: ...
    def get_plot(self, plot_id: str) -> PlotPayload: ...
    def get_dataframe(self, df_id: str) -> pd.DataFrame: ...
    def subscribe(self, callback: Callable[[Event], None]) -> Subscription: ...
```

The Workspace emits events when results / plots / dataframes change. The BindingManager subscribes and marks affected blocks stale.

### 10.2 Contextual entry points

Quantia surfaces "Insert into Report" actions from:

- **Results tab** — right-click any result → Insert into Report → New Report / Existing Report / At Cursor.
- **Plots tab** — same menu on each plot thumbnail.
- **Data tab** — "Send to Report" on a selected range or a pivot table output.
- **Statistics dialogs** — checkbox at the bottom: "Add result to current Report on OK".
- **Script Editor** — `quantia.report(...)` function that programmatically inserts blocks from a script.

### 10.3 Menu and Toolbar

A new top-level menu **Report** with:
- New Document (from template)
- Open Document
- Switch Document
- Manage Templates
- Manage Reference Library
- Export → PDF / DOCX / HTML / LaTeX / Markdown / PNG
- Refresh All Bindings
- Document Settings

The main toolbar gains a Report button alongside Data, Stats, ML, Visualize.

### 10.4 Tab vs Window

In v1.0 Report Studio is a **dockable tab** in the main window. In v1.1 it can be undocked into its own window (useful for multi-monitor use, e.g., data on one screen, report on the other).

---

## 11. Technology Stack

Strictly within the Python + SQL constraint already adopted by Quantia.

| Concern | Library | Rationale |
|---|---|---|
| **GUI** | PySide6 (Qt 6) | Already in use; QGraphicsView is mature for canvas work |
| **Canvas** | `QGraphicsView` + `QGraphicsScene` + custom `QGraphicsItem`s | Same pattern as the workflow canvas; fine-grained control |
| **Rich text** | `QTextDocument` inside text blocks | Native Qt rich text with fonts, runs, lists, hyperlinks |
| **Typography metrics** | `QFontMetricsF`, `QTextLayout` | Pixel-accurate measurement for layout |
| **Equations** | `matplotlib.mathtext` for inline; optional KaTeX in a `QWebEngineView` for higher fidelity | mathtext renders to pixmap; web engine for complex math |
| **Table rendering on canvas** | Custom `QGraphicsItem` drawing primitives | Avoid HTML round-trips inside the editor |
| **PDF export** | `QPdfWriter` + `QPainter` (primary), `reportlab` (fallback for fine control over tagged PDF) | Vector quality, font embedding, accessibility tags |
| **DOCX export** | `python-docx` | Standard; supports styles, tables, images, captions |
| **HTML export** | `Jinja2` templates | Familiar; easy to theme |
| **LaTeX export** | `Jinja2` templates targeting `.tex`; optionally `pylatex` | Round-trip not required; straight template emission |
| **Markdown export** | Custom serialiser | Lossy by design |
| **Plot rendering** | `matplotlib` (already in use) | Re-render at export DPI from the pickled Figure |
| **Image processing** | `Pillow` | Format conversions, resizing for embedded thumbnails |
| **Syntax highlighting** | `Pygments` | Code block colouring |
| **Citations** | `citeproc-py` for CSL processing; `bibtexparser` for `.bib` import | Standards-based citation formatting |
| **Bibliography database** | SQLite (within the project) | Aligns with the SQL-only mandate; structured, queryable |
| **Font management** | `fontTools` for subsetting on PDF embed | Smaller exports, license compliance |
| **JSON schema validation** | `jsonschema` | Validate report.json on load to catch corruption early |
| **Undo / redo** | Custom command pattern; Qt's `QUndoStack` if integration is clean | Coalescing of rapid-fire edits |

---

## 12. Module Layout

The proposed Python module layout, slotting into the existing `src/quantia/` structure.

```
src/quantia/
├── core/
│   ├── report/
│   │   ├── __init__.py
│   │   ├── document.py              # Document, Page domain classes
│   │   ├── blocks.py                # Block dataclasses for every type
│   │   ├── styles.py                # ParagraphStyle, CharacterStyle, TableStyle
│   │   ├── binding.py               # Binding, BindingManager
│   │   ├── master_page.py
│   │   ├── reference_library.py
│   │   ├── undo_commands.py         # AddBlock, MoveBlock, EditText, ...
│   │   └── workspace_bridge.py
│   └── ...
├── ui/
│   └── report/
│       ├── __init__.py
│       ├── report_window.py         # Main dockable tab
│       ├── canvas/
│       │   ├── view.py              # QGraphicsView
│       │   ├── scene.py             # QGraphicsScene + page layout
│       │   ├── page_item.py         # Per-page background, margins, columns
│       │   ├── grid.py
│       │   ├── guides.py
│       │   ├── rulers.py
│       │   ├── selection.py
│       │   ├── handles.py           # Resize/rotate handles
│       │   └── interactions.py      # Drag-and-drop handlers
│       ├── blocks/                  # QGraphicsItem subclasses
│       │   ├── base.py
│       │   ├── text_item.py
│       │   ├── heading_item.py
│       │   ├── static_table_item.py
│       │   ├── bound_table_item.py
│       │   ├── apa_result_item.py
│       │   ├── plot_item.py
│       │   ├── image_item.py
│       │   ├── shape_item.py
│       │   ├── caption_item.py
│       │   ├── cross_ref_item.py
│       │   ├── citation_item.py
│       │   ├── bibliography_item.py
│       │   ├── footnote_item.py
│       │   ├── toc_item.py
│       │   ├── lof_lot_item.py
│       │   ├── equation_item.py
│       │   ├── code_item.py
│       │   ├── page_number_item.py
│       │   └── variable_item.py
│       ├── panels/
│       │   ├── outline.py           # Heading-based document tree
│       │   ├── pages.py             # Thumbnail page navigator
│       │   ├── styles.py            # Style manager
│       │   ├── bindings.py          # Bindings inspector
│       │   ├── block_library.py     # Drag-to-canvas library
│       │   ├── references.py       # Reference editor
│       │   └── inspector.py         # Per-block property panel
│       ├── dialogs/
│       │   ├── document_settings.py
│       │   ├── master_page_editor.py
│       │   ├── style_editor.py
│       │   ├── table_style_editor.py
│       │   ├── reference_editor.py
│       │   ├── template_gallery.py
│       │   ├── export_pdf.py
│       │   ├── export_docx.py
│       │   ├── export_html.py
│       │   └── export_latex.py
│       ├── toolbar.py               # Contextual top toolbar
│       └── theming.py
├── services/
│   └── report/
│       ├── layout_engine.py         # Text reflow, table pagination
│       ├── typography_engine.py
│       ├── table_renderer.py
│       ├── equation_renderer.py
│       ├── citation_engine.py
│       ├── style_resolver.py
│       ├── template_manager.py
│       └── refresh_engine.py
├── export/
│   └── report/
│       ├── pdf_exporter.py
│       ├── docx_exporter.py
│       ├── html_exporter.py
│       ├── latex_exporter.py
│       ├── markdown_exporter.py
│       └── png_exporter.py
├── persistence/
│   └── report/
│       ├── serializer.py
│       ├── asset_store.py
│       └── schema/
│           ├── document.schema.json
│           └── styles.schema.json
└── templates/
    └── report/
        ├── apa7_paper.qntpl
        ├── apa7_short.qntpl
        ├── lab_report.qntpl
        ├── exec_summary.qntpl
        ├── dissertation_chapter.qntpl
        ├── conference_poster.qntpl
        ├── survey_report.qntpl
        └── blank.qntpl
```

---

## 13. Performance Considerations

### 13.1 Canvas responsiveness

- **Viewport culling.** Pages outside the visible viewport skip painting entirely.
- **Tile-level caching.** Large pages cache their backing pixmap; only invalidated tiles repaint on edits.
- **Lazy plot resolution.** Plot blocks render at screen DPI on canvas, not export DPI; export-quality rendering is deferred to export time.
- **Batched updates.** Multiple block mutations in a single user action coalesce into one scene update.

### 13.2 Refresh performance

- **Hash-based change detection.** Bindings store a content hash, not full content. Refresh checks are O(number of bindings), not O(content size).
- **Incremental refresh.** Refreshing one binding doesn't re-render the whole document — only that block's bounding rect.
- **Background prefetch.** When a result is updated in the workspace, the binding subsystem precomputes the new payload off the main thread so the refresh appears instant when the user clicks.

### 13.3 Export performance

- **Progressive PDF generation.** Pages export one at a time with a progress bar; user can cancel partway through.
- **Plot caching at export DPI.** Each unique (plot_id, dpi) pair is rendered once per export run.
- **Font subsetting.** Embedded fonts in PDF include only the glyphs actually used.

### 13.4 Memory limits

- **Image downscaling.** Embedded images larger than a configurable threshold are stored full-resolution but rendered on-canvas at downscaled cache.
- **Page count guidance.** Documents over 500 pages display a soft warning ("Reports of this size export slower; consider splitting into multiple Documents linked via cross-references").

---

## 14. Edge Cases and Failure Modes

| Scenario | Behaviour |
|---|---|
| Bound result is deleted from workspace | Block becomes an **orphan**; renders last-known content with a red badge; offers "Re-bind" or "Convert to static" |
| Bound result schema changes (column renamed, removed) | Block flagged as **schema mismatch**; dialog shows old vs new and prompts user to map columns or accept loss |
| Two bindings target the same artefact | Both stay in sync; no special handling needed |
| Plot block bound to a deleted figure | Orphan placeholder, as above |
| Project opened on a machine missing a font | Fall back to bundled equivalent (Inter for sans, Source Serif for serif, Fira Code for mono); warn once per missing font |
| Table doesn't fit on one page | Auto-paginate with repeating header row; user can override with "keep together" |
| Image too large to embed | Warn at 50 MB / image; refuse at 200 MB / image (suggest linking instead) |
| Circular cross-reference | Detected and warned; renders as broken-link placeholder |
| Citation style switched mid-document | All citations and the bibliography re-render in the new style; no manual cleanup required |
| Export fails midway | Partial output discarded; full error log written to `report/exports/last_error.log` |
| Concurrent edit conflict (v1.1+) | Last-writer-wins with conflict markers shown in the comment thread; manual merge dialog |
| Auto-save during a heavy operation | Defers to a quiet moment; never blocks the UI |
| Crash recovery | On next launch, prompt to recover from the most recent auto-save snapshot |
| Document opened from a future version | Read-only mode with a clear message; export still allowed |

---

## 15. Roadmap and Phasing

### Phase 1 — v1.0: "Reports that bind"
Minimum that ships:
- Canvas with multi-page documents, A4/Letter page sizes
- Block types: paragraph text, heading, static table, bound table, bound plot, image, caption, page number, page break
- Paragraph and character styles
- Three templates: Blank, APA Short Report, Executive Summary
- Bindings with refresh, stale detection, orphan handling
- Export to PDF (via QPdfWriter) and HTML
- Auto-save and recovery
- Outline panel, Pages panel, Styles panel, Bindings panel

### Phase 2 — v1.1: "Reports that scale"
- Block types: APA result line, citation, bibliography, cross-reference, table of contents, list of figures, list of tables, footnote, code block, equation
- Reference library and citation styles (APA 7, MLA 9, Chicago)
- Templates: Dissertation Chapter, Lab Report, Survey Report, Statistical Brief
- Export to DOCX
- Master pages and section breaks
- Document variables
- Track changes and version snapshots
- Comments

### Phase 3 — v1.2: "Reports that publish"
- Export to LaTeX and Markdown
- Conference Poster template (A0)
- Endnotes, index
- Custom CSL style import
- Tagged PDF for accessibility
- Find & replace with regex
- Snippets and reusable blocks

### Phase 4 — v2.0: "Reports that collaborate"
- Real-time co-editing with multi-user cursors
- Cloud-sync (optional, off by default to preserve offline guarantee)
- Template marketplace
- AI-assisted layout suggestions and prose generation (opt-in, fully local using a bundled small model)
- EPUB export
- Plugin API for custom block types

---

## 16. Open Questions

1. **Equation rendering fidelity vs dependency weight.** Should v1.0 ship matplotlib mathtext (already-bundled, limited LaTeX subset) or invest in a `QWebEngineView`-hosted KaTeX (full LaTeX, but adds ~80 MB to the installer)?
2. **Single vs multi-document per project.** Multi-document is more flexible; single-document is simpler to teach. Decision affects UI in Pages panel and the project file structure.
3. **DOCX round-tripping.** Should DOCX export be one-way (cleaner, simpler) or attempt round-trip (Word edits flow back into Quantia)? Round-trip is hard and rarely fully fidelity-preserving.
4. **Master page model.** InDesign-style master pages are powerful but conceptually heavy. Should v1.0 ship a simpler "header / footer / page number" model and reserve full master pages for v1.1?
5. **Bibliography source of truth.** Per-project or per-user? A user with 200 references shared across studies benefits from a global library; a user collaborating on one project benefits from project-local.
6. **Reflow vs frame-based text.** Frame-based (PageMaker-style) is what we've specified — text lives in fixed-size frames. Reflow (Word-style, text flows freely) is more familiar to academic users. Hybrid would mean two text-block modes; complexity cost is real.
7. **AI assistance.** Should v1.x include a local LLM ("explain this regression in plain English for the discussion section")? Strong feature; aligns poorly with "fully offline" if the model is too large to bundle.

---

## Appendix A — Glossary

| Term | Meaning |
|---|---|
| **Block** | The atomic unit of report content (text, table, plot, image, etc.) |
| **Binding** | A live link from a Block to a Workspace artefact |
| **Canvas** | The editable WYSIWYG document surface |
| **CSL** | Citation Style Language — XML/JSON format for defining citation styles |
| **Master Page** | A page template applied to one or more pages, supplying repeated elements |
| **Orphan** | A bound block whose source artefact no longer exists |
| **Stale** | A bound block whose source has changed since last refresh |
| **Style Sheet** | The collection of paragraph, character, and table styles defined for a Document |
| **Tagged PDF** | A PDF with structural metadata for accessibility (headings, reading order, alt text) |
| **WYSIWYG** | What You See Is What You Get — on-screen rendering matches print output |

---

## Appendix B — File Format Schema (Abbreviated)

```json
{
  "schema_version": "1.0",
  "document_id": "f3a1c2…",
  "title": "Effects of Sleep Deprivation on Working Memory",
  "authors": ["Reena Sharma", "Anand Kapoor"],
  "citation_style": "apa7",
  "created_at": "2026-04-15T10:23:00Z",
  "modified_at": "2026-04-18T14:11:00Z",
  "page_size": {"width_pt": 595, "height_pt": 842, "name": "A4"},
  "default_orientation": "portrait",
  "margins": {"top": 72, "bottom": 72, "left": 72, "right": 72},
  "columns": {"count": 1, "gutter_pt": 12},
  "master_pages": [ /* ... */ ],
  "pages": [
    {
      "page_id": "0a91…",
      "index": 0,
      "blocks": [
        {
          "block_id": "1f44…",
          "type": "heading",
          "position": {"x": 72, "y": 72},
          "size": {"width": 451, "height": 32},
          "z_order": 0,
          "paragraph_style_id": "Heading1",
          "content": {"text": "Results"}
        },
        {
          "block_id": "2c87…",
          "type": "bound_table",
          "position": {"x": 72, "y": 130},
          "size": {"width": 451, "height": 180},
          "z_order": 1,
          "paragraph_style_id": "Body",
          "content": {
            "table_style_id": "APATable",
            "show_header": true,
            "decimal_places": 3
          },
          "binding": {
            "target_kind": "RESULT",
            "target_id": "regression_001",
            "target_path": "coefficients",
            "content_hash": "8a3f…",
            "last_refreshed_at": "2026-04-18T14:08:00Z",
            "auto_refresh": false
          }
        }
      ]
    }
  ],
  "style_sheet": {
    "paragraph_styles": {
      "Body": { /* ... */ },
      "Heading1": { /* ... */ }
    },
    "character_styles": { /* ... */ },
    "table_styles": {
      "APATable": { /* ... */ }
    }
  },
  "document_variables": {
    "author": "Reena Sharma",
    "study_id": "PSY-2026-014"
  }
}
```

---

*End of specification.*
