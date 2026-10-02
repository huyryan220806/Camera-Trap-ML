import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from prepare_swg import label_policy, normalize, valid_bbox
from split_swg import audit_records, choose_location_split


class MetadataTests(unittest.TestCase):
    def test_label_normalization_does_not_merge_distinct_species(self):
        self.assertEqual(normalize(' Chinese serow '), 'chinese_serow')
        self.assertNotEqual(normalize('red_muntjac'), normalize('large_antlered_muntjac'))

    def test_quality_and_ambiguous_labels_not_species(self):
        for name in ['empty', 'human', 'problem', 'unidentified_bird', 'pangolin', 'roosevelts_muntjac_group']:
            self.assertNotEqual(label_policy(name), 'candidate')
        self.assertEqual(label_policy('annamite_striped_rabbit'), 'candidate')

    def test_absolute_and_relative_box(self):
        im = {'width': 100, 'height': 50}
        self.assertEqual(valid_bbox({'bbox': [10, 5, 20, 10]}, im), ([10, 5, 20, 10], 'valid'))
        self.assertEqual(valid_bbox({'bbox_relative': [.1, .1, .2, .2]}, im), ([10., 5., 20., 10.], 'valid'))

    def test_reject_invalid_and_ambiguous_boxes(self):
        im = {'width': 100, 'height': 50}
        for a in [{'bbox':[90,0,20,10]}, {'bbox':[100,0,.5,10]}, {'bbox':[0,0,0,10]}, {'bbox':[0,0,float('nan'),10]},
                  {'bbox':[0,0,10,10], 'bbox_relative':[0,0,.1,.2]}, {'bbox':[0,0,10,10], 'sequence_level_annotation':True}]:
            self.assertNotEqual(valid_bbox(a,im)[1], 'valid')
        self.assertEqual(valid_bbox({},im)[1], 'no_bbox')

    def test_split_is_reproducible_and_location_disjoint(self):
        records = [{'location':f'L{i:02}', 'label':label, 'seq_id':f'{i}-{label}-{j}'}
                   for i in range(30) for label in ['a','b'] for j in range(3)]
        first, _ = choose_location_split(records,['a','b'],42,50,3,2)
        second, _ = choose_location_split(records,['a','b'],42,50,3,2)
        self.assertEqual(first,second)
        self.assertEqual(set(first.values()), {'train','val','test'})
        for label in ['a','b']:
            self.assertEqual({first[r['location']] for r in records if r['label']==label}, {'train','val','test'})

    def test_audit_detects_sequence_and_location_leakage(self):
        rows = [{'image_id':'i1','file_name':'a.jpg','seq_id':'s','location':'l','split':'train'},
                {'image_id':'i2','file_name':'b.jpg','seq_id':'s','location':'l','split':'test'}]
        audit=audit_records(rows)
        self.assertFalse(audit['metadata_leakage_check_passed'])
        self.assertEqual(audit['cross_split_overlap']['seq_id'],1)
        rows[1].update(seq_id='s2',location='l2')
        self.assertTrue(audit_records(rows)['metadata_leakage_check_passed'])

    def test_infeasible_split_is_rejected(self):
        rows=[{'location':f'L{i}','label':'rare' if i==0 else 'common','seq_id':str(i)} for i in range(20)]
        with self.assertRaises(ValueError): choose_location_split(rows,['rare','common'],42,10,1,1)


if __name__ == '__main__':
    unittest.main()
