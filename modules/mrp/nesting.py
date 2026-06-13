from typing import List, Dict

def optimize_1d_cuts(pieces_mm: List[float], stock_length_mm: float = 6000.0, blade_kerf_mm: float = 5.0) -> Dict:
    # Filter out pieces <= 0
    pieces_mm = [p for p in pieces_mm if p > 0]
    
    # Sort pieces_mm in descending order (largest first)
    pieces_mm.sort(reverse=True)
    
    bins = []
    
    for piece in pieces_mm:
        placed = False
        for b in bins:
            if b["remaining_space"] >= piece:
                b["remaining_space"] -= (piece + blade_kerf_mm)
                b["cuts"].append(piece)
                placed = True
                break
        if not placed:
            bins.append({
                "remaining_space": stock_length_mm - (piece + blade_kerf_mm),
                "cuts": [piece]
            })
            
    total_bars = len(bins)
    total_cut_length = sum(pieces_mm)
    total_waste_mm = (total_bars * stock_length_mm) - total_cut_length
    waste_percentage = (total_waste_mm / (total_bars * stock_length_mm) * 100) if total_bars > 0 else 0.0
    
    return {
        "total_bars": total_bars,
        "total_cut_length_m": total_cut_length / 1000.0,
        "total_waste_m": total_waste_mm / 1000.0,
        "waste_percentage": waste_percentage,
        "bars": bins
    }
