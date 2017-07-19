import nltk

class Analyzer():
    """Implements sentiment analysis."""

    def __init__(self, positives, negatives):
        """Initialize Analyzer."""
        stor = ''
        self.positives = []
        self.negatives = []
        read = open(positives, "r")
        with read as lines:
            for line in lines:
                line.strip()
                if line.startswith(';') or line.startswith('\n'):
                    continue
                self.positives.append(line)
        read = open(negatives, "r")
        with read as lines:
            for line in lines:
                line.strip()
                if line.startswith(';') or line.startswith('\n'):
                    continue
                self.negatives.append(line)
        # TODO

    def analyze(self, text):
        """Analyze text for sentiment, returning its score."""
        tokenizer = nltk.tokenize.TweetTokenizer()
        tokens = tokenizer.tokenize(text)
        score = 0
        for word in tokens:
            word.lower()
            word = word + '\n'
            if word in self.positives:
                score +=1
            elif word in self.negatives:
                score -= 1
            else:
                continue
        return score
