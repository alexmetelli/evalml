from unittest.mock import MagicMock

import pytest

from evalml.automl import AutoMLSearch
from evalml.automl.engine import ParallelEngine


def test_evaluate_no_data():
    engine = ParallelEngine()
    expected_error = "Dataset has not been loaded into the engine."
    with pytest.raises(ValueError, match=expected_error):
        engine.evaluate_batch([])


def test_evaluate_batch(dummy_parallel_binary_pipeline_class, X_y_binary):
    X, y = X_y_binary
    automl = AutoMLSearch(X_train=X, y_train=y, problem_type='binary', max_time=1, max_batches=1,
                          allowed_pipelines=[dummy_parallel_binary_pipeline_class])
    pipelines = [dummy_parallel_binary_pipeline_class({'Mock Classifier': {'a': 1}}),
                 dummy_parallel_binary_pipeline_class({'Mock Classifier': {'a': 4.2}})]

    mock_should_continue_callback = MagicMock(return_value=True)
    mock_pre_evaluation_callback = MagicMock()
    mock_post_evaluation_callback = MagicMock(side_effect=[123, 456])

    engine = ParallelEngine(X_train=automl.X_train,
                            y_train=automl.y_train,
                            automl=automl,
                            should_continue_callback=mock_should_continue_callback,
                            pre_evaluation_callback=mock_pre_evaluation_callback,
                            post_evaluation_callback=mock_post_evaluation_callback)
    new_pipeline_ids = engine.evaluate_batch(pipelines)

    assert len(pipelines) == 2  # input arg should not have been modified
    assert mock_should_continue_callback.call_count == 0  # since all pipelines are evaluated in parallel, there's no stopping mid-batch
    assert mock_pre_evaluation_callback.call_count == 2
    assert mock_post_evaluation_callback.call_count == 2
    assert new_pipeline_ids == [123, 456]
    assert mock_pre_evaluation_callback.call_args_list[0][0][0] == pipelines[0]
    assert mock_pre_evaluation_callback.call_args_list[1][0][0] == pipelines[1]
    assert mock_post_evaluation_callback.call_args_list[0][0][0] in pipelines
    assert mock_post_evaluation_callback.call_args_list[0][0][1]['cv_score_mean'] == 0.42
    assert mock_post_evaluation_callback.call_args_list[1][0][0] in pipelines
    assert mock_post_evaluation_callback.call_args_list[1][0][1]['cv_score_mean'] == 0.42
