import argparse
import os
import tempfile
import unittest

import asdf
from scipy.sparse import coo_matrix

import ast2vec.tests as tests
from ast2vec import Repo2Coocc, Repo2CooccTransformer
from ast2vec.repo2.coocc import repo2coocc_entry


def validate_asdf_file(obj, filename):
    data = asdf.open(filename)
    obj.assertIn("meta", data.tree)
    obj.assertIn("matrix", data.tree)
    obj.assertIn("tokens", data.tree)
    obj.assertEqual(data.tree["meta"]["model"], "co-occurrences")


class Repo2CooccTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tests.setup()

    def test_obj(self):
        basedir = os.path.dirname(__file__)
        repo2 = Repo2Coocc(linguist=tests.ENRY, timeout=600)
        coocc = repo2.convert_repository(os.path.join(basedir, "..", ".."))
        self.assertIsInstance(coocc, tuple)
        self.assertEqual(len(coocc), 2)
        self.assertIn("document", coocc[0])
        self.assertIsInstance(coocc[1], coo_matrix)
        self.assertEqual(coocc[1].shape, (len(coocc[0]),) * 2)
        self.assertGreater(coocc[1].getnnz(), 20000)

    def test_asdf(self):
        basedir = os.path.dirname(__file__)
        with tempfile.NamedTemporaryFile() as file:
            args = argparse.Namespace(
                linguist=tests.ENRY, output=file.name, bblfsh_endpoint=None,
                timeout=None, repository=os.path.join(basedir, "..", ".."))
            repo2coocc_entry(args)
            validate_asdf_file(self, file.name)

    def test_linguist(self):
        # If this test fails, check execution permissions for provided paths.
        with self.assertRaises(FileNotFoundError):
            Repo2Coocc(linguist="xxx", timeout=600)
        with self.assertRaises(FileNotFoundError):
            Repo2Coocc(linguist=__file__, timeout=600)


class Repo2CooccTransformerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tests.setup()

    def test_transform(self):
        basedir = os.path.dirname(__file__)
        with tempfile.TemporaryDirectory() as tmpdir:
            r2cc = Repo2CooccTransformer(
                bblfsh_endpoint=os.getenv("BBLFSH_ENDPOINT", "0.0.0.0:9432"),
                linguist=tests.ENRY, timeout=600)
            r2cc.transform(repos=basedir, output=tmpdir)

            # check that output file exists
            outfile = r2cc.prepare_filename(basedir, tmpdir)
            self.assertEqual(os.path.exists(outfile), 1)

            validate_asdf_file(self, outfile)

    def test_empty(self):
        basedir = os.path.dirname(__file__)
        with tempfile.TemporaryDirectory() as tmpdir:
            r2cc = Repo2CooccTransformer(
                bblfsh_endpoint=os.getenv("BBLFSH_ENDPOINT", "0.0.0.0:9432"),
                linguist=tests.ENRY, timeout=600)
            r2cc.transform(repos=os.path.join(basedir, "coocc"), output=tmpdir)
            self.assertFalse(os.listdir(tmpdir))

if __name__ == "__main__":
    unittest.main()