from dataclasses import dataclass
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from src.features.text_cleaning import clean_text


_analyzer = SentimentIntensityAnalyzer()


@dataclass(frozen=True)
class SentimentScore:
    compound: float
    pos: float
    neu: float
    neg: float


def score_title(title: str) -> SentimentScore:
    """
    VADER returns:
      - compound in [-1, 1]
      - pos/neu/neg in [0, 1] summing ~ 1
    """
    t = clean_text(title)
    if not t:
        return SentimentScore(compound=0.0, pos=0.0, neu=1.0, neg=0.0)

    s = _analyzer.polarity_scores(t)
    return SentimentScore(
        compound=float(s["compound"]),
        pos=float(s["pos"]),
        neu=float(s["neu"]),
        neg=float(s["neg"]),
    )
