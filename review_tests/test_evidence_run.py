"""The provenance guard must detect injected faults; no physics pass claim."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from evidence_run import EvidenceRun, verify_run


def setup_run(tmp_path):
    (tmp_path / 'src').mkdir()
    source = tmp_path / 'src' / 'solver.py'
    source.write_text('MODEL = 1\n')
    data = tmp_path / 'assay.json'
    data.write_text('{"source": "synthetic_test"}\n')
    run = EvidenceRun(tmp_path, tmp_path / 'run', inputs=[data],
                      configuration={'assumptions': 'test only'}, method='test')
    (run.output / 'result.json').write_text('{"value": 1}\n')
    return run, source, data


def test_unmodified_run_verifies_but_preserves_failed_model_status(tmp_path):
    run, _, _ = setup_run(tmp_path)
    run.finish(model_status='FAILED_PHYSICAL_GATE', result_summary={})
    result = verify_run(run.output)
    assert result['status'] == 'PASS'
    assert result['model_status'] == 'FAILED_PHYSICAL_GATE'


@pytest.mark.parametrize('fault', ['source', 'data', 'deleted_input', 'output',
                                    'extra_output', 'new_source', 'registration'])
def test_fault_is_detected_after_completion(tmp_path, fault):
    run, source, data = setup_run(tmp_path)
    run.finish(model_status='DEVELOPMENT', result_summary={})
    if fault == 'source': source.write_text('MODEL = 2\n')
    elif fault == 'data': data.write_text('{"changed": true}\n')
    elif fault == 'deleted_input': data.unlink()
    elif fault == 'output': (run.output / 'result.json').write_text('{}\n')
    elif fault == 'extra_output': (run.output / 'extra.json').write_text('{}\n')
    elif fault == 'new_source': (tmp_path / 'src' / 'new.py').write_text('X = 1\n')
    else: (run.output / 'registration.json').write_text('{}\n')
    assert verify_run(run.output)['status'] == 'FAIL'


def test_inputs_changed_during_calculation_cannot_be_sealed(tmp_path):
    run, _, data = setup_run(tmp_path)
    data.write_text('{}\n')
    with pytest.raises(RuntimeError):
        run.finish(model_status='DEVELOPMENT', result_summary={})
    assert verify_run(run.output)['status'] == 'FAIL'


def test_previous_runs_are_never_overwritten(tmp_path):
    run, _, data = setup_run(tmp_path)
    with pytest.raises(FileExistsError):
        EvidenceRun(tmp_path, run.output, inputs=[data], configuration={}, method='test')


def test_sealed_outputs_cannot_be_reblessed(tmp_path):
    run, _, _ = setup_run(tmp_path)
    run.finish(model_status='DEVELOPMENT', result_summary={})
    (run.output / 'result.json').write_text('{}')
    with pytest.raises(FileExistsError):
        run.finish(model_status='DEVELOPMENT', result_summary={})
    assert verify_run(run.output)['status'] == 'FAIL'


def test_nested_file_named_manifest_is_still_an_output(tmp_path):
    run, _, _ = setup_run(tmp_path)
    (run.output / 'nested').mkdir()
    p = run.output / 'nested' / 'manifest.json'
    p.write_text('{}')
    run.finish(model_status='DEVELOPMENT', result_summary={})
    p.write_text('{"modified": true}')
    assert verify_run(run.output)['status'] == 'FAIL'


def test_missing_input_cannot_register(tmp_path):
    with pytest.raises(ValueError):
        EvidenceRun(tmp_path, tmp_path / 'run', inputs=[tmp_path / 'absent'],
                    configuration={}, method='test')
    assert not (tmp_path / 'run').exists()
