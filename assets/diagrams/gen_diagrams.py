import base64

def b64(path):
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode()

FLUX_ICON = b64('/home/mfall/cloud-native/gitops-selfservice/assets/logos/flux.svg')
CROSSPLANE_ICON = b64('/home/mfall/cloud-native/gitops-selfservice/assets/logos/crossplane.svg')
K8S_ICON = b64('/home/mfall/cloud-native/gitops-selfservice/assets/logos/kubernetes.svg')

ACCENT = "#1f7a5c"
INK = "#16213e"
MUTED = "#6b7280"
CARD_BG = "#ffffff"
CARD_BORDER = "#e5e7eb"

# Conservative (generous) average glyph widths in px, at the given font sizes,
# for a bold/regular system-ui font — deliberately overestimated since this is
# never visually previewed before shipping.
TITLE_CHAR_W = 13.5   # at font-size 20, font-weight 700
SUB_CHAR_W = 10.5     # at font-size 16, font-weight 400
H_PAD = 28            # left/right internal padding (excluding icon)
ICON_COL_W = 62       # space reserved for the icon column when present
BOX_H = 90

def defs():
    return '''
  <defs>
    <filter id="shadow" x="-30%" y="-30%" width="160%" height="160%">
      <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#0f172a" flood-opacity="0.12"/>
    </filter>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#9aa0a6"/>
    </marker>
  </defs>
'''

def person(cx, cy, r, label):
    return f'''
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="#f3f4f6" stroke="{CARD_BORDER}" stroke-width="2"/>
  <circle cx="{cx}" cy="{cy-r*0.22}" r="{r*0.28}" fill="#6b7280"/>
  <path d="M {cx-r*0.5} {cy+r*0.55} Q {cx} {cy-r*0.05} {cx+r*0.5} {cy+r*0.55} L {cx+r*0.5} {cy+r*0.85} Q {cx} {cy+r*1.05} {cx-r*0.5} {cy+r*0.85} Z" fill="#6b7280"/>
  <text x="{cx}" y="{cy+r+28}" text-anchor="middle" font-family="system-ui,sans-serif" font-size="18" fill="{INK}" font-weight="600">{label}</text>
'''

def box_width(title, subtitle, has_icon):
    text_w = max(len(title) * TITLE_CHAR_W, len(subtitle or "") * SUB_CHAR_W)
    left = ICON_COL_W if has_icon else H_PAD
    return int(left + text_w + H_PAD)

def box(x, y, w, title, subtitle, icon_b64=None, accent=False):
    h = BOX_H
    border = f'stroke="{ACCENT}" stroke-width="3"' if accent else f'stroke="{CARD_BORDER}" stroke-width="1.5"'
    title_color = ACCENT if accent else INK
    text_x = x + (ICON_COL_W if icon_b64 else H_PAD)
    icon_svg = ""
    if icon_b64:
        isz = 40
        icon_svg = f'<image x="{x+18}" y="{y+h/2-isz/2}" width="{isz}" height="{isz}" href="data:image/svg+xml;base64,{icon_b64}"/>'
    if subtitle:
        title_y = y + h/2 - 6
        sub = f'<text x="{text_x}" y="{y+h/2+22}" font-family="system-ui,sans-serif" font-size="16" fill="{MUTED}">{subtitle}</text>'
    else:
        title_y = y + h/2 + 7
        sub = ""
    return f'''
  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{CARD_BG}" {border} filter="url(#shadow)"/>
  {icon_svg}
  <text x="{text_x}" y="{title_y}" font-family="system-ui,sans-serif" font-size="20" font-weight="700" fill="{title_color}">{title}</text>
  {sub}
'''

def arrow(x1, y1, x2, y2, label=None):
    lbl = ""
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2 - 12
        lbl = f'<text x="{mx}" y="{my}" text-anchor="middle" font-family="system-ui,sans-serif" font-size="16" fill="{MUTED}">{label}</text>'
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#9aa0a6" stroke-width="2" marker-end="url(#arrow)"/>{lbl}'

