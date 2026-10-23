#!/usr/bin/env python3
"""Export a checked diagram to a one-slide PowerPoint deck. Python 3.9+, standard library only.

Usage:
    python scripts/export-pptx.py <folder>/<slug>.svg [-o <out.pptx>] [--title "Slide title"] [--no-svg]
    python scripts/export-pptx.py <folder>/<slug>.png ...

Writes <slug>.pptx beside the input. The slide is 16:9 with the PNG fitted inside a
0.25 inch margin, aspect preserved. When the SVG is given and exists, it is embedded as
well (PowerPoint 2016 and later render it crisp at any zoom; older versions fall back to
the PNG). A plan.json beside the input supplies the theme: a dark plan gives the slide a
#0F172A background. No network, no packages, no PowerPoint needed to build the file.

The .pptx is a zip of OOXML parts written here by hand: content types, relationships,
presentation, one slide master, one blank layout, one theme, one slide, the media.
"""
import argparse
import datetime
import json
import re
import struct
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

EMU_PER_INCH = 914400
SLIDE_W, SLIDE_H = 12192000, 6858000          # 13.333 x 7.5 in, 16:9
MARGIN = 228600                               # 0.25 in
TITLE_H = 822960                              # 0.9 in band when --title is used

NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')
XML = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
EMPTY_TREE = ('<p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
              '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/>'
              '<a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>')


def png_size(data):
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise SystemExit('not a PNG file')
    w, h = struct.unpack('>II', data[16:24])
    return w, h


def svg_size(text):
    root = re.search(r'<svg[^>]*>', text)
    if not root:
        raise SystemExit('no <svg> root')
    w = re.search(r'\bwidth="(\d+(?:\.\d+)?)"', root.group(0))
    h = re.search(r'\bheight="(\d+(?:\.\d+)?)"', root.group(0))
    if not w or not h:
        raise SystemExit('<svg> root needs numeric width and height')
    return float(w.group(1)), float(h.group(1))


def fit(img_w, img_h, box_x, box_y, box_w, box_h):
    scale = min(box_w / img_w, box_h / img_h)
    w, h = int(img_w * scale), int(img_h * scale)
    return box_x + (box_w - w) // 2, box_y + (box_h - h) // 2, w, h


def theme_xml():
    fill = ('<a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
            '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
            '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst>')
    ln = ('<a:lnStyleLst>' + ''.join(
        f'<a:ln w="{w}" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
        '<a:prstDash val="solid"/></a:ln>' for w in (6350, 12700, 19050)) + '</a:lnStyleLst>')
    eff = '<a:effectStyleLst>' + '<a:effectStyle><a:effectLst/></a:effectStyle>' * 3 + '</a:effectStyleLst>'
    return (XML + '<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="ArchWeave">'
            '<a:themeElements><a:clrScheme name="ArchWeave">'
            '<a:dk1><a:srgbClr val="111827"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>'
            '<a:dk2><a:srgbClr val="1F2937"/></a:dk2><a:lt2><a:srgbClr val="F3F4F6"/></a:lt2>'
            '<a:accent1><a:srgbClr val="0F6CBD"/></a:accent1><a:accent2><a:srgbClr val="D97706"/></a:accent2>'
            '<a:accent3><a:srgbClr val="1E8A7E"/></a:accent3><a:accent4><a:srgbClr val="6D44C9"/></a:accent4>'
            '<a:accent5><a:srgbClr val="6B7280"/></a:accent5><a:accent6><a:srgbClr val="B91C1C"/></a:accent6>'
            '<a:hlink><a:srgbClr val="0F4C81"/></a:hlink><a:folHlink><a:srgbClr val="6D44C9"/></a:folHlink>'
            '</a:clrScheme><a:fontScheme name="ArchWeave">'
            '<a:majorFont><a:latin typeface="Segoe UI"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>'
            '<a:minorFont><a:latin typeface="Segoe UI"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont>'
            '</a:fontScheme><a:fmtScheme name="ArchWeave">' + fill + ln + eff +
            '<a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
            '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
            '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst>'
            '</a:fmtScheme></a:themeElements><a:objectDefaults/><a:extraClrSchemeLst/></a:theme>')


