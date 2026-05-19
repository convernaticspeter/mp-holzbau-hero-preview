#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / 'index.html').read_text(encoding='utf-8')


def step_block(step: int) -> str:
    m = re.search(
        rf'<div class="quiz-step[^"]*" data-step="{step}">(.*?)(?=\n\s*<!-- Step|\n\s*<!-- Success|\n\s*</div>\s*</div>\s*</div>)',
        HTML,
        re.S,
    )
    assert m, f'missing step {step}'
    return m.group(1)


def test_single_choice_steps_have_no_visible_continue_buttons():
    for step in [1, 2, 4, 5]:
        block = step_block(step)
        assert 'onclick="nextStep()"' not in block, f'step {step} still has a Weiter/nextStep button'
        assert f'id="btn{step}"' not in block, f'step {step} still has btn{step}'


def test_single_choice_select_option_auto_advances_without_button_dependency():
    select_fn = re.search(r'function selectOption\(el, field, value\) \{(.*?)\n\s*\}', HTML, re.S)
    assert select_fn, 'missing selectOption function'
    body = select_fn.group(1)
    assert 'nextStep()' in body, 'selectOption must auto-advance single-choice steps'
    assert "[1, 2, 4, 5].includes(currentStep)" in body, 'auto-advance must target single-choice steps'


def test_multiselect_step_is_skippable_and_keeps_continue_button():
    block = step_block(3)
    assert 'onclick="nextStep()"' in block, 'multi-select step needs the only quiz Weiter button'
    assert 'id="btn3"' in block, 'multi-select continue button should remain addressable'
    btn3 = re.search(r'<button[^>]*id="btn3"[^>]*>', block)
    assert btn3, 'missing multi-select continue button'
    assert 'disabled' not in btn3.group(0), 'multi-select continue must be enabled so it can be skipped'


def test_submission_allows_empty_multiselect_priorities():
    submit_fn = re.search(r'function submitQuiz\(\) \{(.*?)\n\s*\}', HTML, re.S)
    assert submit_fn, 'missing submitQuiz function'
    first_if = re.search(r'if \((.*?)\) return;', submit_fn.group(1), re.S)
    assert first_if, 'missing submit validation guard'
    assert '!quizData.priorities.length' not in first_if.group(1), 'empty priorities should not block submit'


if __name__ == '__main__':
    tests = [name for name in globals() if name.startswith('test_')]
    failed = 0
    for name in tests:
        try:
            globals()[name]()
            print(f'PASS {name}')
        except AssertionError as e:
            failed += 1
            print(f'FAIL {name}: {e}')
    raise SystemExit(1 if failed else 0)
