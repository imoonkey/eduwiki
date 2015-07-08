from __future__ import division
__author__ = 'moonkey'

from collections import Counter
from models import *


def answer_stat(answers):
    # ans/correct/tc/qc/GE/SE/guess/tt/st/comment
    if len(answers) == 0:
        return None
    stats = {}
    for key in answers[0]:
        if key == 'topic':
            stats[key] = Counter([a[key] for a in answers if key in a])
            if len(stats[key]) != 1:
                stats[key] = answers[0][key]

        if key in ['comment', 'comment_guess']:
            stats[key] = "<br>".join([a[key] for a in answers if key in a])
        elif key in [
            'topic_confidence',
            'question_confidence',
            'topic_confidence_time_delta',
            'submit_time_delta'
        ]:
            li = [a[key] for a in answers if key in a]
            stats[key] = sum(li) / len(li)
        elif key in ['grammatical_errors', 'semantic_errors']:
            lili = [a[key] for a in answers if key in a]
            merged_li = []
            for li in lili:
                merged_li.extend(li)
            stats[key] = Counter(merged_li).most_common()
        else:
            stats[key] = Counter(
                [a[key] for a in answers if key in a]).most_common()

    return stats


def db_answer_stats():
    answered_questions = WikiQuestionAnswer.objects().distinct('question')
    stats = []
    for question in answered_questions:
        answers = WikiQuestionAnswer.objects(question=question)
        stat = answer_stat(answers)
        stats.append(stat)
    return stats

if __name__ == "__main__":
    from mongoengine import connect

    connect('eduwiki_db', host='localhost')
    stats = db_answer_stats()
    print stats