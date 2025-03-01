import math
from datetime import datetime
from typing import List, Dict, Tuple

from thread_story import tell_thread_story

def parse_utc(dt_str: str) -> datetime:
    """
    Parse an ISO8601 datetime string, e.g. '2014-12-23T19:11:08Z',
    into a Python datetime (UTC).
    """
    # Replace trailing 'Z' with '+00:00' so that fromisoformat works properly.
    return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))

def get_color_for_status(status: str) -> str:
    """
    Return an SVG color for the given message status.
    """
    if status == "PATCH_SET":
        return "blue"
    elif status == "REQUEST_CHANGES":
        return "red"
    elif status == "APPROVAL":
        return "green"
    return "black"

def avoid_overlap(x_positions, min_sep=10):
    """
    Given a list of x_positions (sorted ascending), adjust them so that
    no two points overlap (maintain at least min_sep between consecutive points).
    The algorithm here does a simple left-to-right “push” if it finds
    any overlap with its neighbor.
    """
    for i in range(1, len(x_positions)):
        if x_positions[i] - x_positions[i-1] < min_sep:
            # Push the point to the right just enough
            x_positions[i] = x_positions[i-1] + min_sep

def create_thread_svg(messages: List[Dict], width=1000, height=200) -> str:
    """
    Create an SVG string that shows each message as a dot on a timeline,
    with arrows drawn for references.
    """
    # Sort messages by sent time
    messages_sorted = sorted(messages, key=lambda m: parse_utc(m["header"]["sent_utc"]))

    # Identify earliest and latest times
    times = [parse_utc(m["header"]["sent_utc"]) for m in messages_sorted]
    t_min = min(times)
    t_max = max(times)

    # If everything is at the same time (degenerate case),
    # artificially expand range by 1 second
    if t_min == t_max:
        t_max = t_max.replace(second=t_max.second + 1)

    # Convert times to numeric range [0, 1], then map to [0, width - 100]
    # We'll leave a margin so arrows are less likely to clip the edge.
    def time_to_x(t: datetime) -> float:
        frac = (t - t_min).total_seconds() / (t_max - t_min).total_seconds()
        return 50 + frac * (width - 100)

    # Pre-calculate each message's x position
    x_positions = [time_to_x(parse_utc(m["header"]["sent_utc"])) for m in messages_sorted]
    # Force non-overlapping
    avoid_overlap(x_positions, min_sep=12)

    # Choose a single y coordinate for all dots
    y_coord = height // 2

    # Identify the author of the first message (chronologically)
    author_first = messages_sorted[0]["header"]["author"]

    # Build a map from message key -> (index_in_sorted_list, x_position)
    key_to_index = {}
    for i, msg in enumerate(messages_sorted):
        key_to_index[msg["key"][1]] = (i, x_positions[i])

    # Start building the SVG output
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        'style="background-color: white; font-family: sans-serif;">'
    ]

    # Draw a horizontal axis for reference
    svg_parts.append(
        f'<line x1="50" y1="{y_coord}" x2="{width-50}" y2="{y_coord}" '
        'stroke="gray" stroke-width="1"/>'
    )

    # -- Draw reference arrows first, so circles appear on top --
    for i, msg in enumerate(messages_sorted):
        # If references is None or empty, skip
        if not msg.get("references"):
            continue
        src_x = x_positions[i]
        for refs in msg["references"]:
            ref_key = refs[1]
            if ref_key in key_to_index:
                ref_idx, ref_x = key_to_index[ref_key]
                # We'll draw a simple arrow from the referencing message to the referenced one.
                # y is constant = y_coord for both, so we can just do a small curve or offset:
                mid_y = y_coord - 20 if src_x > ref_x else y_coord + 20
                path_d = (f"M {src_x} {y_coord} "
                          f"Q {(src_x + ref_x)/2} {mid_y}, {ref_x} {y_coord}")
                svg_parts.append(
                    f'<path d="{path_d}" stroke="black" fill="none" marker-end="url(#arrowhead)"/>'
                )

    # Define an arrowhead marker in the <defs> block if we haven’t already:
    svg_parts.append('''
<defs>
  <marker id="arrowhead" markerWidth="5" markerHeight="5" 
          refX="2" refY="2" orient="auto" fill="black">
    <path d="M0,0 L0,4 L4,2 z" />
  </marker>
</defs>
''')

    # -- Draw circles for each message --
    for i, msg in enumerate(messages_sorted):
        x = x_positions[i]
        color = get_color_for_status(msg["body"].get("status", ""))
        # if same author as first message
        if msg["header"]["author"] == author_first:
            # Outer ring: draw a slightly bigger circle
            svg_parts.append(
                f'<circle cx="{x}" cy="{y_coord}" r="6" fill="none" stroke="{color}" stroke-width="2" />'
            )
            # Dot on top
            svg_parts.append(
                f'<circle cx="{x}" cy="{y_coord}" r="3" fill="{color}" />'
            )
        else:
            svg_parts.append(
                f'<circle cx="{x}" cy="{y_coord}" r="4" fill="{color}" />'
            )

    # Optionally, label the earliest and latest times
    svg_parts.append(
        f'<text x="50" y="{y_coord + 25}" fill="gray" style="font-size:12px;">'
        f'{t_min.isoformat()}</text>'
    )
    svg_parts.append(
        f'<text x="{width - 100}" y="{y_coord + 25}" fill="gray" style="font-size:12px;">'
        f'{t_max.isoformat()}</text>'
    )

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def draw_thread(args):
    thread, outfile = args
    print(thread, outfile)
    messages = tell_thread_story(thread)

    print("got story for ", thread)

    svg_output = create_thread_svg(messages)

    print("got svg ", thread)

    with open(outfile, "w") as f:
        f.write(svg_output)

    print(f"SVG visualization has been written to {outfile}")


# ---------------------------
# Example usage
if __name__ == "__main__":
    # messages = tell_thread_story('20130926225545.GB26663@awork2.anarazel.de')
    messages = tell_thread_story('TYAPR01MB586654E2D74B838021BE77CAF5EEA@TYAPR01MB5866.jpnprd01.prod.outlook.com')

    for m in messages:
        print(m)

    svg_output = create_thread_svg(messages)
    # Write to a file or print
    with open("thread_viz.svg", "w") as f:
        f.write(svg_output)
    print("SVG visualization has been written to thread_viz.svg")
