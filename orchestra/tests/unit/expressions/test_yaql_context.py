# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from orchestra.tests.unit import base


class YAQLVariableExtractionTest(base.ExpressionEvaluatorTest):

    @classmethod
    def setUpClass(cls):
        cls.language = 'yaql'
        super(YAQLVariableExtractionTest, cls).setUpClass()

    def test_empty_extraction(self):
        expr = '<% just_text and $not_a_var %>'

        self.assertListEqual([], self.evaluator.extract_vars(expr))

    def test_single_var_extraction(self):
        expr = '<% $.foobar  %>'

        expected_vars = [
            '$.foobar'
        ]

        self.assertListEqual(expected_vars, self.evaluator.extract_vars(expr))

    def test_single_dotted_var_extraction(self):
        expr = '<% $.foo.bar  %>'

        expected_vars = [
            '$.foo.bar'
        ]

        self.assertListEqual(expected_vars, self.evaluator.extract_vars(expr))

    def test_single_indexing_var_extraction(self):
        expr = '<% $.foo[0]  %>'

        expected_vars = [
            '$.foo[0]'
        ]

        self.assertListEqual(expected_vars, self.evaluator.extract_vars(expr))

    def test_single_functional_var_extraction(self):
        expr = '<% $.foo.get(bar)  %>'

        expected_vars = [
            '$.foo.get(bar)'
        ]

        self.assertListEqual(expected_vars, self.evaluator.extract_vars(expr))

    def test_multiple_vars_extraction(self):
        expr = '<% $.foobar $.foo.get(bar) $.fu.bar $.fu.bar[0]  %>'

        expected_vars = [
            '$.foobar',
            '$.foo.get(bar)',
            '$.fu.bar',
            '$.fu.bar[0]'
        ]

        self.assertListEqual(
            sorted(expected_vars),
            sorted(self.evaluator.extract_vars(expr))
        )

    def test_multiple_interleaved_vars_extraction(self):
        expr = '<% Why the $.foobar are you so $.fu.bar serious? %>'

        expected_vars = [
            '$.foobar',
            '$.fu.bar'
        ]

        self.assertListEqual(
            expected_vars,
            sorted(self.evaluator.extract_vars(expr))
        )
