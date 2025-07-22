def compute_safety_score(risk_dict):
    """
    Compute an overall safety score from a risk dictionary.
    Expects a dict with risk categories and scores between 0.0 and 1.0.
    Returns the maximum risk score as the overall score.
    """
    if not risk_dict:
        return 0.0
    return max(float(score) for score in risk_dict.values() if isinstance(score, (int, float, str)) and str(score).replace('.', '', 1).isdigit())
