import random
import unittest
import numpy as np
import torch
from src.training.curve_audit import preserved_eval


class PreservedEvalTests(unittest.TestCase):
    def test_restores_mixed_modes_and_rng_after_exception(self):
        model = torch.nn.Sequential(torch.nn.Linear(2, 2), torch.nn.Dropout(.5))
        model.train()
        model[0].eval()
        modes = [m.training for m in model.modules()]
        random.seed(7)
        np.random.seed(7)
        torch.manual_seed(7)
        expected = (random.random(), float(np.random.random()), torch.rand(3))
        random.seed(7)
        np.random.seed(7)
        torch.manual_seed(7)
        with self.assertRaisesRegex(RuntimeError, 'synthetic'):
            with preserved_eval(model):
                self.assertTrue(all(not m.training for m in model.modules()))
                random.random()
                np.random.random()
                torch.rand(20)
                raise RuntimeError('synthetic')
        actual = (random.random(), float(np.random.random()), torch.rand(3))
        self.assertEqual(actual[:2], expected[:2])
        self.assertTrue(torch.equal(actual[2], expected[2]))
        self.assertEqual([m.training for m in model.modules()], modes)

    def test_restores_modes_on_success_without_parameter_update(self):
        model = torch.nn.Sequential(torch.nn.Linear(2, 2), torch.nn.Dropout(.5))
        model.train()
        initial = {k: v.clone() for k, v in model.state_dict().items()}
        with preserved_eval(model), torch.inference_mode():
            model(torch.ones(1, 2))
        self.assertTrue(all(m.training for m in model.modules()))
        self.assertTrue(all(torch.equal(initial[k], v) for k, v in model.state_dict().items()))
