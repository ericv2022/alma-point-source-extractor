"""Regression tests for the original APSE catalog routines."""

import unittest

from APSE import filterSources, makeSourceList


def make_source(x=100, y=100, ispoint=True, zerooff=False):
    """Create a minimal source matching the legacy APSE structure."""

    source = {
        "ispoint": ispoint,
        "pixelcoords": [x, y],
        "pixelsperarcsec": [5.0, 5.0],
        "shape": {
            "majoraxis": {"value": 1.0},
            "minoraxis": {"value": 0.8},
            "positionangle": {"value": 0.0},
            "direction": {
                "RA": [1.0],
                "DEC": [0.5],
            },
        },
        "flux": {
            "value": [0.01],
            "error": [0.001],
        },
    }

    if zerooff:
        source["zerooff"] = 0.001

    return source


class TestFilterSources(unittest.TestCase):

    def test_isolated_point_source_retained(self):
        sources = {0: make_source()}
        result = filterSources(sources)
        self.assertEqual(result, sources)

    def test_extended_source_rejected(self):
        sources = {0: make_source(ispoint=False)}
        self.assertEqual(filterSources(sources), {})

    def test_background_source_rejected(self):
        sources = {0: make_source(zerooff=True)}
        self.assertEqual(filterSources(sources), {})

    def test_two_distant_sources_retained(self):
        sources = {
            0: make_source(100, 100),
            1: make_source(200, 200),
        }
        self.assertEqual(filterSources(sources), sources)

    def test_two_overlapping_sources_both_rejected(self):
        sources = {
            0: make_source(100, 100),
            1: make_source(100.5, 100),
        }
        self.assertEqual(filterSources(sources), {})

    def test_optional_filters_can_be_disabled(self):
        sources = {
            0: make_source(ispoint=False, zerooff=True),
        }
        result = filterSources(
            sources,
            pointSourcesOnly=False,
            noBackgroundEmission=False,
            isolatedSourcesOnly=False,
        )
        self.assertEqual(result, sources)


class TestMakeSourceList(unittest.TestCase):

    def test_catalog_fields(self):
        sources = {42: make_source()}
        result = makeSourceList(sources)

        self.assertEqual(
            result,
            {
                0: {
                    "RA": 1.0,
                    "DEC": 0.5,
                    "FLUX": 0.01,
                    "FLUXERR": 0.001,
                }
            },
        )

    def test_catalog_reindexes_sources(self):
        sources = {
            12: make_source(100, 100),
            27: make_source(200, 200),
        }
        result = makeSourceList(sources)
        self.assertEqual(list(result.keys()), [0, 1])

    def test_add_keywords_currently_has_no_effect(self):
        sources = {0: make_source()}
        self.assertEqual(
            makeSourceList(sources, addKeywords=True),
            makeSourceList(sources, addKeywords=False),
        )


if __name__ == "__main__":
    unittest.main()
