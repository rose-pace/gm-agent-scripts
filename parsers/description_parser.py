from typing import List
import re

class DescriptionParser:

    @staticmethod
    def split_into_sentences(text: str) -> List[str]:
        """Split text into sentences handling common abbreviations"""
        # Don't split on common D&D abbreviations like 'ft.' or 'vs.'
        text = text.replace('ft.', 'ft_').replace('vs.', 'vs_')
        
        # Split on periods followed by spaces and capital letters
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        
        # Restore abbreviations
        sentences = [s.replace('ft_', 'ft.').replace('vs_', 'vs.') for s in sentences]
        return sentences

    @classmethod
    def classify_text(cls, text: str) -> dict:
        """
        Classify sentences into description categories using keyword/context matching
        """
        result = {
            'appearance': [],
            'personality': [],
            'background': [],
            'tactics': []
        }
        
        # Expanded markers with weights
        markers = {
            'appearance': {
                'strong': ['appears', 'looks like', 'wearing', 'clad in', 'appearance'],
                'moderate': ['tall', 'short', 'massive', 'towering', 'imposing', 'wielding'],
                'weak': ['scales', 'skin', 'eyes', 'armor', 'clothes', 'garments']
            },
            'personality': {
                'strong': ['personality', 'demeanor', 'attitude', 'nature'],
                'moderate': ['believes', 'desires', 'proud', 'fears', 'loves', 'hates'],
                'weak': ['mind', 'thoughts', 'feels', 'prefers']
            },
            'background': {
                'strong': ['history', 'background', 'origin', 'originally', 'born'],
                'moderate': ['became', 'turned into', 'transformed', 'created'],
                'weak': ['was', 'were', 'used to', 'once']
            },
            'tactics': {
                'strong': ['tactics', 'strategy', 'combat style', 'fighting'],
                'moderate': ['attacks', 'defends', 'prefers to', 'in battle'],
                'weak': ['using', 'wields', 'power', 'ability']
            }
        }

        sentences = cls.split_into_sentences(text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            scores = {'appearance': 0, 'personality': 0, 'background': 0, 'tactics': 0}
            
            # Calculate score for each category
            for category, marker_groups in markers.items():
                for marker in marker_groups['strong']:
                    if marker.lower() in sentence.lower():
                        scores[category] += 3
                for marker in marker_groups['moderate']:
                    if marker.lower() in sentence.lower():
                        scores[category] += 2
                for marker in marker_groups['weak']:
                    if marker.lower() in sentence.lower():
                        scores[category] += 1
            
            # Assign sentence to highest scoring category if score > 0
            max_score = max(scores.values())
            if max_score > 0:
                # In case of tie, assign to all categories with max score
                for category, score in scores.items():
                    if score == max_score:
                        result[category].append(sentence)
        
        # Join sentences for each category
        description = {k: ' '.join(v) if v else None for k, v in result.items()}
        description['unparsed_text'] = text
        return description
