import numpy as np

def calculate_geometry(x, y):
    """Calculates distance in yards and visible angle in degrees based on a 120x80 pitch."""
    distance = np.sqrt((120 - x) ** 2 + (40 - y) ** 2)
    angle_rad = np.abs(np.arctan2(44 - y, 120 - x) - np.arctan2(36 - y, 120 - x))
    angle_deg = np.degrees(angle_rad)
    return distance, angle_deg

def calculate_xg(distance, angle, body_part="Foot"):
    """Calculates expected goals using a basic logistic regression formula with a strict floor."""
    z = -1.5 - (0.09 * distance) + (0.05 * angle)
    xg_prob = 1 / (1 + np.exp(-z))
    
    current_xg = max(0.005, xg_prob)
    
    if body_part == "Header":
        current_xg = max(0.005, current_xg * 0.6)
        
    return current_xg