def svg_wrap(width, height, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
{defs()}
{body}
</svg>'''

def row(boxes_spec, y, gap=40, start_x=0):
    """boxes_spec: list of (title, subtitle, icon_b64_or_None, accent_bool). Returns (svg_body, centers, total_width)."""
    widths = [box_width(t, s, bool(ic)) for (t, s, ic, ac) in boxes_spec]
    total_w = sum(widths) + gap * (len(widths) - 1)
    body = []
    centers = []
    x = start_x
    for (t, s, ic, ac), w in zip(boxes_spec, widths):
        body.append(box(x, y, w, t, s, icon_b64=ic, accent=ac))
        centers.append(x + w / 2)
        x += w + gap
    return "\n".join(body), centers, total_w

def branch_diagram(person_label, arrow_label, api_title, top_title, top_sub, top_icon,
                    bottom_boxes, out_path, margin=60):
    row1_spec = [
        (api_title, None, K8S_ICON, False),
        (top_title, top_sub, top_icon, True),
    ]
    row1_body, row1_centers, row1_w = row(row1_spec, y=68, gap=50, start_x=0)
    row2_body, row2_centers, row2_w = row(bottom_boxes, y=280, gap=40, start_x=0)

    content_w = max(row1_w, row2_w)
    # center both rows within the widest one
    row1_offset = (content_w - row1_w) / 2
    row2_offset = (content_w - row2_w) / 2

    person_r = 55
    person_cx = margin + person_r
    person_x_right = person_cx + person_r

    total_w = margin + person_r * 2 + 90 + content_w + margin

    body = []
    body.append(person(person_cx, 110, person_r, person_label))
    api_x = person_x_right + 90 + row1_offset
    body.append(arrow(person_x_right + 10, 110, api_x - 8, 110, arrow_label))

    # shift row1/row2 bodies by the computed x offsets by re-emitting with offset
    def shifted_row(spec, y, offset, gap=40):
        widths = [box_width(t, s, bool(ic)) for (t, s, ic, ac) in spec]
        b = []
        centers = []
        x = offset
        for (t, s, ic, ac), w in zip(spec, widths):
            b.append(box(x, y, w, t, s, icon_b64=ic, accent=ac))
            centers.append(x + w / 2)
            x += w + gap
        return "\n".join(b), centers

    base_x = person_x_right + 90
    r1_body, r1_centers = shifted_row(row1_spec, 68, base_x + row1_offset, gap=50)
    r2_body, r2_centers = shifted_row(bottom_boxes, 280, base_x + row2_offset, gap=40)
    body.append(r1_body)
    body.append(r2_body)

    top_center = r1_centers[-1]
    body.append(f'<line x1="{top_center}" y1="158" x2="{top_center}" y2="220" stroke="#9aa0a6" stroke-width="2"/>')
    left_c, right_c = r2_centers[0], r2_centers[-1]
    body.append(f'<line x1="{left_c}" y1="220" x2="{right_c}" y2="220" stroke="#9aa0a6" stroke-width="2"/>')
    for cx in r2_centers:
        body.append(f'<line x1="{cx}" y1="220" x2="{cx}" y2="278" stroke="#9aa0a6" stroke-width="2" marker-end="url(#arrow)"/>')

    height = 430
    open(out_path, 'w').write(svg_wrap(int(total_w), height, "\n".join(body)))
    print(out_path, "width=", int(total_w))

branch_diagram(
    person_label="Développeur",
    arrow_label="flux bootstrap",
    api_title="Kubernetes API",
    top_title="Source Controller",
    top_sub="Git · Helm · OCI · Bucket · ArtifactGenerator",
    top_icon=FLUX_ICON,
    bottom_boxes=[
        ("Kustomize Controller", "applique les manifestes", None, False),
        ("Helm Controller", "gère les releases Helm", None, False),
        ("Notification Controller", "alertes (Slack, Discord…)", None, False),
    ],
    out_path='/home/mfall/cloud-native/gitops-selfservice/assets/diagrams/flux-controllers.svg',
)

branch_diagram(
    person_label="Développeur",
    arrow_label="applique un Claim",
    api_title="Kubernetes API",
    top_title="Crossplane (core)",
    top_sub="XRD + pipeline de Composition",
    top_icon=CROSSPLANE_ICON,
    bottom_boxes=[
        ("Functions", "gRPC, synchrone, dans le pipeline", None, False),
        ("Provider (provider-ovh)", "reconcile indépendant, async", None, False),
        ("RBAC Manager", "ClusterRoles par provider", None, False),
    ],
    out_path='/home/mfall/cloud-native/gitops-selfservice/assets/diagrams/crossplane-architecture.svg',
)
