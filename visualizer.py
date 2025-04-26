from typing import Dict, List, Any
import html

def generate_diff_html(diff_sections: List[Dict[str, Any]]) -> str:
    """
    Generate HTML to visualize differences with color coding
    """
    html_output = """
    <style>
        .diff-container {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            padding: 20px;
            background-color: #f9f9f9;
            border-radius: 5px;
            border: 1px solid #ddd;
        }
        .diff-unchanged {
            color: #333;
        }
        .diff-added {
            background-color: #e6ffed;
            color: #22863a;
            text-decoration: none;
            padding: 2px 0;
            border-radius: 3px;
        }
        .diff-deleted {
            background-color: #ffeef0;
            color: #cb2431;
            text-decoration: line-through;
            padding: 2px 0;
            border-radius: 3px;
        }
        .diff-modified {
            background-color: #fff5b1;
            color: #735c0f;
            padding: 2px 0;
            border-radius: 3px;
        }
        .tooltip {
            position: relative;
            display: inline-block;
            border-bottom: 1px dotted black;
        }
        .tooltip .tooltiptext {
            visibility: hidden;
            width: 300px;
            background-color: #555;
            color: #fff;
            text-align: center;
            border-radius: 6px;
            padding: 5px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -150px;
            opacity: 0;
            transition: opacity 0.3s;
        }
        .tooltip:hover .tooltiptext {
            visibility: visible;
            opacity: 1;
        }
    </style>
    <div class="diff-container">
    """
    
    for section in diff_sections:
        section_type = section.get("type", "unchanged")
        section_text = html.escape(section.get("text", ""))
        
        # Replace newlines with <br> tags for HTML display
        section_text = section_text.replace("\n", "<br>")
        
        if section_type == "unchanged":
            html_output += f'<span class="diff-unchanged">{section_text}</span>'
        elif section_type == "added":
            html_output += f'<span class="diff-added">{section_text}</span>'
        elif section_type == "deleted":
            html_output += f'<span class="diff-deleted">{section_text}</span>'
        elif section_type == "modified":
            original_text = html.escape(section.get("original", ""))
            original_text = original_text.replace("\n", "<br>")
            html_output += f'''
            <span class="tooltip diff-modified">
                {section_text}
                <span class="tooltiptext">Original: {original_text}</span>
            </span>
            '''
    
    html_output += "</div>"
    return html_output