def master_xml():
    return (XML + f'<p:sldMaster {NS}><p:cSld><p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef></p:bg>'
            + EMPTY_TREE + '</p:spTree></p:cSld>'
            '<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" '
            'accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
            '<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>'
            '<p:txStyles><p:titleStyle><a:lvl1pPr><a:defRPr sz="2800" b="1"/></a:lvl1pPr></p:titleStyle>'
            '<p:bodyStyle><a:lvl1pPr><a:defRPr sz="1800"/></a:lvl1pPr></p:bodyStyle>'
            '<p:otherStyle><a:lvl1pPr><a:defRPr sz="1800"/></a:lvl1pPr></p:otherStyle></p:txStyles></p:sldMaster>')


def layout_xml():
    return (XML + f'<p:sldLayout {NS} type="blank" preserve="1"><p:cSld name="Blank">' + EMPTY_TREE +
            '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>')


def slide_xml(pic, title, dark, with_svg):
    x, y, w, h = pic
    bg = ('<p:bg><p:bgPr><a:solidFill><a:srgbClr val="0F172A"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>'
          if dark else '')
    shapes = ''
    if title:
        color = 'F1F5F9' if dark else '111827'
        shapes += (f'<p:sp><p:nvSpPr><p:cNvPr id="2" name="Title"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
                   f'<p:spPr><a:xfrm><a:off x="{MARGIN}" y="{MARGIN}"/><a:ext cx="{SLIDE_W - 2 * MARGIN}" cy="{TITLE_H}"/></a:xfrm>'
                   '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>'
                   '<p:txBody><a:bodyPr anchor="ctr" wrap="square"><a:normAutofit/></a:bodyPr><a:lstStyle/>'
                   f'<a:p><a:r><a:rPr lang="en-US" sz="2800" b="1"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
                   f'<a:latin typeface="Segoe UI"/></a:rPr><a:t>{escape(title)}</a:t></a:r></a:p></p:txBody></p:sp>')
    svg_ext = ('<a:extLst><a:ext uri="{96DAC541-7B7A-43D3-8B79-37D633B846F1}">'
               '<asvg:svgBlip xmlns:asvg="http://schemas.microsoft.com/office/drawing/2016/SVG/main" r:embed="rId3"/>'
               '</a:ext></a:extLst>') if with_svg else ''
    shapes += (f'<p:pic><p:nvPicPr><p:cNvPr id="3" name="Diagram"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr>'
               f'<p:nvPr/></p:nvPicPr><p:blipFill><a:blip r:embed="rId2">{svg_ext}</a:blip><a:stretch><a:fillRect/></a:stretch>'
               f'</p:blipFill><p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm>'
               '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>')
    return (XML + f'<p:sld {NS}><p:cSld>{bg}' + EMPTY_TREE + shapes + '</p:spTree></p:cSld>'
            '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')


