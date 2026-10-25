import copy
import inspect
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.error_analysis import run_error_analysis
from src.evaluation.reproducibility import compare_replay, verify_validation_inputs, CHECKPOINTS


def evidence():
    return {'image_level': {'macro_f1': .74, 'confusion_matrix': [[1, 0], [0, 1]]},
            'predictions': [{'image_id': 'a', 'true_class_id': 0, 'predicted_class_id': 0},
                            {'image_id': 'b', 'true_class_id': 1, 'predicted_class_id': 1}]}


class IntegrityTests(unittest.TestCase):
    def test_identical_replay(self):
        self.assertEqual(compare_replay(evidence(), evidence())['status'], 'PASS')

    def test_same_f1_different_matrix_fails(self):
        changed = evidence()
        changed['image_level']['confusion_matrix'] = [[0, 1], [1, 0]]
        self.assertEqual(compare_replay(evidence(), changed)['status'], 'FAIL')

    def test_changed_predictions_fail_even_with_same_matrix(self):
        changed = evidence()
        changed['predictions'][0]['predicted_class_id'] = 1
        self.assertEqual(compare_replay(evidence(), changed)['changed_image_ids'], ['a'])

    def test_duplicate_ids_blocked(self):
        changed = evidence()
        changed['predictions'] *= 2
        with self.assertRaises(ValueError):
            compare_replay(evidence(), changed)

    def test_scalar_metric_mismatch_is_not_only_a_warning(self):
        for delta in (.0001, .02):
            changed = evidence()
            changed['image_level']['macro_f1'] -= delta
            self.assertEqual(compare_replay(evidence(), changed)['status'], 'FAIL')

    def test_default_preflight_and_opt_out_blocked(self):
        self.assertIs(inspect.signature(run_error_analysis).parameters['preflight_hash_check'].default, True)
        with self.assertRaisesRegex(ValueError, 'mandatory'):
            run_error_analysis(Path('not-read.pt'), preflight_hash_check=False)
        with self.assertRaisesRegex(ValueError, 'mandatory'):
            run_error_analysis(Path('not-read.pt'), overwrite=True)

    def test_unpinned_checkpoint_and_modified_provenance_blocked(self):
        with patch('src.evaluation.reproducibility.digest', return_value='bad'):
            with self.assertRaisesRegex(ValueError, 'pinned'):
                verify_validation_inputs(Path('.'), Path('x.pt'), {})
        with patch('src.evaluation.reproducibility.digest', side_effect=[next(iter(CHECKPOINTS)), 'bad']):
            with self.assertRaisesRegex(ValueError, 'provenance'):
                verify_validation_inputs(Path('.'), Path('x.pt'), {})

    def test_analysis_default_passes_mandatory_preflight_to_loader(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            ckpt = path / 'b2.pt'
            ckpt.write_bytes(b'synthetic')
            payload = {'num_classes': 8, 'backbone_name': 'resnet18',
                       'id_to_label': {i: str(i) for i in range(8)}, 'model_state_dict': {}}
            with patch('scripts.error_analysis.torch.load', return_value=payload), \
                 patch('scripts.error_analysis.verify_validation_inputs', return_value=(path, 'synthetic', 'B2')), \
                 patch('scripts.error_analysis.B2CropClassifier'), \
                 patch('scripts.error_analysis.make_b2_loaders', side_effect=ValueError('source SHA mismatch')) as loader:
                with self.assertRaisesRegex(ValueError, 'source SHA mismatch'):
                    run_error_analysis(ckpt, output_dir=path, attempt='probe')
                self.assertIs(loader.call_args.kwargs['preflight_hash_check'], True)
            self.assertFalse((path / 'error_analysis_b2_probe.json').exists())


if __name__ == '__main__':
    unittest.main()
