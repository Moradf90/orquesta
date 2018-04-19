# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from orchestra.tests.unit.specs.mistral import base


class WorkflowSpecVarsValidationTest(base.MistralWorkflowSpecTest):

    def test_bad_vars_yaql(self):
        wf_def = """
            version: '2.0'

            sequential:
                description: A basic sequential workflow.
                input:
                    - y
                vars:
                    foo: <% $.a %>
                    fooa: <% $.x + $.y + $.z %>
                tasks:
                    task1:
                        action: std.noop
        """

        wf_spec = self.instantiate(wf_def)

        expected_errors = {
            'context': [
                {
                    'type': 'yaql',
                    'expression': '<% $.a %>',
                    'message': 'Variable "a" is referenced before assignment.',
                    'schema_path': 'properties.vars',
                    'spec_path': 'sequential.vars'
                },
                {
                    'type': 'yaql',
                    'expression': '<% $.x + $.y + $.z %>',
                    'message': 'Variable "x" is referenced before assignment.',
                    'schema_path': 'properties.vars',
                    'spec_path': 'sequential.vars'
                },
                {
                    'type': 'yaql',
                    'expression': '<% $.x + $.y + $.z %>',
                    'message': 'Variable "z" is referenced before assignment.',
                    'schema_path': 'properties.vars',
                    'spec_path': 'sequential.vars'
                }
            ]
        }

        self.assertDictEqual(wf_spec.inspect(), expected_errors)

    def test_bad_vars_jinja(self):
        wf_def = """
            version: '2.0'

            sequential:
                description: A basic sequential workflow.
                input:
                    - y
                vars:
                    foo: "{{ _.a }}"
                    fooa: "{{ _.x + _.y + _.z }}"
                tasks:
                    task1:
                        action: std.noop
        """

        wf_spec = self.instantiate(wf_def)

        expected_errors = {
            'context': [
                {
                    'type': 'jinja',
                    'expression': '{{ _.a }}',
                    'message': 'Variable "a" is referenced before assignment.',
                    'schema_path': 'properties.vars',
                    'spec_path': 'sequential.vars'
                },
                {
                    'type': 'jinja',
                    'expression': '{{ _.x + _.y + _.z }}',
                    'message': 'Variable "x" is referenced before assignment.',
                    'schema_path': 'properties.vars',
                    'spec_path': 'sequential.vars'
                },
                {
                    'type': 'jinja',
                    'expression': '{{ _.x + _.y + _.z }}',
                    'message': 'Variable "z" is referenced before assignment.',
                    'schema_path': 'properties.vars',
                    'spec_path': 'sequential.vars'
                }
            ]
        }

        self.assertDictEqual(wf_spec.inspect(), expected_errors)

    def test_bad_vars_mix_yaql_and_jinja(self):
        wf_def = """
            version: '2.0'

            sequential:
                description: A basic sequential workflow.
                input:
                    - y
                vars:
                    foo: "{{ _.a }}"
                    fooa: <% $.x + $.y + $.z %>
                tasks:
                    task1:
                        action: std.noop
        """

        wf_spec = self.instantiate(wf_def)

        expected_errors = {
            'context': [
                {
                    'type': 'jinja',
                    'expression': '{{ _.a }}',
                    'message': 'Variable "a" is referenced before assignment.',
                    'schema_path': 'properties.vars',
                    'spec_path': 'sequential.vars'
                },
                {
                    'type': 'yaql',
                    'expression': '<% $.x + $.y + $.z %>',
                    'message': 'Variable "x" is referenced before assignment.',
                    'schema_path': 'properties.vars',
                    'spec_path': 'sequential.vars'
                },
                {
                    'type': 'yaql',
                    'expression': '<% $.x + $.y + $.z %>',
                    'message': 'Variable "z" is referenced before assignment.',
                    'schema_path': 'properties.vars',
                    'spec_path': 'sequential.vars'
                }
            ]
        }

        self.assertDictEqual(wf_spec.inspect(), expected_errors)

    def test_bad_vars_in_sequential_tasks(self):
        wf_def = """
            version: '2.0'

            sequential:
                description: A basic sequential workflow.
                vars:
                    foobar: foobar
                tasks:
                    task1:
                        action: std.echo
                        input:
                            message: <% $.foobar %>
                        on-success:
                            - task2
                    task2:
                        action: std.echo
                        input:
                            message: <% $.foo %>
        """

        wf_spec = self.instantiate(wf_def)

        expected_errors = {
            'context': [
                {
                    'type': 'yaql',
                    'expression': '<% $.foo %>',
                    'message': 'Variable "foo" is referenced before assignment.',
                    'schema_path': 'properties.tasks.properties.task2.properties.input',
                    'spec_path': 'sequential.tasks.task2.input'
                }
            ]
        }

        self.assertDictEqual(wf_spec.inspect(), expected_errors)

    def test_bad_vars_in_branching_tasks(self):
        wf_def = """
            version: '2.0'

            sequential:
                description: A basic sequential workflow.
                vars:
                    foobar: foobar
                tasks:
                    task1:
                        action: std.echo
                        input:
                            message: <% $.foobar %>
                        publish:
                            foo: bar
                        on-success:
                            - task2
                    task2:
                        action: std.echo
                        input:
                            message: <% $.foo + $.bar %>

                    task3:
                        action: std.echo
                        input:
                            message: <% $.foobar %>
                        publish:
                            bar: foo
                        on-success:
                            - task4
                    task4:
                        action: std.echo
                        input:
                            message: <% $.foo + $.bar %>
        """

        wf_spec = self.instantiate(wf_def)

        expected_errors = {
            'context': [
                {
                    'type': 'yaql',
                    'expression': '<% $.foo + $.bar %>',
                    'message': 'Variable "bar" is referenced before assignment.',
                    'schema_path': 'properties.tasks.properties.task2.properties.input',
                    'spec_path': 'sequential.tasks.task2.input'
                },
                {
                    'type': 'yaql',
                    'expression': '<% $.foo + $.bar %>',
                    'message': 'Variable "foo" is referenced before assignment.',
                    'schema_path': 'properties.tasks.properties.task4.properties.input',
                    'spec_path': 'sequential.tasks.task4.input'
                }
            ]
        }

        self.assertDictEqual(wf_spec.inspect(), expected_errors)

    def test_bad_vars_in_reusable_split_tasks(self):
        wf_def = """
            version: '2.0'

            sequential:
                description: A basic sequential workflow.
                vars:
                    foobar: foobar
                tasks:
                    task1:
                        action: std.echo
                        input:
                            message: <% $.foobar %>
                        publish:
                            foo: bar
                        on-success:
                            - task2
                    task2:
                        action: std.echo
                        input:
                            message: <% $.foo + $.bar %>
                        on-success:
                            - task5

                    task3:
                        action: std.echo
                        input:
                            message: <% $.foobar %>
                        publish:
                            bar: foo
                        on-success:
                            - task4
                    task4:
                        action: std.echo
                        input:
                            message: <% $.foo + $.bar %>
                        on-success:
                            - task5

                    task5:
                        action: std.echo
                        input:
                            message: <% $.foo %>
        """

        wf_spec = self.instantiate(wf_def)

        expected_errors = {
            'context': [
                {
                    'type': 'yaql',
                    'expression': '<% $.foo + $.bar %>',
                    'message': 'Variable "bar" is referenced before assignment.',
                    'schema_path': 'properties.tasks.properties.task2.properties.input',
                    'spec_path': 'sequential.tasks.task2.input'
                },
                {
                    'type': 'yaql',
                    'expression': '<% $.foo + $.bar %>',
                    'message': 'Variable "foo" is referenced before assignment.',
                    'schema_path': 'properties.tasks.properties.task4.properties.input',
                    'spec_path': 'sequential.tasks.task4.input'
                },
                {
                    'type': 'yaql',
                    'expression': '<% $.foo %>',
                    'message': 'Variable "foo" is referenced before assignment.',
                    'schema_path': 'properties.tasks.properties.task5.properties.input',
                    'spec_path': 'sequential.tasks.task5.input'
                }
            ]
        }

        self.assertDictEqual(wf_spec.inspect(), expected_errors)

    def test_vars_in_join_task(self):
        wf_def = """
            version: '2.0'

            sequential:
                description: A complex branching workflow.
                vars:
                    foobar: foobar
                tasks:
                    task1:
                        action: std.echo
                        input:
                            message: <% $.foobar %>
                        publish:
                            foo: bar
                        on-success:
                            - task2
                    task2:
                        action: std.echo
                        input:
                            message: <% $.foo %>
                        on-success:
                            - task5

                    task3:
                        action: std.echo
                        input:
                            message: <% $.foobar %>
                        publish:
                            bar: foo
                        on-success:
                            - task4
                    task4:
                        action: std.echo
                        input:
                            message: <% $.bar %>
                        on-success:
                            - task5

                    task5:
                        join: all
                        action: std.echo
                        input:
                            message: <% $.foo + $.bar %>
        """

        wf_spec = self.instantiate(wf_def)

        self.assertDictEqual(wf_spec.inspect(), dict())