def rels(pairs):
    body = ''.join(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/{typ}" Target="{tgt}"/>'
                   for rid, typ, tgt in pairs)
    return XML + f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{body}</Relationships>'


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('diagram', help='<slug>.svg (PNG must sit beside it) or <slug>.png')
    ap.add_argument('-o', '--out', help='output .pptx (default: <slug>.pptx beside the input)')
    ap.add_argument('--title', default='', help='optional title band above the diagram')
    ap.add_argument('--no-svg', action='store_true', help='embed the PNG only')
    args = ap.parse_args()

    src = Path(args.diagram)
    if src.suffix.lower() == '.svg':
        svg_path, png_path = src, src.with_suffix('.png')
    elif src.suffix.lower() == '.png':
        svg_path, png_path = src.with_suffix('.svg'), src
    else:
        raise SystemExit('input must be .svg or .png')
    if not png_path.exists():
        raise SystemExit(f'{png_path} not found; render the PNG first (render-png or the checker with cairosvg)')
    png = png_path.read_bytes()
    img_w, img_h = png_size(png)
    with_svg = (not args.no_svg) and svg_path.exists()
    svg = svg_path.read_bytes() if with_svg else None

    dark = False
    title = args.title
    plan_path = src.parent / 'plan.json'
    if plan_path.exists():
        try:
            meta = json.loads(plan_path.read_text(encoding='utf-8')).get('meta', {})
            dark = meta.get('theme') == 'dark'
        except Exception:
            pass

    top = MARGIN + (TITLE_H + MARGIN if title else 0)
    pic = fit(img_w, img_h, MARGIN, top, SLIDE_W - 2 * MARGIN, SLIDE_H - top - MARGIN)

    out = Path(args.out) if args.out else src.with_suffix('.pptx')
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    ct_svg = '<Default Extension="svg" ContentType="image/svg+xml"/>' if with_svg else ''
    content_types = (XML + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                     '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                     '<Default Extension="xml" ContentType="application/xml"/>'
                     '<Default Extension="png" ContentType="image/png"/>' + ct_svg +
                     '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
                     '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>'
                     '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>'
                     '<Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
                     '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
                     '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
                     '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
                     '</Types>')
    presentation = (XML + f'<p:presentation {NS} saveSubsetFonts="1">'
                    '<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>'
                    '<p:sldIdLst><p:sldId id="256" r:id="rId2"/></p:sldIdLst>'
                    f'<p:sldSz cx="{SLIDE_W}" cy="{SLIDE_H}"/><p:notesSz cx="6858000" cy="9144000"/>'
                    '<p:defaultTextStyle><a:defPPr><a:defRPr lang="en-US"/></a:defPPr></p:defaultTextStyle></p:presentation>')
    core = (XML + '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f'<dc:title>{escape(title or src.stem)}</dc:title><dc:creator>ArchWeave</dc:creator>'
            f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
            f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified></cp:coreProperties>')
    app = (XML + '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
           '<Application>ArchWeave</Application><Slides>1</Slides></Properties>')
    slide_rels = [('rId1', 'officeDocument/2006/relationships/slideLayout', '../slideLayouts/slideLayout1.xml'),
                  ('rId2', 'officeDocument/2006/relationships/image', '../media/image1.png')]
    if with_svg:
        slide_rels.append(('rId3', 'officeDocument/2006/relationships/image', '../media/image1.svg'))

    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', content_types)
        z.writestr('_rels/.rels', rels([
            ('rId1', 'officeDocument/2006/relationships/officeDocument', 'ppt/presentation.xml'),
            ('rId2', 'package/2006/relationships/metadata/core-properties', 'docProps/core.xml'),
            ('rId3', 'officeDocument/2006/relationships/extended-properties', 'docProps/app.xml')]))
        z.writestr('docProps/core.xml', core)
        z.writestr('docProps/app.xml', app)
        z.writestr('ppt/presentation.xml', presentation)
        z.writestr('ppt/_rels/presentation.xml.rels', rels([
            ('rId1', 'officeDocument/2006/relationships/slideMaster', 'slideMasters/slideMaster1.xml'),
            ('rId2', 'officeDocument/2006/relationships/slide', 'slides/slide1.xml'),
            ('rId3', 'officeDocument/2006/relationships/theme', 'theme/theme1.xml')]))
        z.writestr('ppt/slideMasters/slideMaster1.xml', master_xml())
        z.writestr('ppt/slideMasters/_rels/slideMaster1.xml.rels', rels([
            ('rId1', 'officeDocument/2006/relationships/slideLayout', '../slideLayouts/slideLayout1.xml'),
            ('rId2', 'officeDocument/2006/relationships/theme', '../theme/theme1.xml')]))
        z.writestr('ppt/slideLayouts/slideLayout1.xml', layout_xml())
        z.writestr('ppt/slideLayouts/_rels/slideLayout1.xml.rels', rels([
            ('rId1', 'officeDocument/2006/relationships/slideMaster', '../slideMasters/slideMaster1.xml')]))
        z.writestr('ppt/theme/theme1.xml', theme_xml())
        z.writestr('ppt/slides/slide1.xml', slide_xml(pic, title, dark, with_svg))
        z.writestr('ppt/slides/_rels/slide1.xml.rels', rels(slide_rels))
        z.writestr('ppt/media/image1.png', png)
        if with_svg:
            z.writestr('ppt/media/image1.svg', svg)

    kind = 'PNG + SVG' if with_svg else 'PNG'
    print(f'PPTX {out} ({out.stat().st_size} bytes, 16:9, {kind}, {"dark" if dark else "light"} slide'
          f'{", title" if title else ""})')


if __name__ == '__main__':
    main()
