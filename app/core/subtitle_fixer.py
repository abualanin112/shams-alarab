import re
from pathlib import Path

def is_english(token: str) -> bool:
    """English token: any word containing [A-Za-z]."""
    return bool(re.search(r'[A-Za-z]', token))

def is_arabic(token: str) -> bool:
    """Arabic token: any word containing [\u0600-\u06FF]."""
    return bool(re.search(r'[\u0600-\u06FF]', token))

def is_connector(token: str) -> bool:
    """Connector is the single Arabic character 'و'."""
    return token == 'و'

def process_line_logic(text: str) -> str:
    """
    Applies the deterministic line-breaking rule:
    1. Find the first English token (Anchor).
    2. Identify the English Block (consecutive English tokens and connectors).
    3. Reorder visually: [English Block] [Arabic Before Anchor].
    4. Break line before remaining tokens and recurse.
    """
    tokens = text.split()
    if not tokens:
        return ""

    anchor_idx = -1
    for i, token in enumerate(tokens):
        if is_english(token):
            anchor_idx = i
            break
    
    if anchor_idx == -1:
        # Case A: No English tokens
        return text

    # Case B: English tokens exist
    arabic_before = tokens[:anchor_idx]
    
    # Identify English block
    block_end = anchor_idx + 1
    while block_end < len(tokens):
        token = tokens[block_end]
        if is_english(token):
            block_end += 1
        elif is_connector(token):
            # Connector is part of the block if followed by English
            if block_end + 1 < len(tokens) and is_english(tokens[block_end+1]):
                block_end += 1
            else:
                break
        else:
            break
            
    english_block = tokens[anchor_idx:block_end]
    remaining = tokens[block_end:]
    
    # Line 1: [English Block] + [Arabic tokens that appeared before (reordered visually)]
    line1 = " ".join(english_block + arabic_before)
    
    if not remaining:
        return line1
    else:
        # Process remaining tokens as a new potential line recursively
        # This ensures multiple blocks are handled correctly.
        rest = process_line_logic(" ".join(remaining))
        return line1 + "\n" + rest

def fix_srt(input_path: str, output_path: str) -> str:
    """
    Reads an SRT file, processes each text line, and writes to a new SRT file.
    Preserves indices and timestamps.
    """
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by blocks (usually separated by double newline)
    # Using regex to capture parts clearly
    blocks = re.split(r'\n\s*\n', content.strip())
    processed_blocks = []
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            processed_blocks.append(block)
            continue
            
        index = lines[0]
        timestamp = lines[1]
        text_lines = lines[2:]
        
        fixed_text_lines = []
        for line in text_lines:
            fixed_text_lines.append(process_line_logic(line))
            
        processed_blocks.append(f"{index}\n{timestamp}\n" + "\n".join(fixed_text_lines))

    output_content = "\n\n".join(processed_blocks) + "\n"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output_content)
        
    return str(output_file)
