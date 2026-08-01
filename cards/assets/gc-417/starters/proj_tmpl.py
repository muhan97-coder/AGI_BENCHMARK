"""proj_tmpl: tiny template renderer (gc-417 starter; seeded defects)."""


def render(template, ctx):
    out = []
    i = 0
    n = len(template)
    while i < n:
        ch = template[i]
        if ch == "{":
            j = template.find("}", i + 1)
            if j == -1:
                out.append(ch)
                i += 1
                continue
            path = template[i + 1:j]
            out.append(ctx[path])
            i = j + 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)
