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

import copy
import logging
import six
from six.moves import queue

from orchestra.expressions import base as expr
from orchestra.specs import types
from orchestra.specs.native.v1 import base
from orchestra.utils import dictionary as dx
from orchestra.utils import parameters as args_utils


LOG = logging.getLogger(__name__)

RESERVED_TASK_NAMES = [
    'fail',
    'noop'
]


def instantiate(definition):
    return WorkflowSpec(definition)


def deserialize(data):
    return WorkflowSpec.deserialize(data)


class TaskTransitionSpec(base.Spec):
    _schema = {
        'type': 'object',
        'properties': {
            'when': types.NONEMPTY_STRING,
            'publish': {
                'oneOf': [
                    types.NONEMPTY_STRING,
                    types.NONEMPTY_DICT
                ]
            },
            'do': {
                'oneOf': [
                    types.NONEMPTY_STRING,
                    types.UNIQUE_STRING_LIST
                ]
            }
        },
        'additionalProperties': False
    }

    _context_evaluation_sequence = [
        'when',
        'publish',
        'do'
    ]

    _context_inputs = [
        'publish'
    ]

    def __init__(self, *args, **kwargs):
        super(TaskTransitionSpec, self).__init__(*args, **kwargs)

        publish_spec = getattr(self, 'publish', None)

        if publish_spec and isinstance(publish_spec, six.string_types):
            self.publish = args_utils.parse_inline_params(publish_spec or str())

        do_spec = getattr(self, 'do', None)

        if not do_spec:
            self.do = 'noop'


class TaskTransitionSequenceSpec(base.SequenceSpec):
    _schema = {
        'type': 'array',
        'items': TaskTransitionSpec
    }


class ItemizedSpec(base.Spec):
    _schema = {
        'type': 'object',
        'properties': {
            'items': {
                'oneOf': [
                    types.NONEMPTY_STRING,
                    types.UNIQUE_STRING_LIST
                ]
            },
            'concurrency': types.YAQL_OR_POSITIVE_INTEGER
        }
    }


class TaskSpec(base.Spec):
    _schema = {
        'type': 'object',
        'properties': {
            'join': {
                'oneOf': [
                    {'enum': ['all']},
                    types.POSITIVE_INTEGER
                ]
            },
            'with': ItemizedSpec,
            'action': types.NONEMPTY_STRING,
            'input': types.NONEMPTY_DICT,
            'next': TaskTransitionSequenceSpec,
        },
        'additionalProperties': False
    }

    _context_evaluation_sequence = [
        'action',
        'input',
        'next'
    ]

    def __init__(self, *args, **kwargs):
        super(TaskSpec, self).__init__(*args, **kwargs)

        action_spec = getattr(self, 'action', str())
        input_spec = args_utils.parse_inline_params(action_spec)

        if input_spec:
            self.action = action_spec[:action_spec.index(' ')]
            self.input = input_spec

    def has_join(self):
        return hasattr(self, 'join') and self.join

    def finalize_context(self, next_task_name, criteria, in_ctx):
        new_ctx = {}

        task_transition_specs = getattr(self, 'next') or []

        for task_transition_spec in task_transition_specs:
            condition = getattr(task_transition_spec, 'when') or None
            next_task_names = getattr(task_transition_spec, 'do') or []

            if next_task_name in next_task_names:
                if (condition and len(criteria) <= 0) or (not condition and len(criteria) > 0):
                    continue

                if condition and len(criteria) > 0 and condition != criteria[0]:
                    continue

                task_publish_spec = getattr(task_transition_spec, 'publish') or {}

                new_ctx = {
                    var_name: expr.evaluate(var_expr, in_ctx)
                    for var_name, var_expr in six.iteritems(task_publish_spec)
                }

                break

        out_ctx = dx.merge_dicts(in_ctx, new_ctx, overwrite=True)

        for key in list(out_ctx.keys()):
            if key.startswith('__'):
                out_ctx.pop(key)

        return out_ctx


