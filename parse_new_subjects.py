import pdfplumber, re, json, sys
sys.stdout.reconfigure(encoding='utf-8')

def get_pages(path):
    pages = []
    with pdfplumber.open(path) as pdf:
        for p in pdf.pages:
            pages.append(p.extract_text() or '')
    return pages

def clean(s):
    s = re.sub(r'\(cid:\d+\)', ' ', s)
    s = re.sub(r'https?://\S+', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

# ============================================================
# ÁLGEBRA  (36 pages = 2 exams × 6 temas; renumber 1-12)
# ============================================================
pages_alg = get_pages(r'D:\UBA\Álgebra\Segundo Parcial\Álgebra Segundo Parcial 12 Temas.pdf')
full_alg = '\n===PAGE===\n'.join(pages_alg)

def parse_algebra():
    data = {}
    # Find all tema start positions
    tema_starts = list(re.finditer(
        r'(?m)^UBAXXI.*?Tema\s+(\d+)\s*$',
        full_alg
    ))
    for idx, m in enumerate(tema_starts):
        orig_tema = int(m.group(1))
        # Renumber sequentially 1-12 (first 6 = 1-6, second 6 = 7-12)
        new_tema = idx + 1
        start = m.start()
        end = tema_starts[idx+1].start() if idx+1 < len(tema_starts) else len(full_alg)
        content = full_alg[start:end]
        exercises = parse_algebra_tema(content)
        if exercises:
            data[str(new_tema)] = {'tema': new_tema, 'exercises': exercises}
    return data

def parse_algebra_tema(content):
    exercises = []
    parts = re.split(r'(?m)^-\s*Ejercicio\s+(\d+)\s*\([0-9.,]+\s*puntos?\)', content)
    i = 1
    while i + 1 < len(parts):
        ex_num = int(parts[i])
        block = parts[i+1]
        resol = re.search(r'Resoluci[oó´]+n', block)
        if resol:
            block = block[:resol.start()]
        corr_m = re.search(r'Opci[oó´]+n\s+correcta:\s*([ABCD])\)', block, re.IGNORECASE)
        if not corr_m:
            i += 2; continue
        correct = corr_m.group(1)
        block = block[:corr_m.start()]
        opts = extract_algebra_options(block)
        q_text = extract_algebra_question(block)
        exercises.append({
            'num': ex_num,
            'question': clean(q_text),
            'options': opts,
            'correct': correct
        })
        i += 2
    return exercises

def extract_algebra_options(block):
    opts = {'A': '', 'B': '', 'C': '', 'D': ''}
    lines = block.split('\n')
    for line in lines:
        line = line.strip()
        m = re.match(r'^A\)\s*(.*?)\s{2,}C\)\s*(.*)', line)
        if m:
            opts['A'] = m.group(1).strip()
            opts['C'] = m.group(2).strip()
            continue
        m = re.match(r'^B\)\s*(.*?)\s{2,}D\)\s*(.*)', line)
        if m:
            opts['B'] = m.group(1).strip()
            opts['D'] = m.group(2).strip()
            continue
        m4 = re.match(r'^A\)\s*(.*?)\s+B\)\s*(.*?)\s+C\)\s*(.*?)\s+D\)\s*(.*)', line)
        if m4:
            opts['A'] = m4.group(1).strip()
            opts['B'] = m4.group(2).strip()
            opts['C'] = m4.group(3).strip()
            opts['D'] = m4.group(4).strip()
            continue
        ms = re.match(r'^([ABCD])\)\s+(.*)', line)
        if ms and not opts[ms.group(1)]:
            opts[ms.group(1)] = ms.group(2).strip()
    result = []
    for letter in ['A', 'B', 'C', 'D']:
        text = opts[letter] or letter
        result.append({'letter': letter, 'text': clean(text)})
    return result

def extract_algebra_question(block):
    m = re.search(r'(?m)^[ABCD]\)', block)
    if m:
        return block[:m.start()].strip()
    return block.strip()

algebra_data = parse_algebra()
print(f"Álgebra: {len(algebra_data)} temas")
for k in sorted(algebra_data.keys(), key=int):
    exs = algebra_data[k]['exercises']
    print(f"  Tema {k}: {len(exs)} ejercicios, correctas={[e['correct'] for e in exs]}")

# ============================================================
# PENSAMIENTO COMPUTACIONAL  (4 PDFs, temas 1 3 5 7)
# ============================================================
PC_FILES = {
    1: r'D:\UBA\Pensamiento Computacional\Segundo Pärcial\2do_Parcial_-_2do_C._2025_-_Tema_1-3f1bb50c20bc440f9e4fbafc4b33cfe6.pdf',
    3: r'D:\UBA\Pensamiento Computacional\Segundo Pärcial\2do_Parcial_-_2do_C._2025_-_Tema_3-2bf046285b094038a1e72b1dab4f2e70.pdf',
    5: r'D:\UBA\Pensamiento Computacional\Segundo Pärcial\2do_Parcial_-_2do_C._2025_-_Tema_5-23de496193f7439fb0a54c38acfee9d9.pdf',
    7: r'D:\UBA\Pensamiento Computacional\Segundo Pärcial\2do_Parcial_-_2do_C._2025_-_Tema_7-0b24e892d56d4961a18fa90bb128edc0.pdf',
}

def parse_pc_file(tema_num, path):
    pages = get_pages(path)
    # Join all pages (skip page 0 which is the header/matrix page)
    content = '\n'.join(pages[1:])
    # The em-dash in exercise headers may differ; handle both – and -
    parts = re.split(r'(?m)^(Ejercicio\s+\d+\s*[–\-]\s*Tema\s+\d+\s+\d+\s*Ptos?)\s*$', content)

    exercises = []
    i = 1
    while i + 1 < len(parts):
        header = parts[i]
        block = parts[i+1]
        ex_num_m = re.search(r'Ejercicio\s+(\d+)', header)
        if not ex_num_m:
            i += 2; continue
        ex_num = int(ex_num_m.group(1))
        # Clean page markers and URLs
        block = re.sub(r'https?://\S+', '', block)
        block = re.sub(r'\d{1,2}/\d{1,2}/\d{4}\s+Tema\s+\d+\s*[–\-]\s*Pag\s*\d+', '', block)
        # Find correct answer: "X X X" (standalone) or "X  X  X"
        correct = None
        # Full-line: "C X C"
        cm = re.search(r'(?m)^([ABCD])\s+X\s+\1\s*$', block)
        if cm:
            correct = cm.group(1)
        else:
            # Inline: "A X texto A" — but this is tricky; look for the X marker
            cm2 = re.search(r'(?m)^([ABCD])\s+X\s', block)
            if cm2:
                correct = cm2.group(1)
        if not correct:
            i += 2; continue
        # Build clean options
        opts, q_text = extract_pc_content(block)
        exercises.append({
            'num': ex_num,
            'question': clean(q_text),
            'options': opts,
            'correct': correct
        })
        i += 2
    return exercises

def extract_pc_content(block):
    """
    Parse PC option blocks. Options appear BEFORE their letter markers:
    [option A text]
    A [X?] A
    [option B text]
    B [X?] B  ...
    Returns (options, question_text).
    """
    lines = block.split('\n')
    # Find all letter marker positions
    marker_re = re.compile(r'^([ABCD])(\s+X)?(\s+\S.*?)?\s+\1\s*$')
    marker_positions = []  # (line_index, letter, inline_text)
    for idx, line in enumerate(lines):
        m = marker_re.match(line.strip())
        if m:
            letter = m.group(1)
            inline = (m.group(3) or '').strip()
            marker_positions.append((idx, letter, inline))

    if not marker_positions:
        return [{'letter': l, 'text': l} for l in 'ABCD'], block.strip()

    # Text before first marker = question + option A text
    # Group lines into chunks per option
    opts_text = {}
    for j, (pos, letter, inline) in enumerate(marker_positions):
        if j == 0:
            pre_lines = lines[:pos]
        else:
            prev_pos = marker_positions[j-1][0]
            pre_lines = lines[prev_pos+1:pos]
        # Also add inline text from the marker itself
        opt_lines = [l for l in pre_lines if l.strip()]
        if inline:
            opt_lines.append(inline)
        # Lines after last marker belong to the last option
        if j == len(marker_positions) - 1:
            post_lines = [l for l in lines[pos+1:] if l.strip()]
            opt_lines.extend(post_lines)
        opts_text[letter] = ' '.join(opt_lines).strip()

    # Question text = everything before option A text starts
    # Heuristic: question ends at the last '?' in the pre-option-A block
    pre_a_lines = lines[:marker_positions[0][0]]
    opt_a_raw = opts_text.get('A', '')
    # Try to remove opt A text from the end of pre_a_lines
    q_lines = pre_a_lines
    if opt_a_raw and opt_a_raw != 'A':
        # Remove opt A content from pre lines
        pre_text = '\n'.join(pre_a_lines)
        a_clean = opt_a_raw[:40]  # first 40 chars
        idx_a = pre_text.find(a_clean)
        if idx_a > 0:
            q_lines = pre_text[:idx_a].split('\n')

    q_text = ' '.join(l for l in q_lines if l.strip())

    opts = []
    for letter in 'ABCD':
        text = opts_text.get(letter, letter)
        opts.append({'letter': letter, 'text': clean(text) or letter})
    return opts, q_text

pc_data = {}
for tema_num, path in PC_FILES.items():
    exs = parse_pc_file(tema_num, path)
    pc_data[str(tema_num)] = {'tema': tema_num, 'exercises': exs}
    print(f"PC Tema {tema_num}: {len(exs)} ejercicios")

# ============================================================
# ANÁLISIS MATEMÁTICO  (4 temas, ejercicios MC: vary per exam)
# ============================================================
pages_am = get_pages(r'D:\UBA\Análisis Matemático\Segundo Parcial\A.M Segundo Parcial 4 Temas.pdf')

def parse_analisis():
    data = {}
    # Find tema-block start pages: pages with "Segundo Parcial ... Tema N" header
    blocks = []
    for i, pg in enumerate(pages_am):
        m = re.search(r'Segundo Parcial[^\n]*?Tema\s+(\d+)', pg)
        if m:
            blocks.append((i, int(m.group(1))))

    for j, (start, _) in enumerate(blocks):
        end = blocks[j+1][0] if j+1 < len(blocks) else len(pages_am)
        chunk = '\n'.join(pages_am[start:end])
        qs = parse_analisis_mc(chunk)
        if qs:
            new_key = str(j + 1)
            data[new_key] = {'tema': j + 1, 'questions': qs}
    return data

def parse_analisis_mc(content):
    """Extract MC exercises (those containing ■ correct marker)."""
    questions = []
    ex_blocks = re.split(r'(?m)^(\d+)\.\s*\(\s*\d+\s*puntos?\s*\)', content)
    i = 1
    while i + 1 < len(ex_blocks):
        ex_num = int(ex_blocks[i])
        block = ex_blocks[i+1]
        if '■' not in block:
            i += 2; continue
        first_opt = re.search(r'■|\(cid:50\)', block)
        if not first_opt:
            i += 2; continue
        q_raw = block[:first_opt.start()]
        q_raw = re.sub(r'Resoluci[oó´]+n.*', '', q_raw, flags=re.DOTALL)
        q_text = clean(q_raw)
        opts, correct = extract_analisis_opts(block)
        if opts and correct:
            questions.append({
                'num': ex_num,
                'question': q_text,
                'options': opts,
                'correct': correct
            })
        i += 2
    return questions

def extract_analisis_opts(block):
    """
    Parse MC options with ■ (correct) and (cid:50) (wrong) markers.
    Two formats observed:
    - June exercise 2: ■ appears first (before correct option text),
      subsequent (cid:50) appear after wrong option text.
    - All others (November, June ex6): (cid:50) appears first (before
      each wrong option text), ■ appears inline before correct text.
    """
    block = re.sub(r'Resoluci[oó´]+n.*', '', block, flags=re.DOTALL)
    parts = re.split(r'(■|\(cid:50\))', block)

    markers = []
    for idx in range(1, len(parts), 2):
        if idx < len(parts) and parts[idx] in ('■', '(cid:50)'):
            markers.append((idx, parts[idx]))

    if len(markers) < 2:
        return [], None

    correct = None
    for j, (_, m) in enumerate(markers[:4]):
        if m == '■':
            correct = 'ABCD'[j]
            break
    if not correct:
        return [], None

    first_marker = markers[0][1]
    opts = []

    for j in range(min(4, len(markers))):
        marker_idx, marker = markers[j]
        letter = 'ABCD'[j]

        if first_marker == '(cid:50)':
            # All markers precede their option text — take text after each marker
            seg_after_idx = marker_idx + 1
            raw = parts[seg_after_idx].strip() if seg_after_idx < len(parts) else ''
            lines = [l.strip() for l in raw.split('\n')
                     if l.strip() and not l.strip().startswith('http')]
            text = ' '.join(lines[:2]) if lines else letter
        else:
            # ■ is first: ■ precedes correct text; (cid:50) follows wrong text
            if marker == '■':
                seg_after_idx = marker_idx + 1
                raw = parts[seg_after_idx].strip() if seg_after_idx < len(parts) else ''
                lines = [l.strip() for l in raw.split('\n')
                         if l.strip() and not l.strip().startswith('http')]
                text = lines[0] if lines else letter
            elif j == 1:
                # Option B: its text is the last line in the segment after ■ (parts[2])
                raw = parts[2].strip() if len(parts) > 2 else ''
                lines = [l.strip() for l in raw.split('\n')
                         if l.strip() and not l.strip().startswith('http')]
                text = lines[-1] if len(lines) > 1 else (lines[0] if lines else letter)
            else:
                # Options C, D: text is immediately before this (cid:50)
                seg_before_idx = marker_idx - 1
                raw = parts[seg_before_idx].strip() if 0 <= seg_before_idx < len(parts) else ''
                lines = [l.strip() for l in raw.split('\n')
                         if l.strip() and not l.strip().startswith('http')]
                text = lines[-1] if lines else letter

        opts.append({'letter': letter, 'text': clean(text) or letter})

    return opts, correct

analisis_data = parse_analisis()
print(f"\nAnálisis: {len(analisis_data)} temas")
for k in sorted(analisis_data.keys(), key=int):
    qs = analisis_data[k]['questions']
    print(f"  Tema {k}: {len(qs)} preguntas MC, correctas={[q['correct'] for q in qs]}")

# ============================================================
# SAVE JSON
# ============================================================
with open('algebra_data.json', 'w', encoding='utf-8') as f:
    json.dump(algebra_data, f, ensure_ascii=False, indent=2)
with open('pc_data.json', 'w', encoding='utf-8') as f:
    json.dump(pc_data, f, ensure_ascii=False, indent=2)
with open('analisis_data.json', 'w', encoding='utf-8') as f:
    json.dump(analisis_data, f, ensure_ascii=False, indent=2)
print("\nSaved: algebra_data.json, pc_data.json, analisis_data.json")
