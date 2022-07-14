import unittest
from numpy.testing import assert_allclose
import pandas as pd
from scipy.sparse import csr_matrix
from anndata import AnnData
from ..pre import extract, filt_min_n, get_net_mat, match, rename_net
from ..utils import get_toy_data


class TestPre(unittest.TestCase):

    mat, net = get_toy_data()

    def test_extract(self):

        mat, r, c = self.mat.values, self.mat.index, self.mat.columns

        # Input is list
        m_lt, r_lt, c_lt = extract([mat, r, c])

        # Input is DF
        m_df, r_df, c_df = extract(self.mat)

        # Input is AnnData without raw
        var = pd.DataFrame(index=c)
        obs = pd.DataFrame(index=r)
        adata = AnnData(csr_matrix(mat), var=var, obs=obs)

        m_an, r_an, c_an = extract(adata, use_raw=False)

        # Input is AnnData with raw
        adata.raw = adata
        m_ar, r_ar, c_ar = extract(adata)

        # Assert mat
        assert_allclose(m_lt.A, mat)
        assert_allclose(m_df.A, mat)
        assert_allclose(m_an.A, mat)
        assert_allclose(m_ar.A, mat)

        # Assert samples
        r = list(r)
        self.assertEqual(list(r_lt), r)
        self.assertEqual(list(r_df), r)
        self.assertEqual(list(r_an), r)
        self.assertEqual(list(r_ar), r)

        # Assert columns
        c = list(c)
        self.assertEqual(list(c_lt), c)
        self.assertEqual(list(c_df), c)
        self.assertEqual(list(c_an), c)
        self.assertEqual(list(c_ar), c)

    def test_filt_min_n(self):

        mat, net = self.mat, self.net
        mat, r, c = extract(mat)

        f_net = filt_min_n(c, net, min_n=4)

        self.assertTrue(net.shape[0] > f_net.shape[1])

    def test_get_net_mat(self):

        net = self.net
        sources, targets, regX = get_net_mat(net)

        self.assertTrue(regX.shape[0] == len(targets))
        self.assertTrue(regX.shape[1] == len(sources))

    def test_match(self):

        mat, net = self.mat, self.net
        mat, r, c = extract(mat)
        sources, targets, net = get_net_mat(net)

        match(c, targets, net)

    def test_rename_net(self):

        net = self.net
        rename_net(net, source='source', target='target', weight='weight')