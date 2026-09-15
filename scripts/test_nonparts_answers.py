import unittest
from render_nonparts_answers import render


class AnswerRenderingTests(unittest.TestCase):
    def setUp(self):
        self.answers=[{'question':f'Question {n}?','answer':f'Answer {n}.'} for n in range(25)]

    def page(self, canonical):
        return '<html><head>'+canonical+'</head><body><main><h1>Tooling &amp; inspection</h1><p>Article.</p></main></body></html>'

    def test_canonical_attribute_order_does_not_change_output(self):
        left=self.page('<link rel="canonical" href="https://pharmaglobaleng.com/services/">')
        right=self.page('<link href="https://pharmaglobaleng.com/services/" rel="canonical"/>')
        a=render(left,self.answers);b=render(right,self.answers)
        self.assertEqual(a[a.index('<!-- pge-answer-cards:start -->'):],b[b.index('<!-- pge-answer-cards:start -->'):])
        self.assertIn('https://pharmaglobaleng.com/services/#answers',b)

    def test_rerender_replaces_answers_without_duplicating_cards_or_schema(self):
        page=self.page('<link rel="canonical" href="https://pharmaglobaleng.com/services/">')
        first=render(page,self.answers)
        self.assertEqual(first,render(first,self.answers))
        self.answers[0]['answer']='A corrected answer.'
        updated=render(first,self.answers)
        self.assertNotIn('Answer 0.',updated)
        self.assertEqual(updated.count('class="pge-answer-card"'),25)
        self.assertEqual(updated.count('id="pge-answer-schema"'),1)
        self.assertEqual(updated.count('A corrected answer.'),2)


if __name__=='__main__':unittest.main()
