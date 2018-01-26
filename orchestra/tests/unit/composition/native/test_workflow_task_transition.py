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

from orchestra.tests.unit.composition.native import base


class TaskTransitionWorkflowComposerTest(base.OrchestraWorkflowComposerTest):

    def test_error_handling(self):
        wf_name = 'error-handling'

        expected_wf_graph = {
            'directed': True,
            'graph': {},
            'nodes': [
                {
                    'id': 'task1'
                },
                {
                    'id': 'task2'
                },
                {
                    'id': 'task3'
                }
            ],
            'adjacency': [
                [
                    {
                        'id': 'task2',
                        'key': 0,
                        'criteria': ['<% succeeded() %>']
                    },
                    {
                        'id': 'task3',
                        'key': 0,
                        'criteria': ['<% failed() %>']
                    }
                ],
                [],
                []
            ],
            'multigraph': True
        }

        self.assert_compose_to_wf_graph(wf_name, expected_wf_graph)

        expected_wf_ex_graph = {
            'directed': True,
            'graph': {},
            'nodes': [
                {
                    'id': 'task1',
                    'name': 'task1'
                },
                {
                    'id': 'task2',
                    'name': 'task2'
                },
                {
                    'id': 'task3',
                    'name': 'task3'
                }
            ],
            'adjacency': [
                [
                    {
                        'id': 'task2',
                        'key': 0,
                        'criteria': ['<% succeeded() %>']
                    },
                    {
                        'id': 'task3',
                        'key': 0,
                        'criteria': ['<% failed() %>']
                    }
                ],
                [],
                []
            ],
            'multigraph': True
        }

        self.assert_compose_to_wf_ex_graph(wf_name, expected_wf_ex_graph)

    def test_on_complete(self):
        wf_name = 'task-on-complete'

        expected_wf_graph = {
            'directed': True,
            'graph': {},
            'nodes': [
                {
                    'id': 'task1'
                },
                {
                    'id': 'task2'
                },
                {
                    'id': 'task3'
                },
                {
                    'id': 'task4'
                }
            ],
            'adjacency': [
                [
                    {
                        'id': 'task2',
                        'key': 0,
                        'criteria': ['<% succeeded() %>']
                    },
                    {
                        'id': 'task3',
                        'key': 0,
                        'criteria': ['<% failed() %>']
                    },
                    {
                        'id': 'task4',
                        'key': 0,
                        'criteria': []
                    }
                ],
                [],
                [],
                []
            ],
            'multigraph': True
        }

        self.assert_compose_to_wf_graph(wf_name, expected_wf_graph)

        expected_wf_ex_graph = {
            'directed': True,
            'graph': {},
            'nodes': [
                {
                    'id': 'task1',
                    'name': 'task1'
                },
                {
                    'id': 'task2',
                    'name': 'task2'
                },
                {
                    'id': 'task3',
                    'name': 'task3'
                },
                {
                    'id': 'task4',
                    'name': 'task4'
                }
            ],
            'adjacency': [
                [
                    {
                        'id': 'task2',
                        'key': 0,
                        'criteria': ['<% succeeded() %>']
                    },
                    {
                        'id': 'task3',
                        'key': 0,
                        'criteria': ['<% failed() %>']
                    },
                    {
                        'id': 'task4',
                        'key': 0,
                        'criteria': []
                    }
                ],
                [],
                [],
                []
            ],
            'multigraph': True
        }

        self.assert_compose_to_wf_ex_graph(wf_name, expected_wf_ex_graph)

    def test_task_transitions_split(self):
        wf_name = 'task-transitions-split'

        expected_wf_graph = {
            'directed': True,
            'graph': {},
            'nodes': [
                {
                    'id': 'task1'
                },
                {
                    'id': 'task2',
                    'splits': ['task2']
                }
            ],
            'adjacency': [
                [
                    {
                        'id': 'task2',
                        'key': 0,
                        'criteria': []
                    },
                    {
                        'id': 'task2',
                        'key': 1,
                        'criteria': ['<% failed() %>']
                    },
                    {
                        'id': 'task2',
                        'key': 2,
                        'criteria': ['<% succeeded() %>']
                    }
                ],
                []
            ],
            'multigraph': True
        }

        self.assert_compose_to_wf_graph(wf_name, expected_wf_graph)

        expected_wf_ex_graph = {
            'directed': True,
            'graph': {},
            'nodes': [
                {
                    'id': 'task1',
                    'name': 'task1'
                },
                {
                    'id': 'task2__1',
                    'name': 'task2',
                    'splits': [('task2', 1)]
                },
                {
                    'id': 'task2__2',
                    'name': 'task2',
                    'splits': [('task2', 2)]
                },
                {
                    'id': 'task2__3',
                    'name': 'task2',
                    'splits': [('task2', 3)]
                }
            ],
            'adjacency': [
                [
                    {
                        'id': 'task2__1',
                        'key': 0,
                        'criteria': []
                    },
                    {
                        'id': 'task2__2',
                        'key': 0,
                        'criteria': ['<% failed() %>']
                    },
                    {
                        'id': 'task2__3',
                        'key': 0,
                        'criteria': ['<% succeeded() %>']
                    }
                ],
                [],
                [],
                []
            ],
            'multigraph': True
        }

        self.assert_compose_to_wf_ex_graph(wf_name, expected_wf_ex_graph)
