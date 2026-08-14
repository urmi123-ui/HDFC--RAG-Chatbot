import os
import glob
from bs4 import BeautifulSoup
import json

def clean_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script, style, nav, footer, etc to reduce noise
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'noscript', 'svg', 'button', 'form']):
        tag.decompose()
        
    return soup

def extract_sections(soup):
    sections = {}
    
    # Heuristic: find headers and collect text until next header
    keywords = {
        "expense_ratio": ["expense ratio", "expenses"],
        "exit_load": ["exit load"],
        "minimum_investment": ["minimum investment", "sip amount", "lumpsum", "minimum sip"],
        "benchmark": ["benchmark"],
        "fund_management": ["fund manager", "management", "managed by"],
        "overview": ["overview", "about this fund", "category"],
        "investment_objective": ["investment objective", "fund objective", "scheme objective", "objective"],
        "fund_house": ["fund house", "amc", "mutual fund house", "about hdfc mutual fund"],
        "tax": ["tax", "taxation"]
    }
    
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    
    for heading in headings:
        heading_text = heading.get_text(separator=' ', strip=True).lower()
        
        matched_section = None
        for sec, kw_list in keywords.items():
            if any(kw in heading_text for kw in kw_list):
                matched_section = sec
                break
                
        if matched_section:
            content = []
            nxt = heading.find_next_sibling()
            
            # Loop until we hit another heading
            while nxt and nxt.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                text = nxt.get_text(separator=' ', strip=True)
                if text:
                    content.append(text)
                nxt = nxt.find_next_sibling()
                
            # If we successfully parsed content for this section
            if content:
                # Append if section already exists (some pages have multiple matching headers)
                if matched_section in sections:
                    sections[matched_section] += "\n" + " ".join(content)
                else:
                    sections[matched_section] = " ".join(content)
            
    # Try finding fundDetailsContainer to extract actual values for expense ratio, NAV, etc.
    container = soup.find(class_=lambda x: x and "fundDetailsContainer" in x)
    if container:
        text_parts = [t.strip() for t in container.get_text(separator="|", strip=True).split("|") if t.strip()]
        details = {}
        for i in range(0, len(text_parts) - 1, 2):
            label = text_parts[i].lower()
            val = text_parts[i+1]
            if "nav" in label:
                details["nav"] = f"{text_parts[i]}: {val}"
            elif "min. for sip" in label:
                details["min_sip"] = f"Min. for SIP: {val}"
            elif "fund size" in label:
                details["fund_size"] = f"Fund size (AUM): {val}"
            elif "expense ratio" in label:
                details["expense_ratio_val"] = f"Expense ratio is {val}."
            elif "rating" in label:
                details["rating"] = f"Rating: {val}"
        
        # Merge key values into respective sections
        if "expense_ratio_val" in details:
            sections["expense_ratio"] = details["expense_ratio_val"] + " " + sections.get("expense_ratio", "")
        if "min_sip" in details:
            sections["minimum_investment"] = details["min_sip"] + ". " + sections.get("minimum_investment", "")
        if "fund_size" in details:
            sections["fund_house"] = sections.get("fund_house", "") + f" Fund size (AUM) is {details['fund_size']}."
        if "nav" in details:
            sections["overview"] = sections.get("overview", "") + f" {details['nav']}."
        if "rating" in details:
            sections["overview"] = sections.get("overview", "") + f" Rating: {details['rating']}."

    # Fallback if specific sections weren't found
    if not sections:
        sections['general'] = soup.get_text(separator=' ', strip=True)[:3000] # truncate to avoid massive chunks
        
    return sections

def parse_all():
    raw_dir = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
    processed_dir = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
    
    html_files = glob.glob(os.path.join(raw_dir, "*.html"))
    
    for filepath in html_files:
        filename = os.path.basename(filepath)
        slug = filename.split('_')[0]
        timestamp = filename.split('_')[1].replace('.html', '')
        
        with open(filepath, 'r', encoding='utf-8') as f:
            html = f.read()
            
        soup = clean_html(html)
        sections = extract_sections(soup)
        
        parsed_filename = f"{slug}_{timestamp}.json"
        parsed_filepath = os.path.join(processed_dir, parsed_filename)
        
        data = {
            "slug": slug,
            "source_file": filename,
            "timestamp": timestamp,
            "sections": sections
        }
        
        with open(parsed_filepath, "w", encoding="utf-8") as out:
            json.dump(data, out, indent=2, ensure_ascii=False)
            
        print(f"Parsed {slug} and saved to {parsed_filepath}")

if __name__ == "__main__":
    parse_all()
