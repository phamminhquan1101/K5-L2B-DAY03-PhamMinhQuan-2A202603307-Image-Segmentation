import unittest

import numpy as np

from mask_protocol import mask_to_cvat_rle, validate_prompts


def decode(points, shape):
    result = np.zeros(shape, dtype=bool)
    left, top, right, bottom = points[-4:]
    runs = points[:-4]
    pixels = np.repeat(np.arange(len(runs)) % 2, runs)
    result[top:bottom + 1, left:right + 1] = pixels.reshape(bottom - top + 1, right - left + 1)
    return result


class CVATMaskProtocolTests(unittest.TestCase):
    def test_round_trip_preserves_holes_disconnected_regions_and_edges(self):
        mask = np.zeros((9, 13), dtype=bool)
        mask[1:8, 2:11] = True
        mask[3:5, 5:7] = False
        mask[0, 12] = True
        mask[8, 0] = True
        np.testing.assert_array_equal(decode(mask_to_cvat_rle(mask), mask.shape), mask)

    def test_single_pixel_and_full_mask_use_inclusive_bounds(self):
        for mask in (np.ones((1, 1), dtype=bool), np.ones((3, 7), dtype=bool)):
            encoded = mask_to_cvat_rle(mask)
            self.assertEqual(encoded[0], 0)
            self.assertEqual(encoded[-4:], [0, 0, mask.shape[1] - 1, mask.shape[0] - 1])
            np.testing.assert_array_equal(decode(encoded, mask.shape), mask)

    def test_cropped_mask_coordinates_are_not_shifted(self):
        mask = np.zeros((100, 200), dtype=bool)
        mask[20:23, 80:84] = True
        self.assertEqual(mask_to_cvat_rle(mask), [0, 12, 80, 20, 83, 22])

    def test_empty_mask_does_not_create_phantom_object(self):
        self.assertIsNone(mask_to_cvat_rle(np.zeros((3, 4))))

    def test_invalid_or_negative_only_prompts_are_rejected(self):
        for positive, negative, box in [([], [[1, 1]], None), ([[200, 0]], [], None),
                                         ([[float('nan'), 0]], [], None), ([[1, 1]], [], [1, 1, 1, 3])]:
            with self.assertRaises(ValueError):
                validate_prompts(positive, negative, box, 200, 100)


if __name__ == '__main__':
    unittest.main()
