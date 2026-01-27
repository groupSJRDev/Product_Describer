from typing import Dict, Any

def extract_critical_specs(specs: Dict[str, Any]) -> Dict[str, str]:
    """Extract key specifications for prompt emphasis.

    Args:
        specs: Product specifications dictionary

    Returns:
        Dictionary with 'critical' specifications formatted for prompt
    """
    critical_items = []

    # Extract dimensions if available
    if "dimensions" in specs and "primary" in specs["dimensions"]:
        dims = specs["dimensions"]["primary"]
        if "width" in dims and dims["width"].get("value"):
            critical_items.append(
                f"- Width: {dims['width']['value']}{dims['width'].get('unit', 'mm')}"
            )
        if "height" in dims and dims["height"].get("value"):
            critical_items.append(
                f"- Height: {dims['height']['value']}{dims['height'].get('unit', 'mm')}"
            )
        if "depth" in dims and dims["depth"].get("value"):
            critical_items.append(
                f"- Depth: {dims['depth']['value']}{dims['depth'].get('unit', 'mm')}"
            )

    # Extract primary colors
    if "visual_characteristics" in specs and "primary_colors" in specs["visual_characteristics"]:
        colors = specs["visual_characteristics"]["primary_colors"]
        if colors:
            color_strs = []
            for c in colors:
                if isinstance(c, dict) and "hex" in c:
                    color_strs.append(f"{c.get('name', 'Color')} ({c['hex']})")
                elif isinstance(c, str):
                    color_strs.append(c)
            if color_strs:
                critical_items.append(f"- Colors: {', '.join(color_strs)}")

    # Extract material finish
    if "materials" in specs and "primary_material" in specs["materials"]:
        mat = specs["materials"]["primary_material"]
        if "finish" in mat:
            critical_items.append(f"- Finish: {mat['finish']}")
        if "transparency" in mat:
            critical_items.append(f"- Transparency: {mat['transparency']}")

    # Extract logo detail
    if "branding" in specs and "logo" in specs["branding"]:
        logo = specs["branding"]["logo"]
        if "placement" in logo:
            critical_items.append(f"- Logo placement: {logo['placement']}")

    # Extract label info if present
    if "packaging" in specs and "label" in specs["packaging"]:
        label = specs["packaging"]["label"]
        if label:
             if isinstance(label, dict) and "position" in label:
                critical_items.append(f"- Label position: {label['position']}")

    return {
        "critical": "\n".join(critical_items)
        if critical_items
        else "- See full specifications below"
    }