class TaskMappingSpec(base.MappingSpec):
    _schema = {
        'type': 'object',
        'minProperties': 1,
        'patternProperties': {
            '^\w+$': TaskSpec
        }
    }

    def has_task(self, task_name):
        if task_name in RESERVED_TASK_NAMES:
            return True

        return task_name in self

    def get_task(self, task_name):
        if task_name in RESERVED_TASK_NAMES:
            return TaskSpec({'name': task_name})

        return self[task_name]

    def get_next_tasks(self, task_name, *args, **kwargs):
        task_spec = self.get_task(task_name)

        next_tasks = []

        task_transitions = getattr(task_spec, 'next') or []

        for task_transition in task_transitions:
            condition = getattr(task_transition, 'when') or None
            next_task_names = getattr(task_transition, 'do') or []

            if isinstance(next_task_names, six.string_types):
                next_task_names = [x.strip() for x in next_task_names.split(',')]

            for next_task_name in next_task_names:
                next_tasks.append((next_task_name, condition))

        return sorted(next_tasks, key=lambda x: x[0])

    def get_prev_tasks(self, task_name, *args, **kwargs):
        prev_tasks = []

        for name, task_spec in six.iteritems(self):
            for next_task in self.get_next_tasks(name):
                if task_name == next_task[0]:
                    prev_tasks.append((name, next_task[1]))

        return sorted(prev_tasks, key=lambda x: x[0])

    def get_start_tasks(self):
        start_tasks = [
            (task_name, None)
            for task_name in self.keys()
            if not self.get_prev_tasks(task_name)
        ]

        return sorted(start_tasks, key=lambda x: x[0])

    def is_join_task(self, task_name):
        task_spec = self.get_task(task_name)

        return getattr(task_spec, 'join', None) is not None

    def is_split_task(self, task_name):
        return (
            not self.is_join_task(task_name) and
            len(self.get_prev_tasks(task_name)) > 1
        )

    def in_cycle(self, task_name):
        traversed = []
        q = queue.Queue()

        for task in self.get_next_tasks(task_name):
            q.put(task[0])

        while not q.empty():
            next_task_name = q.get()

            # If the next task matches the original task, then it's in a loop.
            if next_task_name == task_name:
                return True

            # If the next task has already been traversed but didn't match the
            # original task, then there's a loop but the original task is not
            # in the loop.
            if next_task_name in traversed:
                continue

            for task in self.get_next_tasks(next_task_name):
                q.put(task[0])

            traversed.append(next_task_name)

        return False

    def has_cycles(self):
        for task_name, task_spec in six.iteritems(self):
            if self.in_cycle(task_name):
                return True

        return False

    def inspect_semantics(self, parent=None):
        result = []

        # Identify use of reserved words in task names.
        for task_name, task_spec in six.iteritems(self):
            if task_name in RESERVED_TASK_NAMES:
                message = 'The task name "%s" is reserved with special function.' % task_name
                spec_path = parent.get('spec_path') + '.' + task_name
                schema_path = parent.get('schema_path') + '.patternProperties.^\\w+$'
                entry = {'message': message, 'spec_path': spec_path, 'schema_path': schema_path}
                result.append(entry)

        # Identify the undefined task in task transitions.
        q = queue.Queue()

        for task in self.get_start_tasks():
            q.put(task[0])

        while not q.empty():
            task_name = q.get()

            # Identify the next set of tasks and related transition specs.
            # The get_next_tasks function is not used here because it doesn't
            # provide the specific info required to identify spec/schema paths.
            task_spec = self.get_task(task_name)
            task_transition_specs = getattr(task_spec, 'next') or []
            spec_path = parent.get('spec_path') + '.' + task_name
            schema_path = parent.get('schema_path') + '.patternProperties.^\\w+$'

            for i in range(0, len(task_transition_specs)):
                task_transition_spec = task_transition_specs[i]
                next_task_names = getattr(task_transition_spec, 'do') or []

                if isinstance(next_task_names, six.string_types):
                    next_task_names = [x.strip() for x in next_task_names.split(',')]

                for next_task_name in next_task_names:
                    if self.has_task(next_task_name):
                        if next_task_name not in RESERVED_TASK_NAMES:
                            q.put(next_task_name)
                    else:
                        entry = {
                            'message': 'The task "%s" is not defined.' % next_task_name,
                            'spec_path': spec_path + '.next[' + str(i) + '].do',
                            'schema_path': schema_path + '.properties.next.items.properties.do'
                        }

                        result.append(entry)

        return result

    def inspect_context(self, parent=None):
        ctxs = {}
        errors = []
        parent_ctx = parent.get('ctx', []) if parent else []
        rolling_ctx = list(set(parent_ctx))
        q = queue.Queue()

        for task in self.get_start_tasks():
            q.put((task[0], copy.deepcopy(rolling_ctx)))

        while not q.empty():
            task_name, task_ctx = q.get()

            if not task_ctx:
                task_ctx = ctxs.get(task_name, [])

            task_spec = self.get_task(task_name)

            spec_path = parent.get('spec_path') + '.' + task_name
            schema_path = parent.get('schema_path') + '.patternProperties.^\\w+$'

            task_parent = {
                'ctx': task_ctx,
                'spec_path': spec_path,
                'schema_path': schema_path
            }

            result = task_spec.inspect_context(parent=task_parent)
            errors.extend(result[0])
            task_ctx = list(set(task_ctx + result[1]))
            rolling_ctx = list(set(rolling_ctx + task_ctx))

            # Identify the next set of tasks and related transition specs.
            transitions = []
            task_transition_specs = getattr(task_spec, 'next') or []

            for i in range(0, len(task_transition_specs)):
                task_transition_spec = task_transition_specs[i]
                next_task_names = getattr(task_transition_spec, 'do') or []

                if not next_task_names:
                    transitions.append((None, task_transition_spec, str(i)))
                    continue

                if isinstance(next_task_names, six.string_types):
                    next_task_names = [x.strip() for x in next_task_names.split(',')]

                for next_task_name in next_task_names:
                    entry = (next_task_name, task_transition_spec, str(i))
                    transitions.append(entry)

            for entry in transitions:
                next_task_name = entry[0]
                task_transition_spec = entry[1]
                seq_num = entry[2]

                parent_ctx = {
                    'ctx': task_ctx,
                    'spec_path': spec_path + '.next[' + seq_num + ']',
                    'schema_path': schema_path + '.properties.next.items'
                }

                result = task_transition_spec.inspect_context(parent_ctx)
                errors.extend(result[0])
                branch_ctx = list(set(task_ctx + result[1]))

                if not next_task_name or not self.has_task(next_task_name):
                    continue

                next_task_spec = self.get_task(next_task_name)

                if not next_task_spec.has_join():
                    q.put((next_task_name, branch_ctx))
                else:
                    next_task_ctx = ctxs.get(next_task_name, [])
                    ctxs[next_task_name] = list(set(next_task_ctx + branch_ctx))
                    q.put((next_task_name, None))

        return (errors, rolling_ctx)


class WorkflowSpec(base.Spec):
    _schema = {
        'type': 'object',
        'properties': {
            'vars': types.NONEMPTY_DICT,
            'input': types.UNIQUE_STRING_OR_ONE_KEY_DICT_LIST,
            'output': types.NONEMPTY_DICT,
            'tasks': TaskMappingSpec
        },
        'required': ['tasks'],
        'additionalProperties': False
    }

    _context_evaluation_sequence = [
        'input',
        'vars',
        'tasks',
        'output'
    ]

    _context_inputs = [
        'input',
        'vars'
    ]
